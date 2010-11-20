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
        ))



class Slots:
    def __init__(self, app):
        self.app = app

    def connect(self):
        win = self.app.window
        win.connect(win.sendButton, signal.clicked, self.sendMessage)
        win.connect(win.messageEdit, signal.returnPressed, self.sendMessage)
        win.connect(win.messageEdit, signal.textChanged, self.sendButtonController)

    def sendMessage(self):
        txt = self.app.window.messageEdit.text()
        if txt != "":
            self.app.addMessage(txt)
            self.app.window.messageEdit.setText("")

    def sendButtonController(self, text):
        self.app.window.sendButton.setEnabled( text != "" )

class Blain(qt.QApplication):
    def __init__(self):
        qt.QApplication.__init__(self, sys.argv)
        self.messages = [];
        self.window = uic.loadUi("window.ui")
        self.slots = Slots(self)
        self.slots.connect()

    def run(self):
        self.window.show()
        sys.exit(self.exec_())

    def addMessage(self, text):
        mt = self.window.messageTable
        mt.insertRow(0)
        msg = uic.loadUi("message.ui")
        msg.messageLabel.setText(text)
        self.messages.append(msg)
        mt.setCellWidget(0, 0, msg)


if __name__ == "__main__":
    Blain().run()