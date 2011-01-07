
from traceback import print_exc

from PyQt4.Qt import QThread, QSettings

from inc.microblogging import api_call
from inc.json_hack import json
from inc.parse import drug, parse_post, parse_date, pythonize_post

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


def get_page(service, user, count, page, opts={}):
    options = {
            'page': page,
            'count': count,
            'id': user,
            'include_rts': 'true', #get all 200 tweets from twitter
            }
    options.update(opts)
    try:
        return api_call(service, 'statuses/user_timeline', options), True
    except:
        print_exc()
        return [], False



class UserStatusThread(QThread):

    def __init__(self, app, id, user, service, knownids):
        QThread.__init__(self, app)
        self.id = id
        self.app = app
        self.user = user
        self.service = service
        self.knownids = knownids

    def run(self):
        if not self.service or not self.user:
            self.app.logStatus.emit("Error: no user given! ("+self.service+")")
            self.app.killThread.emit(self.id)
            self.quit()
            return

        ok = False
        n, i = 1, 0
        _id = ''
        trys = 0
        page = 1
        step = 200

        new_statuses = None

        try:
            res = api_call(self.service, 'users/show', {'id': self.user})
            protected = res['protected']
            servicecount = res['statuses_count']
            ok = True
        except:
            print_exc()
            protected = True # by error :P
        if protected:
            self.app.updates.updates.user(self.service, self.user, 0, ok)
            self.app.killThread.emit(self.id)
            self.quit()
            return
        while servicecount > 0:
            fetch_count = min(n==1 and int(step/10) or step, servicecount)
            print "%i Fetching %i from page %i, %i updates remaining (%s)" % \
                (n, fetch_count, page, servicecount, self.service),"[%i]"%trys
            new_statuses,new_ok = get_page(self.service, self.user, fetch_count,
                page, page == 2 and _id and {'max_id':_id} or {})
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
                    print id, "(found)"
                    stop = True
                else:
                    print id
                    i += 1
                    update = parse_post(self.service, status)
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
            self.app.logStatus.emit("Error: no results for {0} on {1}!".\
                format(self.user, self.service))
        self.app.updates.updates.user(self.service, self.user, i, ok)
        print self.service + " done."
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
        print_exc()
        return []


def next_page(service, prev, result):
    return pages[service].next(prev, result)



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
        while friendscount > 0:
            page = next_page(self.service, page, new_friends)
            print "Fetching from friends page %i, %i updates remaining (%s)" % \
                (page, friendscount, self.service),"[%i]"%trys
            new_friends = get_friends(self.service, self.user, page)
            stop = False
            friendscount -= len(new_friends)
            if len(new_friends) == 0:
                trys += 1
            for friend in new_friends:
                id = str(friend['screen_name'])
                if self.friends.contains(id):
                    print id, "(found)", self.service
                    stop = True
                else:
                    print id, "(new)", self.service
                dump = json.dumps(friend)
                self.friends.setValue(id, dump)
            if stop or trys > 3: break
            #self.yieldCurrentThread()
        print "friends list up-to-date. (%s)" % self.service
        self.end()

    def end(self):
        self.app.killThread.emit("__%s__" % self.service)
        # update all users
        if self.updateusers:
            for user in self.friends.allKeys() + [self.user]:
                self.app.updateUser.emit(self.service, user)
        self.app.updates.updates.friends(self.service, user)
        print "done."
        self.quit()



class Threader:

    def __init__(self, app):
        self.app = app
        self.threads = {}


    def connect(self):
        self.app.killThread.connect(self.killThread)
        self.app.updateUser.connect(self.updateUser)
        self.app.updateMicroblogging.connect(self.updateMicroblogging)


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
        print len(self.threads),"threads still running:  ",", ".\
            join(self.threads.keys()),"-"*40
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
        print "updating user", user, "(%s) ..." % service
        id = service + user
        if self.check_thread(id, service, user):
            knownids = self.app.db.get_knownids(user)
            self.threads[id] = UserStatusThread(
                self.app, id, user, service, knownids)
            self.threads[id].start()


    def updateMicroblogging(self, service, user, updateusers=True):
        service, user = str(service), unicode(user)
        print "updating microblog", user, "(%s) ..." % service
        if service in self.threads and self.threads[service].isRunning():
            print "update %s already running" % service
            return
        self.threads["__%s__" % service] = MicroblogThread(
            self.app,user,service,updateusers)


    def start(self, *services):
        for service in services:
            if "__%s__" % service not in self.threads:
                print "update __%s__ isn running" % service
                return
            self.threads["__%s__" % service].start()



pages = pages()
