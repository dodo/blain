
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
        account_id = {}
        # thread starting functions
        self.update['user'] = app.updateUser.emit
        self.update['group'] = lambda *args: app.updateGroup.emit(*args[1:])
        self.update['groups'] = lambda *args: \
            app.updateGroups.emit(args[1], False, *args[2:])
        self.update['friends'] = lambda *args: \
            app.updateMicroblogging.emit(args[0],
            account_id[service], False, *args[2:])
        # read existing friends
        friends = {}
        for service in ["twitter", "identica"]:
            friends[service] = []
            if pref.contains("account/%s/id" % service):
                account_id[service] = pref.value(
                    "account/%s/id" % service).toString()
                friends[service] = map(unicode, QSettings("blain",
                    "%s-%s-friends" % (account_id[service], service)).allKeys())
        friends = drug(**friends)
        # read existing groups
        groups = []
        if pref.contains("account/identica/id"):
            groups = map(unicode, QSettings("blain",
                "%s-groups" % account_id['identica']).allKeys())

        # format: (timestamp, func, service, user, *args)
        timers = [ unicode(st.value(str(i)).toString())
                for i in range(st.value("count",0).toInt()[0]) ]

        # find new timer entries
        new_friend = {'twitter':friends.twitter , 'identica':friends.identica}
        new_friends = new_friend.keys()
        new_group = groups
        new_groups = True
        for timer in map(lambda t: unicode(t).split(","), timers):
            if timer[1] == 'user':
                if timer[3] in new_friend[timer[2]]:
                    new_friend[timer[2]].remove(timer[3])
            elif timer[1] == 'friends':
                if timer[2] in new_friends:
                    new_friends.remove(timer[2])
            elif timer[1] == 'groups':
                new_groups = False
            elif timer[1] == 'group':
                if timer[3] in new_group:
                    new_group.remove(timer[3])
        # add new friend lists
        for service in new_friends:
            timers.append("{0},friends,{1},".format(time(), service))
        # add groups update timer
        if new_groups:
            timers.append("{0},groups,,{1}".\
                format(time(), account_id['identica']))
        # add new groups
        for group in new_group:
            timers.append("{0},group,,{1}".format(time(), group))
        # add new friends
        for service in new_friend:
            for i, user in enumerate(new_friend[service]):
                new_friend[service][i] = "{0},user,{1},{2}".\
                    format(time(),service,user)
        # zip list(friends) of both services together
        if new_friend['twitter'] or new_friend['identica']:
            timers.extend(list(sum(zip(new_friend['identica'],
                                            new_friend['twitter']), ())))
            if len(new_friend['twitter']) > len(new_friend['identica']):
                timers.extend(new_friend['twitter'][len(new_friend['identica']):])
            else:
                timers.extend(new_friend['identica'][len(new_friend['twitter']):])
        # save new timers
        st.setValue('count',len(timers))
        for i in range(len(timers)):
            st.setValue(str(i), timers[i])
        # more python readable format
        timers = [ unicode(t).split(",") for t in timers ]
        timers = [ [float(t[0])] + t[1:] for t in timers ]
        self.timers = timers
        # start timers
        self.updates.user = self.user
        self.updates.group = self.group
        self.updates.groups = self.groups
        self.updates.friends = self.friends
        self.timer.setInterval(
            pref.value("timer/interval",1e4).toInt()[0]) # 10 sec
        if pref.value("timer/active", True).toBool():
            self.timer.start()


    def new_updates(self, service, user, new_time, break_): # new_updates count
        cur, n = None, -1
        for i, timer in enumerate(self.timers):
            if break_(timer):
                n, cur = i, timer
                break
        if cur is None: return
        cur[0] = new_time
        self.settings.setValue(str(n), ",".join(map(unicode, cur)))


    def user(self, service, user, count , ok): # new_updates count
        if count:
            self.app.notifier.notify_by_mode(
                amount = count, user = user)
        service, user = unicode(service), unicode(user)
        self.new_updates(service, user,
            time() - (not ok) * 5 - count / len(self.timers),
            lambda t: t[1] == "user" and t[2] == service and t[3] == user)


    def group(self, _, group, count , ok): # new_updates count
        if count:
            self.app.notifier.notify_by_mode(
                amount = count, user = "group " + group)
        user = unicode(group)
        self.new_updates("identica", group,
            time() - (not ok) * 5 - count / len(self.timers),
            lambda t: t[1] == "group" and t[3] == group)


    def groups(self, user): # new_updates count
        user = unicode(user)
        self.new_updates('identica', user, time(),
            lambda t: t[1] == "groups")


    def friends(self, service, user): # new_updates count
        service, user = unicode(service), unicode(user)
        self.new_updates(service, user, time(),
            lambda t: t[1] == "friends" and t[2] == service)


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
        ids = ['__twitter__']
        if start:
            self.app.threads.start(*ids)
            return []
        return ids


    def identica(self, start = True):
        user = self.app.preferences.ui.identicaidEdit.text()
        self.app.threads.updateMicroblogging('identica', user)
        self.app.threads.updateGroups(user)
        ids = ['__identica__', '%s groups' % user]
        if start:
            self.app.threads.start(*ids)
            return []
        return ids


    def do(self, checked):
        if checked: self.timer.start()
        else:       self.timer.stop()
        self.app.preferences.settings.setValue("timer/active", checked)


    def all(self):
        self.app.threads.start(*(self.identica(False) + self.twitter(False)))

