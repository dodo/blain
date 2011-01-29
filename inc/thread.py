
from traceback import print_exc

from PyQt4.Qt import QThread, QSettings

from inc.microblogging import api_call
from inc.json_hack import json
from inc.parse import drug, parse_post, parse_date, pythonize_post, clean_urls

MAX_PAGE_COUNT = 200

def pages():
    return {
        'twitter': drug(
            next = next_twitter_page,
            get = get_twitter_friends),
        'identica': drug(
            next = next_identica_page,
            get = get_identica_friends)
        }


def get_page(method, service, user, count, page, opts={}):
    options = {
            'page': page,
            'count': count,
            'id': user,
            'include_rts': 'true', #get all 200 tweets from twitter
            }
    options.update(opts)
    try:
        return api_call(service, method, options), True
    except:
        print "[ERROR] while getting user (%s, %s, %i):" % (service, user, page)
        print_exc()
        return [], False



class UserStatusThread(QThread):

    def __init__(self, app, id, user, service, knownids,
                 update_method, user_method, api_method):
        QThread.__init__(self, app)
        self.id = id
        self.app = app
        self.user = user
        self.service = service
        self.knownids = knownids
        self.api_method = api_method
        self.user_method = user_method
        self.update = getattr(self.app.updates, update_method)

    def run(self):
        if not self.service or not self.user:
            self.app.logStatus.emit("[ERROR] no user given! ("+self.service+")")
            self.app.killThread.emit(self.id)
            self.quit()
            return

        ok = False
        n, i = 1, 0
        _id = ''
        trys = 0
        page = 1
        step = 200

        servicecount = 4223 # meh :/
        protected = False
        new_statuses = None

        try:
            res = api_call(self.service, self.user_method, {'id': self.user})
            if 'protected' in res:
                protected = res['protected']
            if 'statuses_count' in res:
                servicecount = res['statuses_count']
            ok = True
        except:
            print_exc()
            protected = True # by error :P
        if protected:
            self.update(self.service, self.user, 0, ok)
            self.app.killThread.emit(self.id)
            self.quit()
            return
        while servicecount > 0:
            fetch_count = min(n==1 and int(step/10) or step, servicecount)
            #print "%i Fetching %i from page %i, %i updates remaining (%s)" % \
            #    (n, fetch_count, page, servicecount, self.service),"[%i]"%trys
            new_statuses,new_ok = get_page(self.api_method,
                self.service, self.user, fetch_count, page,
                page == 2 and _id and {'max_id':_id} or {})
            ok = ok and new_ok
            stop = False
            if n > 1:
                servicecount -= len(new_statuses)
                if len(new_statuses) == 0:
                    trys += 1
            for status in new_statuses:
                _id = str(status['id'])
                id = self.service + _id
                if status['id'] in self.knownids:
                    #print id, "(found)"
                    stop = True
                else:
                    #print id
                    i += 1
                    update = parse_post(self.service, self.user, status)
                    self.knownids.append(status['id'])
                    self.app.addMessage.emit(self.service, update)
            n += 1
            #self.yieldCurrentThread()
            if stop or trys > 3: break
            if fetch_count != int(step/10):
                page += 1

        if i:
            self.app.logStatus.emit("%i updates on %s from %s" % \
                (i, self.service, self.user))
        else:
            self.app.logStatus.emit("[ERROR] no results for {0} on {1}!".\
                format(self.user, self.service))
        self.update(self.service, self.user, i, ok)
        #print self.service + " done."
        self.app.killThread.emit(self.id)
        self.quit()



def next_twitter_page(prev, result):
    if result is None:
        return -1
    return result['next_cursor']


def get_twitter_friends(result):
    return result['users']


def next_identica_page(prev, _):
    return prev+1


def get_identica_friends(result):
    return result


def get_friends(service, user, page):
    options = {
            'cursor': page,
            'id': user,
            }
    try:
        return pages[service].get(api_call(service, 'statuses/friends', options))
    except:
        print "[ERROR] while getting friends (%s, %s, %i):"%(service, user, page)
        print_exc()
        return []


def next_page(service, prev, result):
    return pages[service].next(prev, result)


def get_group(user):
    try:
        return api_call('identica', 'statusnet/groups/list', {'id':user})
    except:
        print "Error while getting group (%s):" % user
        print_exc()
        return None




class MicroblogThread(QThread):

    def __init__(self, app, user, service, updateusers = True):
        QThread.__init__(self, app)
        self.app = app
        self.user = user
        self.service = service
        self.updateusers = updateusers
        self.friends = QSettings("blain", "%s-%s-friends" % (user, service))


    def run(self):
        if not self.service or not self.user:
            self.quit()
            return
        trys = 0
        page = -1
        new_friends = None
        try:
            friendscount = api_call(self.service, 'users/show',
                {'id': self.user})['friends_count']
        except:
            print_exc()
            self.end()
            return
        old_friends = list(map(unicode,self.friends.allKeys()))
        while friendscount > 0:
            page = next_page(self.service, page, new_friends)
            #print "Fetching from friends page %i, %i updates remaining (%s)" % \
            #    (page, friendscount, self.service),"[%i]"%trys
            new_friends = get_friends(self.service, self.user, page)
            stop = False
            friendscount -= len(new_friends)
            if len(new_friends) == 0:
                trys += 1
            for friend in new_friends:
                id = unicode(friend['screen_name'])
                if self.friends.contains(id):
                    #print id, "(found)", self.service
                    stop = True
                    if id in old_friends:
                        old_friends.remove(id)
                else:
                    #print id, "(new)", self.service
                    self.app.updates.add_timer("user", self.service, id)
                dump = json.dumps(clean_urls(friend))
                self.friends.setValue(id, dump)
            if stop or trys > 3: break
            #self.yieldCurrentThread()
        for id in old_friends:
            #print id, "(lost)", self.service
            self.app.updates.remove_timer("user", self.service, id)
            self.friends.remove(id)
        #print "friends list up-to-date. (%s)" % self.service
        self.end()

    def end(self):
        self.app.killThread.emit("__%s__" % self.service)
        # update all users
        if self.updateusers:
            for user in self.friends.allKeys() + [self.user]:
                self.app.updateUser.emit(self.service, user)
        self.app.updates.updates.friends(self.service, self.user)
        #print "done."
        self.quit()



class GroupsThread(QThread):

    def __init__(self, app, user, updategroups = True):
        QThread.__init__(self, app)
        self.app = app
        self.user = user
        self.updategroups = updategroups
        self.groups = QSettings("blain", "%s-groups" % user)


    def run(self):
        if not self.user:
            self.quit()
            return
        trys = 0
        new_groups = None
        old_groups = list(map(unicode,self.groups.allKeys()))
        while trys < 4:
            trys += 1
            new_groups = get_group(self.user)
            if new_groups is not None:
                break
        if new_groups is None:
            self.end()
            return
        for group in new_groups:
            id = unicode(group['nickname'])
            if self.groups.contains(id):
                #print id, "(found)"
                if id in old_groups:
                    old_groups.remove(id)
            else:
                #print id, "(new)"
                self.app.updates.add_timer("group", "", id)
            dump = json.dumps(clean_urls(group))
            self.groups.setValue(id, dump)
        for id in old_groups:
            #print id, "(lost)"
            self.app.updates.remove_timer("group", "", id)
            self.groups.remove(id)
        #print "groups list up-to-date. (%s)" % self.user
        self.end()

    def end(self):
        self.app.killThread.emit("%s groups" % self.user)
        # update all groups
        if self.updategroups:
            for group in self.groups.allKeys():
                self.app.updateGroup.emit(group)
        self.app.updates.updates.groups(self.user)
        #print "done."
        self.quit()



class Threader:

    def __init__(self, app):
        self.app = app
        self.threads = {}


    def connect(self):
        self.app.killThread.connect(self.killThread)
        self.app.updateUser.connect(self.updateUser)
        self.app.updateGroup.connect(self.updateGroup)
        self.app.updateGroups.connect(self.start_updateGroups)
        self.app.updateMicroblogging.connect(self.start_updateMicroblogging)


    def setup(self):
        pass


    def check_thread(self, id, service, text):
        if id in self.threads and self.threads[id].isRunning():
            print text, "thread still running. (%s)" % service
            return False
        return True


    def killThread(self, id):
        id = str(id)
        if id in self.threads:
            del self.threads[id]
        #print len(self.threads),"threads still running:  ",", ".\
        #    join(self.threads.keys()),"-"*40
        self.app.db.commit() # after addMessage
        self.app.reader.update()
        if not self.threads:
            self.app.filters.update(False) # FIXME do incremental update
            self.app.window.updateMessageView(42)
        else:
            self.app.filters.update(False) # FIXME do incremental update
            self.app.window.updateMessageView(10)


    def updateUser(self, service, user):
        service, user = unicode(service), unicode(user)
        #print "updating user", user, "(%s) ..." % service
        id = service + user
        if self.check_thread(id, service, user):
            knownids = self.app.db.get_knownids(user)
            self.threads[id] = UserStatusThread(
                self.app, id, user, service, knownids,
                "user", 'users/show', 'statuses/user_timeline')
            self.threads[id].start()


    def updateMicroblogging(self, service, user, updateusers=True):
        service, user = str(service), unicode(user)
        #print "updating ", user, "[%s] ..." % service
        id = "__%s__" % service
        if self.check_thread(id, service, "friends"):
            self.threads[id] = MicroblogThread(
                self.app, user, service, updateusers)


    def start_updateMicroblogging(self, service, *args):
        self.updateMicroblogging(service, *args)
        self.start("__%s__" % service)


    def updateGroup(self, group):
        group = unicode(group)
        #print "updating group", group, "..."
        id = " %s group" % group
        if self.check_thread(id, "identica", group):
            knownids = self.app.db.get_knownids(group)
            self.threads[id] = UserStatusThread(
                self.app, id, group, "identica", knownids,
                "group", 'statusnet/groups/show', 'statusnet/groups/timeline')
            self.threads[id].start()


    def updateGroups(self, user, updategroups=True):
        user = unicode(user)
        #print "updating ", user, "groups ..."
        id = "%s groups" % user
        if self.check_thread(id, "identica", "groups"):
            self.threads[id] = GroupsThread(self.app, user, updategroups)


    def start_updateGroups(self, user, *args):
        self.updateGroups(user, *args)
        self.start("%s groups" % user)


    def start(self, *services):
        #print "starting", ", ".join(services)
        for service in services:
            if service not in self.threads:
                print "unknown thread %s" % service
                return
            self.threads[service].start()



pages = pages()
