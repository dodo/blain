

from traceback import print_exc


class Notifier:

    def __init__(self, app):
        if not hasattr(app, 'window'):
            print("notification: need 'window' from app.")
            exit(1)
        if not hasattr(app, 'preferences'):
            print("notification: need 'preferences' from app.")
            exit(1)
        self.app = app
        self.mode = 'disabled'
        self.buttons = {}
        self.notifies = {}
        self.enabled = True
        self.settings = app.preferences.settings


    def connect(self):
        self.app.window.ui.actionSilence.triggered.connect(self.triggerEnabled)


    def setup(self):
        win, pref = self.app.window.ui, self.app.preferences.ui
        self.enabled = self.settings.value("notification/enable", True).toBool()
        self.buttons['disabled'] = pref.notif_disabledButton
        self.buttons['amount'] = pref.notif_amountButton
        self.buttons['user'] = pref.notif_userButton
        self.mode = str(self.settings.value(
            "notification/mode", self.mode).toString())
        try:
            import dbus
            self.dbus = dbus
            pref.notinstalledLabel.setVisible(False)
            sb = dbus.SessionBus()
            notif = sb.get_object('org.freedesktop.Notifications',
                                 '/org/freedesktop/Notifications')
            notify = dbus.Interface(notif, 'org.freedesktop.Notifications')
            self.Notify = notify.Notify
        except:
            win.actionSilence.setEnabled(False)
            pref.notificationSettings.setVisible(False)
            self.Notify = lambda *args, **kwargs: None
            print "[ERROR] cannot get dbus interface"
            print_exc()
            return
        self.notifies['amount'] = self.notify_amount
        self.notifies['user'] = self.notify_user
        win.actionSilence.setChecked(not self.enabled)
        self.resetRadioButtons()
        self.set_action_mode()


    def resetRadioButtons(self):
        button = str(self.settings.value(
            "notification/mode", self.mode).toString())
        if button in self.buttons:
            self.buttons[button].setChecked(True)
        else: print "notification: %s not found in resetButtons" % button


    def saveRadioButtons(self):
        for name, button in self.buttons.items():
            if button.isChecked():
                self.settings.setValue("notification/mode", name)
                self.mode = name
                self.set_action_mode()
                break


    def set_action_mode(self):
        self.app.window.ui.actionSilence.setEnabled(self.mode != 'disabled')



    def triggerEnabled(self, b):
        b = not b
        self.enabled = b
        self.settings.setValue("notification/enable", b)


    def setEnabled(self, b):
        self.triggerEnabled(not b)
        self.app.window.ui.actionSilence.setChecked(b)


    def enable(self):
        self.setEnabled(True)


    def disable(self):
        self.setEnabled(False)


    def notify(self, text, time = 1e4):
        if self.enabled:
            self.Notify("Blain", 0, "", "Blain", text, [], [], time)


    def notify_by_mode(self, **kwargs):
        if self.mode != 'disabled':
            self.notifies[self.mode](**kwargs)


    def notify_amount(self, amount = None, **_):
        if self.mode == 'amount':
            self.notify("{0} new Posts".format(amount))


    def notify_user(self, user = None, amount = None, **_):
        if self.mode == 'user':
            self.notify("{1} new Posts by {0}".format(user, amount))


