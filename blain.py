# -*- coding: utf-8 -*-

import sys

from PyQt4 import uic, Qt as qt


class drug():
    def __init__(self, **kwargs):
        for k in kwargs:
            setattr(self, k, kwargs[k])


signal = drug(**dict(
        clicked = qt.SIGNAL("clicked()"),
        returnPressed = qt.SIGNAL("returnPressed()"),
        textChanged = qt.SIGNAL("textChanged(const QString&)"),
        triggered = qt.SIGNAL("triggered(bool)"),
        hide = qt.SIGNAL("hide()"),
        abstractbuttonclicked = qt.SIGNAL("clicked(QAbstractButton *)"),
        ))



class Slots:
    def __init__(self, app):
        self.app = app

    def connect(self):
        win = self.app.window
        win.connect(win.sendButton, signal.clicked, self.sendMessage)
        win.connect(win.messageEdit, signal.returnPressed, self.sendMessage)
        win.connect(win.messageEdit, signal.textChanged, self.sendButtonController)
        win.connect(win.actionQuit, signal.triggered, self.quit)
        win.connect(win.actionPreferences, signal.triggered, self.showPreferences)
        pref = self.app.preferences
        pref.connect(pref, signal.hide, self.hidePreferences)
        pref.connect(pref.buttonBox, signal.abstractbuttonclicked, self.abPref)

    def sendMessage(self):
        txt = self.app.window.messageEdit.text()
        if txt != "":
            self.app.addMessage(txt)
            self.app.window.messageEdit.setText("")

    def sendButtonController(self, text):
        self.app.window.sendButton.setEnabled( text != "" )

    def quit(self, _):
        self.app.quit()

    def showPreferences(self, _):
        self.app.window.setEnabled(False)
        self.app.preferences.show()

    def hidePreferences(self):
        self.app.window.setEnabled(True)

    def abPref(self, button):
        print button
        self.app.preferences.hide()
        self.app.window.setEnabled(True)



class Blain(qt.QApplication):
    def __init__(self):
        qt.QApplication.__init__(self, sys.argv)
        self.messages = [];
        self.window = uic.loadUi("window.ui")
        self.preferences = uic.loadUi("preferences.ui")
        self.slots = Slots(self)
        self.slots.connect()

    def run(self):
        self.window.show()
        self.window.statusBar.showMessage("Ready ...", 3000)
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