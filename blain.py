# -*- coding: utf-8 -*-

import sys

from PyQt4 import uic, Qt as qt


class drug():
    def __init__(self, **kwargs):
        for k in kwargs:
            setattr(self, k, kwargs[k])


signal = drug(**dict(
        clicked = qt.SIGNAL("clicked()")))



class Slots:
    def __init__(self, app):
        self.app = app

    def connect(self):
        win = self.app.window
        win.connect(win.pushButton, signal.clicked, self.test)

    def test(self):
        print "tada!"


class Blain(qt.QApplication):
    def __init__(self):
        qt.QApplication.__init__(self, sys.argv)
        self.window = uic.loadUi("qt.ui")
        #self.window.messageWidget.hide()
        self.slots = Slots(self)
        self.slots.connect()

    def run(self):
        self.window.show()
        sys.exit(self.exec_())


if __name__ == "__main__":
    Blain().run()