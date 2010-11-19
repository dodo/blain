# -*- coding: utf-8 -*-

import sys

from PyQt4 import QtGui, uic

class Blain(QtGui.QApplication):
    def __init__(self):
        QtGui.QApplication.__init__(self, sys.argv)
        self.window = uic.loadUi("qt.ui")

    def run(self):
        self.window.show()
        sys.exit(self.exec_())


if __name__ == "__main__":
    Blain().run()