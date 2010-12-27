
from time import time
from traceback import print_exc

from PyQt4.Qt import QThread, QSettings, QTimer

from microblogging import api_call
from json_hack import json
from parsing import drug, parse_post, parse_date


MAX_PAGE_COUNT = 200

updates = drug() # will be set in setup

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
            updates.user(self.service, self.user, 0, ok)
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
            self.app.logStatus.emit("Error: no results for {0} on {1}!".\
                format(self.user, self.service))
        updates.user(self.service, self.user, i, ok)
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
        # update all users
        if self.updateusers:
            for user in self.friends.allKeys() + [self.user]:
                self.app.updateUser.emit(service, user)
        updates.friends(self.service, self.user)
        print "done."
        self.quit()


def setup(app):
    update = {}
    app.timer = QTimer(app)
    st = QSettings("blain", "timers")
    update['user'] = app.updateUser.emit
    update['friends'] = lambda *args: app.updateMicroblogging.emit(args[0],
        app.settings.value("account/"+args[0]+"/id").toString(),
        False, *args[2:])
    friends = drug(twitter = [], identica = [])
    if app.settings.contains("account/twitter/id"):
        friends.twitter  = map(unicode,QSettings("blain",
            "%s-twitter-friends"  % app.settings.value("account/twitter/id").\
            toString()).allKeys())
    if app.settings.contains("account/identica/id"):
        friends.identica = map(unicode,QSettings("blain",
            "%s-identica-friends" % app.settings.value("account/identica/id").\
            toString()).allKeys())
    timers = [ unicode(st.value(str(i)).toString()) # (timestamp, func, service, user, *args)
               for i in range(st.value("count",0).toInt()[0]) ]

    # add timer entries
    new_friends = ['twitter', 'identica']
    new_friend = {'twitter':friends.twitter , 'identica':friends.identica}
    for timer in map(lambda t: unicode(t).split(","), timers):
        if timer[1] == 'user':
            if timer[3] in new_friend[timer[2]]:
                new_friend[timer[2]].remove(timer[3])
        elif timer[1] == 'friends':
            if timer[2] in new_friends:
                new_friends.remove(timer[2])
    for service in new_friends:
        timers.append("{0},friends,{1},".format(time(),service))

    for service in new_friend:
        for i, user in enumerate(new_friend[service]):
            new_friend[service][i] = "{0},user,{1},{2}".\
                format(time(),service,user)
    if new_friend['twitter'] or new_friend['identica']:
        timers.extend(list(sum(zip(new_friend['identica'],
                                   new_friend['twitter']), ())))
        if len(new_friend['twitter']) > len(new_friend['identica']):
            timers.extend(new_friend['twitter'][len(new_friend['identica']):])
        else:
            timers.extend(new_friend['identica'][len(new_friend['twitter']):])
    st.setValue('count',len(timers))
    for i in range(len(timers)):
        st.setValue(str(i), timers[i])
    timers = list(map(lambda t: [float(t[0])] + t[1:],
                  map(lambda t: unicode(t).split(","), timers)))

    def update_user(service, user, count, ok): # new_updates count
        service, user = unicode(service), unicode(user)
        cur, n = None, -1
        for i, timer in enumerate(timers):
            if timer[1] == "user" and timer[2] == service and timer[3] == user:
                n, cur = i, timer
                break
        if cur is None: return
        cur[0] = time() - (not ok) * 5 - count / len(timers)
        st.setValue(str(n), ",".join(map(unicode, cur)))

    def update_friends(service, user): # new_updates count
        service, user = unicode(service), unicode(user)
        cur, n = None, -1
        for i, timer in enumerate(timers):
            if timer[1] == "friends" and timer[2] == service:
                n, cur = i, timer
                break
        if cur is None: return
        cur[0] = time()
        st.setValue(str(n), ",".join(map(unicode, cur)))

    def timer_step():
        print "* timer update"
        cur = timers[0]
        for timer in timers:
            if timer[0] < cur[0]:
                cur = timer
        print cur
        update[cur[1]](*cur[2:])

    updates.user = update_user
    updates.friends = update_friends
    app.timer.timeout.connect(timer_step)
    app.timer.setInterval(app.settings.value("timer/interval",1e4).toInt()[0]) # 10 sec
    if app.settings.value("timer/active", True).toBool():
        app.timer.start()


pages = pages()

