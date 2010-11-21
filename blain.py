# -*- coding: utf-8 -*-

import sys

from PyQt4 import uic, Qt as qt

from getFavicon import get_favicon
from microblogging import get_statuses



class drug():
    def __init__(self, **kwargs):
        for k in kwargs:
            setattr(self, k, kwargs[k])



class Slots:
    def __init__(self, app):
        self.app = app

    def connect(self):
        win = self.app.window
        win.sendButton.clicked.connect(self.sendMessage)
        win.messageEdit.returnPressed.connect(self.sendMessage)
        win.messageEdit.textChanged.connect(self.sendButtonController)
        win.actionUpdate_now.triggered.connect(self.updateAll)
        win.actionQuit.triggered.connect(self.app.quit)
        win.actionPreferences.triggered.connect(self.showPreferences)
        pref = self.app.preferences
        #pref.hide.connect
        pref.buttonBox.clicked.connect(self.abPref)
        pref.listWidget.currentRowChanged.connect(pref.stackedWidget.setCurrentIndex)

    def logStatus(self, msg, time=5000):
        print msg
        self.app.window.statusBar.showMessage(msg, time)

    def sendMessage(self):
        txt = self.app.window.messageEdit.text()
        if txt != "":
            self.app.addMessage(txt)
            self.app.window.messageEdit.setText("")

    def sendButtonController(self, text):
        self.app.window.sendButton.setEnabled( text != "" )

    def showPreferences(self, _):
        self.app.window.setEnabled(False)
        self.app.preferences.show()

    def abPref(self, button):
        print button
        self.app.preferences.hide()
        self.app.window.setEnabled(True)

    def updateMicroblogging(self, service):
        user = self.app.preferences.twitteridEdit.text()
        if user != "":
            self.logStatus("===> Fetching %s on %s" % (user, service))
            updates = get_statuses(service, user)
            if not updates:
                self.logStatus("Error: no results!")
            else:
                self.logStatus("Amount of updates:  %i" % len(updates))
                print
                for update in updates:
                    update = drug(**update)
                    self.app.addMessage(update.text)
        else:
            self.logStatus("Error: no user given!")

    def updateTwitter(self):
        self.updateMicroblogging("twitter")

    def updateIdentica(self):
        self.updateMicroblogging("identica")

    def updateAll(self):
        self.updateIdentica()
        self.updateTwitter()



class PreferencesDialog(qt.QDialog):
    def __init__(self, app, *args):
        qt.QDialog.__init__(self, *args)
        self.app = app
        self.content = uic.loadUi("preferences.ui", self)

    def closeEvent(self, event):
        print "lol", event
        self.hide()
        self.app.window.setEnabled(True)



class Blain(qt.QApplication):
    def __init__(self):
        print "loading …"
        qt.QApplication.__init__(self, sys.argv)
        self.messages = [];
        self.window = uic.loadUi("window.ui")
        self.preferences = PreferencesDialog(self)

        icon = get_favicon("http://identi.ca")
        if icon:
            icon = qt.QIcon(qt.QPixmap.fromImage(qt.QImage.fromData(icon)))
            print "identica icon loaded?", not icon.isNull()
            self.preferences.accountsTabWidget.setTabIcon(0, icon)
        else: print "error while loading identica icon"
        self.identicaIcon = icon

        icon = get_favicon('http://twitter.com')
        if icon:
            icon = qt.QIcon(qt.QPixmap.fromImage(qt.QImage.fromData(icon)))
            print "twitter icon loaded?", not icon.isNull()
            self.preferences.accountsTabWidget.setTabIcon(1, icon)
        else: print "error while loading twitter icon"
        self.twitterIcon = icon

        self.slots = Slots(self)
        self.slots.connect()

    def run(self):
        self.window.show()
        self.window.statusBar.showMessage("Ready ...", 3000)
        print "done."
        sys.exit(self.exec_())

    def addMessage(self, text):
        mt = self.window.messageTable
        msg = uic.loadUi("message.ui")
        msg.messageLabel.setText(text)
        self.messages.append(msg)
        i = qt.QTreeWidgetItem(mt)
        mt.setItemWidget(i, 0, msg)


if __name__ == "__main__":
    Blain().run()