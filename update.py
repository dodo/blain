
from PyQt4.Qt import QThread, QSettings

from microblogging import api_call
from json_hack import json
from parsing import drug


def pages():
    return {
        'twitter': drug(
            next = next_twitter_page,
            get = get_twitter_friends),
        'identica': drug(
            next = next_identica_page,
            get = get_identica_friends)
        }


class UserStatusThread(QThread):

    def __init__(self, app, user, service, icon=None):
        QThread.__init__(self, app)
        self.app = app
        self.icon = icon
        self.user = user
        self.service = service

    def run(self):
        if self.user == "":
            self.app.logStatus.emit("Error: no user given! ("+self.service+")")
            self.quit()
        self.app.pager.update(self.service, self.user)
        updates =  self.app.pager.load_page(self.service, self.user)
        if not updates:
            self.app.logStatus.emit("Error: no results! ("+self.service+")")
            self.quit()
        self.app.logStatus.emit("Amount of updates:  %i" % len(updates))
        print
        for update in updates[:10]:
            update.icon = self.icon
            self.app.addMessage.emit(update.__dict__)
        print self.service + " done."
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
    return pages[service].get(api_call(service, 'statuses/friends', options))


def next_page(service, prev, result):
    return pages[service].next(prev, result)



class MicroblogThread(QThread):

    def __init__(self, app, user, service, icon=None):
        QThread.__init__(self, app)
        self.app = app
        self.icon = icon
        self.user = user
        self.service = service
        self.friends = QSettings("blain", "%s-%s-friends" % (user, service))

    def run(self):
        if not self.service or not self.user:
            return self.quit()
        trys = 0
        page = -1
        new_friends = None
        friendscount = api_call(self.service, 'users/show',
            {'id': self.user})['friends_count']
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
        print "friends list up-to-date. (%s)" % self.service
        # update all users
        for friend in self.friends.allKeys():
            opts = {'user':friend, 'service':self.service}
            if self.icon:
                opts['icon'] = self.icon
            self.app.updateUser.emit(opts)
        print "done."
        self.quit()


pages = pages()

