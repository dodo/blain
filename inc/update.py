
from time import time

from PyQt4.Qt import QTimer, QSettings

from inc.parse import drug

class Updater:

    def __init__(self, app):
        if not hasattr(app, 'preferences'):
            print("update: need 'preferences' from app.")
            exit(1)
        self.app = app
        self.update = {}
        self.timers = []
        self.updates = drug()
        self.timer = QTimer(app)
        self.settings = QSettings("blain", "timers")


    def connect(self):
        win = self.app.window.ui
        win.actionDoUpdates.triggered.connect(self.do)
        win.actionUpdate_now.triggered.connect(self.all)
        self.timer.timeout.connect(self.timer_step)
        self.app.window.ui.actionDoUpdates.setChecked(
            self.app.preferences.settings.value("timer/active",True).toBool())


    def setup(self):
        app, st, pref = self.app, self.settings, self.app.preferences.settings
        self.update['user'] = app.updateUser.emit
        self.update['friends'] = lambda *args: \
            app.updateMicroblogging.emit(args[0],
            app.preferences.settings.value(\
            "account/"+args[0]+"/id").toString(),\
            False, *args[2:])
        friends = drug(twitter = [], identica = [])
        if pref.contains("account/twitter/id"):
            friends.twitter  = map(unicode, QSettings("blain",
                "%s-twitter-friends" % pref.value("account/twitter/id").\
                toString()).allKeys())
        if pref.contains("account/identica/id"):
            friends.identica = map(unicode, QSettings("blain",
                "%s-identica-friends" % pref.value("account/identica/id").\
                toString()).allKeys())
        # format: (timestamp, func, service, user, *args)
        self.timers = timers = [ unicode(st.value(str(i)).toString())
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
        self.timers = list(map(lambda t: [float(t[0])] + t[1:],
                        map(lambda t: unicode(t).split(","), timers)))

        self.updates.user = self.user
        self.updates.friends = self.friends
        self.timer.setInterval(
            pref.value("timer/interval",1e4).toInt()[0]) # 10 sec
        if pref.value("timer/active", True).toBool():
            self.timer.start()


    def user(self, service, user, count , ok): # new_updates count
        service, user = unicode(service), unicode(user)
        cur, n = None, -1
        for i, timer in enumerate(self.timers):
            if timer[1] == "user" and timer[2] == service and timer[3] == user:
                n, cur = i, timer
                break
        if cur is None: return
        cur[0] = time() - (not ok) * 5 - count / len(self.timers)
        self.settings.setValue(str(n), ",".join(map(unicode, cur)))


    def friends(self, service, user): # new_updates count
        service, user = unicode(service), unicode(user)
        cur, n = None, -1
        for i, timer in enumerate(self.timers):
            if timer[1] == "friends" and timer[2] == service:
                n, cur = i, timer
                break
        if cur is None: return
        cur[0] = time()
        self.settings.setValue(str(n), ",".join(map(unicode, cur)))


    def timer_step(self):
        print "* timer update"
        cur = self.timers[0]
        for timer in self.timers:
            if timer[0] < cur[0]:
                cur = timer
        print cur
        self.update[cur[1]](*cur[2:])


    def twitter(self, start = True):
        self.app.threads.updateMicroblogging('twitter',
            self.app.preferences.ui.twitteridEdit.text())
        if start:
            self.app.threads.start('twitter')


    def identica(self, start = True):
        self.app.threads.updateMicroblogging('identica',
            self.app.preferences.ui.identicaidEdit.text())
        if start:
            self.app.threads.start('identica')


    def do(self, checked):
        if checked: self.timer.start()
        else:       self.timer.stop()
        self.app.preferences.settings.setValue("timer/active", checked)


    def all(self):
        self.identica(False)
        self.twitter(False)
        self.app.threads.start('twitter', 'identica')

