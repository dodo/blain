# -*- coding: utf-8 -*-

import sys

from PyQt4 import QtCore, QtGui, uic




if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    win = uic.loadUi("qt.ui")
    win.show()
    sys.exit(app.exec_())