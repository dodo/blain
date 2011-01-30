
from time import time
from random import seed, shuffle

from PyQt4.Qt import QTimer, QSettings

from inc.parse import drug


seed()


class Updater:

    def __init__(self, app):
        if not hasattr(app, 'preferences'):
            print("update: need 'preferences' from app.")
            exit(1)
        if not hasattr(app, 'accounts'):
            print("update: need 'accounts' from app.")
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
            self.app.preferences.settings.value("timer/active",False).toBool())


    def setup(self):
        app, st, pref = self.app, self.settings, self.app.preferences.settings
        account_id = {}
        # thread starting functions
        self.update['user'] = app.updateUser.emit
        self.update['group'] = app.updateGroup.emit
        self.update['groups'] = lambda *args: \
            app.updateGroups.emit(*(args[:2]+(False,)+args[3:]))
        self.update['friends'] = lambda *args: \
            app.updateFriends.emit(*(args[:2]+(False,)+args[3:]))
        # read existing friends and groups
        friends, friends_list, groups, groups_list = {}, {}, {}, {}
        for account in self.app.accounts.get():
            if account.service not in friends:
                friends[account.service] = {}
            if account.service not in friends_list:
                friends_list[account.service] = []
            friends_list[account.service].append(account.name)
            friends[account.service][account.name] = \
                list(map(unicode, account.friends.allKeys())) + [account.name]
            if account.groups is not None:
                if account.service not in groups:
                    groups[account.service] = {}
                if account.service not in groups_list:
                    groups_list[account.service] = []
                groups_list[account.service].append(account.name)
                groups[account.service][account.name] = \
                    list(map(unicode, account.groups.allKeys()))
        # read existing timer events

        # format: (timestamp, func, service, account, user, *args)
        timers = [ unicode(st.value(str(i)).toString())
                for i in range(st.value("count",0).toInt()[0]) ]

        #find new timer events
        user_leveled = {'user': friends, 'group': groups}
        account_leveled = {'friends': friends_list, 'groups': groups_list}
        for timer in map(lambda t: unicode(t).split(","), timers):
            if timer[1] == 'user' or timer[1] == 'group':
                # choose current data
                service_level = user_leveled[timer[1]]
                # dive data levels
                if timer[2] in service_level:
                    account_level = service_level[timer[2]]
                    if timer[3] in account_level:
                        user_level = account_level[timer[3]]
                        if timer[4] in user_level:
                            # event found, remove it
                            user_level.remove(timer[4])
            elif timer[1] == 'friends' or timer[1] == 'groups':
                # choose current data
                service_level = account_leveled[timer[1]]
                # dive data levels
                if timer[2] in service_level:
                    account_level = service_level[timer[2]]
                    if timer[3] in account_level:
                        # event found, remove it
                        account_level.remove(timer[3])
        # save left overs
        t = time()
        # add new group lists
        timers.extend([ u"{0},groups,{1},{2},".format(t, service, account)
                        for service in groups_list
                        for account in groups_list[service] ])
        # add new friend lists
        timers.extend([ u"{0},friends,{1},{2},".format(t, service, account)
                        for service in friends_list
                        for account in friends_list[service] ])
        # add new groups
        timers.extend([ u"{0},group,{1},{2},{3}".format(t,service,account,group)
                        for service in groups
                        for account in groups[service]
                        for group   in groups[service][account] ])
        # add new friends
        timers.extend([ u"{0},user,{1},{2},{3}".format(t,service,account,user)
                        for service in friends
                        for account in friends[service]
                        for user    in friends[service][account] ])
        # add some random to the order so twitter
        #   wont get called to often in a row hopfully
        if len(timers) != st.value("count", 0).toInt()[0]:
            shuffle(timers) # inplace
        # save new timers
        st.setValue('count',len(timers))
        for i, timer in enumerate(timers):
            st.setValue(str(i), timer)
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


    def add_timer(self, func, service, account, user, *args):
        timer = ",".join(map(unicode, [time(), func, service, account, user]))
        if args:
            timer += "," + ",".join(map(unicode, args))
        self.settings.setValue(str(len(self.timers)), timer)
        timer = timer.split(",")
        self.timers.append([float(timer[0])] + timer[1:])
        self.settings.setValue("count", len(self.timers))


    def remove_timer(self, func, service, account, user):
        found, cur = [], ",".join(map(unicode, [func, service, account, user]))
        for i, timer in enumerate(self.timers):
            if cur in ",".join(map(unicode, timer)):
                found.append(i)
        if not found: return
        for i in reversed(found):
            self.timers.pop(i)
        self.settings.setValue('count',len(self.timers))
        for i, timer in enumerate(self.timers[found[0]:]):
            self.settings.setValue(str(i+found[0]),",".join(map(unicode,timer)))


    def new_updates(self, account, new_time, break_): # new_updates count
        cur, n, service, accid = None, -1, account.service, account.name
        for i, timer in enumerate(self.timers):
            if service == timer[2] and accid == timer[3] and break_(timer):
                n, cur = i, timer
                break
        if cur is None: return
        cur[0] = new_time
        self.settings.setValue(str(n), ",".join(map(unicode, cur)))


    def user(self, account, user, count, ok): # new_updates count
        if count:
            self.app.notifier.notify_by_mode(
                amount = count, user = user)
        self.new_updates(account,
            time() - (not ok) * 5 - count / len(self.timers),
            lambda t: t[1] == "user" and t[4] == user)


    def group(self, account, group, count, ok): # new_updates count
        if count:
            self.app.notifier.notify_by_mode(
                amount = count, user = "group " + group)
        self.new_updates(account,
            time() - (not ok) * 5 - count / len(self.timers),
            lambda t: t[1] == "group" and t[4] == group)


    def groups(self, account): # new_updates count
        self.new_updates(account, time(), lambda t: t[1] == "groups")


    def friends(self, account): # new_updates count
        self.new_updates(account, time(), lambda t: t[1] == "friends")


    def timer_step(self):
        cur = self.timers[0]
        for timer in self.timers:
            if timer[0] < cur[0]:
                cur = timer
        print "* timer update", cur
        self.update[cur[1]](*cur[2:])


    def account(self, account, start = True):
        acc = account.service, account.name
        ids = [u"{0}{1}friends".format(*acc)]
        self.app.threads.updateFriends(*acc)
        if account.groups is not None:
            ids.append(u"{0}{1}groups".format(*acc))
            self.app.threads.updateGroups(*acc)
        if start:
            self.app.threads.start(*ids)
            return []
        return ids


    def do(self, checked):
        if checked: self.timer.start()
        else:       self.timer.stop()
        self.app.preferences.settings.setValue("timer/active", checked)


    def all(self):
        self.app.threads.start(
            *sum([ self.account(account,False)
            for account in self.app.accounts.get() ],[]))


