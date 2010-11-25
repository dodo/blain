#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from datetime import datetime

from PyQt4 import uic, Qt as qt

from pager import Pager
from ascii import get_logo
from update import MicroblogThread, UserStatusThread
from getFavicon import get_favicon
from parsing import drug, parse_image



class Slots:
    def __init__(self, app):
        self.app = app
        self.threads = {}

    def connect(self):
        win = self.app.window
        win.sendButton.clicked.connect(self.sendMessage)
        win.messageEdit.returnPressed.connect(self.sendMessage)
        win.messageEdit.textChanged.connect(self.sendButtonController)
        win.actionUpdate_now.triggered.connect(self.updateAll)
        win.actionMinimize.triggered.connect(win.hide)
        win.actionQuit.triggered.connect(self.app.quit)
        win.actionPreferences.triggered.connect(self.showPref)
        win.actionSilence.triggered.connect(self.test)
        pref = self.app.preferences
        pref.buttonBox.accepted.connect(self.acceptPref)
        pref.buttonBox.rejected.connect(self.rejectPref)
        pref.buttonBox.button(qt.QDialogButtonBox.Apply).clicked.connect(self.saveSettings)
        pref.listWidget.currentRowChanged.connect(pref.stackedWidget.setCurrentIndex)
        tray = self.app.trayIcon
        tray.activated.connect(self.clickTray)

    def sendMessage(self):
        # TODO send message instead of printing it
        txt = self.app.window.messageEdit.text()
        if txt != "":
            self.app.addMessage.emit(
                {'time':datetime.now(),'text':txt,'info':"test"})
            self.app.window.messageEdit.setText("")

    def sendButtonController(self, text):
        self.app.window.sendButton.setEnabled( text != "" )

    def showPref(self, _):
        self.app.window.setEnabled(False)
        self.app.preferences.show()

    def hidePref(self):
        self.app.preferences.hide()
        self.app.window.setEnabled(True)

    def updateMicroblogging(self, service, text, icon):
        if service in self.threads and self.threads[service].isRunning():
            print "update %s already running" % service
            return
        self.threads[service] = MicroblogThread(self.app, text, service, icon)
        self.threads[service].start()

    def updateTwitter(self):
        self.updateMicroblogging('twitter',
            self.app.preferences.twitteridEdit.text(),
            self.app.twitterIcon)

    def updateIdentica(self):
        self.updateMicroblogging('identica',
            self.app.preferences.identicaidEdit.text(),
            self.app.identicaIcon)


    def updateAll(self):
        self.app.messages = []
        self.app.window.messageTable.clear()
        self.updateIdentica()
        self.updateTwitter()

    def saveSettings(self):
        app = self.app
        setts = app.settings
        pref = app.preferences
        setts.setValue("account/twitter/id", pref.twitteridEdit.text())
        setts.setValue("account/identica/id", pref.identicaidEdit.text())
        setts.setValue("icon/isdark", pref.darkradioButton.isChecked())
        ai = app.appIcon = qt.QIcon(qt.QPixmap(
            get_logo(dark=setts.value("icon/isdark").toBool())))
        app.setWindowIcon(ai)
        app.trayIcon.setIcon(ai)


    def loadSettings(self):
        setts = self.app.settings
        pref = self.app.preferences
        pref.identicaidEdit.setText(setts.value("account/identica/id").toString())
        pref.twitteridEdit.setText(setts.value("account/twitter/id").toString())
        b = setts.value("icon/isdark",True).toBool()
        pref.darkradioButton.setChecked(b)
        pref.lightradioButton.setChecked(not b)

    def rejectPref(self):
        self.hidePref()
        self.loadSettings()

    def acceptPref(self):
        self.hidePref()
        self.saveSettings()

    def clickTray(self, reason):
        if reason == qt.QSystemTrayIcon.Trigger:
            self.app.window.setVisible(not self.app.window.isVisible())

    def test(self):
        from update import get_friends, get_user
        from pprint import pprint
        #pprint(get_friends('twitter', 'dodothelast'))
        #pprint(get_friends('identica', 'dodothelast'))
        pprint(get_user('twitter', 'dodothelast'))
        pprint(get_user('identica', 'dodothelast'))
        print "done."



class PreferencesDialog(qt.QDialog):
    def __init__(self, app, *args):
        qt.QDialog.__init__(self, *args)
        self.app = app
        uic.loadUi("preferences.ui", self)
        self.darkradioButton.setIcon(qt.QIcon(qt.QPixmap(get_logo())))
        self.lightradioButton.setIcon(qt.QIcon(qt.QPixmap(get_logo(dark=False))))

    def closeEvent(self, event):
        self.hide()
        self.app.window.setEnabled(True)
        event.ignore()



class Blain(qt.QApplication):

    logStatus = qt.pyqtSignal((str,), (str, int))
    killThread = qt.pyqtSignal(str)
    addMessage = qt.pyqtSignal(dict)
    updateUser = qt.pyqtSignal(dict)

    def __init__(self):
        print "loading …"
        qt.QApplication.__init__(self, sys.argv)

        def load_icon(id, name, url):
            icon, setts = None, self.settings
            if not setts.contains('icon/'+name):
                icon = get_favicon(url)
                if icon:
                    icon = qt.QIcon(qt.QPixmap.fromImage(qt.QImage.fromData(icon)))
                    print name, "icon loaded?", not icon.isNull()
                    if not icon.isNull():
                        setts.setValue('icon/'+name, icon)
                else: print "error while loading", name, "icon"
            else:
                icon = setts.value('icon/'+name, None)
                if icon: icon = qt.QIcon(icon)
            if icon:
                self.preferences.accountsTabWidget.setTabIcon(id, icon)
            return icon

        self.threads = {}
        self.messages = []
        self.avatar_cache = {}
        self.threadwatcher = None
        self.logStatus.connect(self._logStatus)
        self.addMessage.connect(self._addMessage)
        self.killThread.connect(self._killThread)
        self.updateUser.connect(self._updateUser)

        self.window = uic.loadUi("window.ui")
        self.window.messageTable.hideColumn(0)
        self.preferences = PreferencesDialog(self)
        st = self.settings = qt.QSettings("blain", "blain")
        self.avatars = qt.QSettings("blain", "avatars")
        self.pager = Pager(self)

        self.appIcon = qt.QIcon(qt.QPixmap(get_logo(dark=st.value("icon/isdark",True).toBool())))
        self.setWindowIcon(self.appIcon)
        self.trayIcon = qt.QSystemTrayIcon(self.appIcon, self)
        self.trayIcon.show()

        # load settings
        self.identicaIcon = load_icon(0, "identica", "http://identi.ca")
        self.twitterIcon  = load_icon(1, "twitter", "http://twitter.com")

        self.slots = Slots(self)
        self.slots.loadSettings()
        self.slots.connect()
        self.window.actionUpdate_view.triggered.connect(self.updateMessageView)

    def run(self):
        self.window.show()
        self.window.statusBar.showMessage("Ready ...", 3000)
        print "done."
        sys.exit(self.exec_())

    def updateMessageView(self, maxcount = 200):
        mt = self.window.messageTable
        self.avatar_cache = {}
        mt.clear()
        if len(self.messages) < 200:
            self.messages.sort(key=lambda m:m['time'])
        for _blob in self.messages[-maxcount:]:
            blob = drug(**_blob)
            time = blob.time.strftime("%Y-%m-%d %H:%M:%S")
            msg = uic.loadUi("message.ui") # TODO chache this
            msg.messageLabel.setText(blob.text)
            msg.infoLabel.setText(blob.info)
            if 'icon' in _blob:
                msg.serviceLabel.setPixmap(blob.icon.pixmap(16,16))
            if 'imageinfo' in _blob:
                image = parse_image(*([self]+blob.imageinfo))
                if image[0]:
                    msg.avatarLabel.setPixmap(image[0])
                    self.avatar_cache[image[1]] = msg.avatarLabel
            i = qt.QTreeWidgetItem(mt)
            i.setText(0, time)
            mt.setItemWidget(i, 1, msg)

    def _logStatus(self, msg, time=5000):
        print msg
        self.window.statusBar.showMessage(msg, time)
        self.window.statusBar.update()

    def _addMessage(self, blob):
        blob = dict([(str(k),blob[k]) for k in blob])
        self.messages.append(blob)
        if len(self.messages) > 200:
            self.messages.sort(key=lambda m:m['time'])
            self.messages.pop(0)

    def _killThread(self, id):
        id = str(id)
        if id in self.threads:
            del self.threads[id]
        print len(self.threads),"threads still running:  ",", ".join(self.threads.keys()),"-"*40
        if not self.threads:
            self.updateMessageView()
        else:
            self.updateMessageView(10)

    def _updateUser(self, _blob):
        _blob = dict([(str(k),_blob[k]) for k in _blob])
        for k in ['user', 'service']:
            _blob[k] = str(_blob[k])
        blob = drug(**_blob)
        id = blob.service+blob.user
        if id in self.threads and self.threads[id].isRunning():
            print blob.user, "thread still running. (%s)" % blob.service
        else:
            if 'icon' not in _blob:
                blob.icon = None
            self.threads[id] = UserStatusThread(
                self, id, blob.user, blob.service, blob.icon)
            self.threads[id].start()



if __name__ == "__main__":
    Blain().run()