#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from PyQt4 import uic, Qt as qt

from parsing import parse_post
from ascii import get_logo
from getFavicon import get_favicon
from microblogging import get_statuses

urls = {
    'identica': "http://identi.ca/",
    'twitter':  "http://twitter.com/",
    }

class Slots:
    def __init__(self, app):
        self.app = app

    def connect(self):
        win = self.app.window
        win.sendButton.clicked.connect(self.sendMessage)
        win.messageEdit.returnPressed.connect(self.sendMessage)
        win.messageEdit.textChanged.connect(self.sendButtonController)
        win.actionUpdate_now.triggered.connect(self.updateAll)
        win.actionMinimize.triggered.connect(win.hide)
        win.actionQuit.triggered.connect(self.app.quit)
        win.actionPreferences.triggered.connect(self.showPref)
        pref = self.app.preferences
        pref.buttonBox.accepted.connect(self.acceptPref)
        pref.buttonBox.rejected.connect(self.rejectPref)
        pref.buttonBox.button(qt.QDialogButtonBox.Apply).clicked.connect(self.saveSettings)
        pref.listWidget.currentRowChanged.connect(pref.stackedWidget.setCurrentIndex)
        tray = self.app.trayIcon
        tray.activated.connect(self.clickTray)

    def logStatus(self, msg, time=5000):
        print msg
        self.app.window.statusBar.showMessage(msg, time)
        self.app.window.statusBar.update()

    def sendMessage(self):
        # TODO send message instead of printing it
        txt = self.app.window.messageEdit.text()
        if txt != "":
            self.app.addMessage(datetime.now(), txt)
            self.app.window.messageEdit.setText("")

    def sendButtonController(self, text):
        self.app.window.sendButton.setEnabled( text != "" )

    def showPref(self, _):
        self.app.window.setEnabled(False)
        self.app.preferences.show()

    def hidePref(self):
        self.app.preferences.hide()
        self.app.window.setEnabled(True)

    def updateMicroblogging(self, user, service, icon=None):
        if user != "":
            self.logStatus("===> Fetching %s on %s" % (user, service))
            updates = get_statuses(service, user)
            if not updates:
                self.logStatus("Error: no results!")
            else:
                self.logStatus("Amount of updates:  %i" % len(updates))
                print
                #print updates[0]
                for update in updates:
                    update = parse_post(urls[service], update)
                    self.app.addMessage(update.created_at, update.text, icon)
        else:
            self.logStatus("Error: no user given!")

    def updateTwitter(self):
        self.updateMicroblogging(
            self.app.preferences.twitteridEdit.text(), "twitter",
            self.app.twitterIcon)

    def updateIdentica(self):
        self.updateMicroblogging(
            self.app.preferences.identicaidEdit.text(), "identica",
            self.app.identicaIcon)

    def updateAll(self):
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

        self.messages = [];
        self.window = uic.loadUi("window.ui")
        self.window.messageTable.hideColumn(0)
        self.preferences = PreferencesDialog(self)
        st = self.settings = qt.QSettings("blain")

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

    def run(self):
        self.window.show()
        self.window.statusBar.showMessage("Ready ...", 3000)
        print "done."
        sys.exit(self.exec_())

    def addMessage(self, time, text, icon=None):
        time = time.strftime("%Y-%m-%d %H:%M:%S")
        mt = self.window.messageTable
        msg = uic.loadUi("message.ui")
        msg.messageLabel.setText(text)
        msg.messageLabel.setOpenExternalLinks(True)
        if icon:
            msg.serviceLabel.setPixmap(icon.pixmap(16,16))
        self.messages.append(msg)
        i = qt.QTreeWidgetItem(mt)
        i.setText(0, time)
        mt.setItemWidget(i, 1, msg)


if __name__ == "__main__":
    #print "logo in settings → light and dark theme"
    Blain().run()