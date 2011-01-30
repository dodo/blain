
from PyQt4.Qt import QThread, QSettings

from inc.microblogging import api_call
from inc.json_hack import json
from inc.parse import drug, parse_post, parse_date, pythonize_post, clean_urls

MAX_PAGE_COUNT = 200


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
    except Exception as e:
        print "[ERROR] while getting user (%s, %s, %i):" % (service,user,page),e
        return [], False



class UserStatusThread(QThread):

    def __init__(self, app, id, user, account, knownids,
                 update_method, user_method, api_method):
        QThread.__init__(self, app)
        self.id = id
        self.app = app
        self.user = user
        self.account = account
        self.service = account.service
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
        except Exception as e:
            print "[ERROR]", e
            protected = True # by error :P
        if protected:
            self.update(self.account, self.user, 0, ok)
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
                    update = parse_post(self.account, self.user, status)
                    self.knownids.append(status['id'])
                    self.app.addMessage.emit(update)
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
        self.update(self.account, self.user, i, ok)
        #print self.service + " done."
        self.app.killThread.emit(self.id)
        self.quit()



def next_twitter_page(prev, result):
    if result is None:
        return -1
    return result['next_cursor']


def get_twitter_friends(result):
    return result['users']


def next_statusnet_page(prev, _):
    return prev+1


def get_statusnet_friends(result):
    return result


def get_friends(typ, service, user, page):
    options = {
            'cursor': page,
            'id': user,
            }
    try:
        return pages[typ].get(api_call(service, 'statuses/friends', options))
    except Exception as e:
        print "[ERROR] while getting friends (%s, %s, %i):"%(service,user,page),e
        return []


def next_page(typ, prev, result):
    return pages[typ].next(prev, result)


def get_group(service, user):
    try:
        return api_call(service, 'statusnet/groups/list', {'id':user})
    except Exception as e:
        print "Error while getting group (%s):" % user, e
        return None




class FriendsThread(QThread):

    def __init__(self, app, account, updateusers = True):
        QThread.__init__(self, app)
        self.app = app
        self.account = account
        self.user = account.name
        self.service = account.service
        self.updateusers = updateusers
        self.friends = account.friends


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
        except Exception as e:
            print "[ERROR]", e
            self.end()
            return
        old_friends = list(map(unicode,self.friends.allKeys()))
        while friendscount > 0:
            page = next_page(self.account.type, page, new_friends)
            #print "Fetching from friends page %i, %i updates remaining (%s)" % \
            #    (page, friendscount, self.service),"[%i]"%trys
            new_friends = get_friends(
                self.account.type, self.service, self.user, page)
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
                    self.app.updates.add_timer("user",self.service,self.user,id)
                dump = json.dumps(clean_urls(friend))
                self.friends.setValue(id, dump)
            if stop or trys > 3: break
            #self.yieldCurrentThread()
        for id in old_friends:
            #print id, "(lost)", self.service
            self.app.updates.remove_timer("user", self.service, self.user, id)
            self.friends.remove(id)
        #print "friends list up-to-date. (%s)" % self.service
        self.end()

    def end(self):
        self.app.killThread.emit(self.service + self.user + u"friends")
        # update all users
        if self.updateusers:
            for user in self.friends.allKeys() + [self.user]:
                self.app.updateUser.emit(self.service, self.user, user)
        self.app.updates.updates.friends(self.account)
        #print "done."
        self.quit()



class GroupsThread(QThread):

    def __init__(self, app, account, updategroups = True):
        QThread.__init__(self, app)
        self.app = app
        self.account = account
        self.updategroups = updategroups
        self.groups = account.groups


    def run(self):
        if not self.account:
            self.quit()
            return
        trys = 0
        new_groups = None
        old_groups = list(map(unicode,self.groups.allKeys()))
        while trys < 4:
            trys += 1
            new_groups = get_group(self.account.service, self.account.name)
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
                self.app.updates.add_timer(
                    "group", self.account.service, self.account.name, id)
            dump = json.dumps(clean_urls(group))
            self.groups.setValue(id, dump)
        for id in old_groups:
            #print id, "(lost)"
            self.app.updates.remove_timer(
                "group", self.account.service, self.account.name, id)
            self.groups.remove(id)
        #print "groups list up-to-date. (%s)" % self.user
        self.end()

    def end(self):
        account = self.account
        self.app.killThread.emit(account.service + account.name + u"groups")
        # update all groups
        if self.updategroups:
            for group in self.groups.allKeys():
                self.app.updateGroup.emit(account.service, account.name, group)
        self.app.updates.updates.groups(account)
        #print "done."
        self.quit()



class Threader:

    def __init__(self, app):
        if not hasattr(app, 'accounts'):
            print("thread: need 'accounts' from app.")
            exit(1)
        self.app = app
        self.threads = {}


    def connect(self):
        self.app.killThread.connect(self.killThread)
        self.app.updateUser.connect(self.updateUser)
        self.app.updateGroup.connect(self.updateGroup)
        self.app.updateGroups.connect(self.start_updateGroups)
        self.app.updateFriends.connect(self.start_updateFriends)


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


    def updateUser(self, service, account, user):
        service, account, user = unicode(service),unicode(account),unicode(user)
        id = service + account + user
        account = self.app.accounts.get(service, account)
        #print "updating user", user, "(%s) ..." % service
        if self.check_thread(id, service, user):
            knownids = self.app.db.get_knownids(user)
            self.threads[id] = UserStatusThread(
                self.app, id, user, account, knownids,
                "user", 'users/show', 'statuses/user_timeline')
            self.threads[id].start()


    def updateFriends(self, service, account, updateusers=True):
        service, account = unicode(service), unicode(account)
        id = service + account + u"friends"
        account = self.app.accounts.get(service, account)
        #print "updating ", account, "[%s] ..." % service
        if self.check_thread(id, service, "friends"):
            self.threads[id] = FriendsThread(self.app, account, updateusers)


    def start_updateFriends(self, service, account, *args):
        self.updateFriends(service, account, *args)
        service, account = unicode(service), unicode(account)
        self.start(service + account + u"friends")


    def updateGroup(self, service, account, group):
        service,account,group = unicode(service),unicode(account),unicode(group)
        id = u"{0}{1}group{2}".format(service, account, group)
        account = self.app.accounts.get(service, account)
        #print "updating group", group, "..."
        if self.check_thread(id, service, group):
            knownids = self.app.db.get_knownids(group)
            self.threads[id] = UserStatusThread(
                self.app, id, group, account, knownids,
                "group", 'statusnet/groups/show', 'statusnet/groups/timeline')
            self.threads[id].start()


    def updateGroups(self, service, account, updategroups=True):
        service, account = unicode(service), unicode(account)
        id = service + account + u"groups"
        account = self.app.accounts.get(service, account)
        if account.groups is None:
            return # not a statusnet service
        #print "updating ", account, "groups ..."
        if self.check_thread(id, service, "groups"):
            self.threads[id] = GroupsThread(self.app, account, updategroups)


    def start_updateGroups(self, service, account, *args):
        self.updateGroups(service, account, *args)
        service, account = unicode(service), unicode(account)
        self.start(service + account + u"groups")


    def start(self, *services):
        #print "starting", ", ".join(services)
        for service in services:
            if service not in self.threads:
                print "unknown thread %s" % service
                return
            self.threads[service].start()



pages = {
    'twitter': drug(
        next = next_twitter_page,
        get = get_twitter_friends),
    'statusnet': drug(
        next = next_statusnet_page,
        get = get_statusnet_friends),
}
