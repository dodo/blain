
from traceback import print_exc

from PyQt4.Qt import QThread, QSettings

from microblogging import api_call
from json_hack import json
from parsing import drug, parse_post, parse_date


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
        return api_call(service, 'statuses/user_timeline', options)
    except:
        print_exc()
        return []



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

        n, i = 1, 0
        _id = ''
        trys = 0
        page = 1
        step = 200

        new_statuses = None

        try:
            servicecount = api_call(self.service, 'users/show',
                {'id': self.user})['statuses_count']
        except:
            print_exc()
            self.app.killThread.emit(self.id)
            self.quit()
            return
        while servicecount > 0:
            fetch_count = min(n==1 and int(step/10) or step, servicecount)
            print "%i Fetching %i from page %i, %i updates remaining (%s)" % \
                (n, fetch_count, page, servicecount, self.service),"[%i]"%trys
            new_statuses = get_page(self.service, self.user, fetch_count,
                page, page == 2 and _id and {'max_id':_id} or {})
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
                    self.knownids.append(_id)
                    self.app.addMessage.emit(update)
            n += 1
            self.yieldCurrentThread()
            if stop or trys > 3: break
            if fetch_count != int(step/10):
                page += 1

        if i:
            self.app.logStatus.emit("%i updates on %s from %s" % \
                (i, self.service, self.user))
        else:
            self.app.logStatus.emit("Error: no results! ("+self.service+")")
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

    def __init__(self, app, user, service):
        QThread.__init__(self, app)
        self.app = app
        self.user = user
        self.service = service
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
        for user in self.friends.allKeys() + [self.user]:
            opts = {'user':user, 'service':self.service}
            self.app.updateUser.emit(opts)
        print "done."
        self.quit()

pages = pages()

