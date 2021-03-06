#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from signal import signal, SIGINT, SIG_DFL
from os.path import dirname, realpath

from PyQt4.Qt import QApplication, pyqtSignal

from inc.main import Window
from inc.database import Databaser
from inc.preference import Preferencer
from inc.accounts import Accounter
from inc.update import Updater
from inc.icons import Iconer
from inc.filters import Filterer
from inc.thread import Threader
from inc.reader import Reader
from inc.notification import Notifier

signal(SIGINT, SIG_DFL)


print """TODO:
 - using models for treeview and filterlist
 #- better treeview update (only insert new posts) (timer triggered?)
 - do smth with twitter lists (dont know what this is .. but .. i will do science on it!)
 - logins
 - show conversations for replied posts (posts with reply==None but in a reply by an other post)
 - interner favoriten speicher um posts als später lesen zu markieren
 - pages for posts
 - grouping filters and let the user switch between them
   (for exmaple important posters filter group)
"""



class Blain(QApplication):

    logStatus = pyqtSignal(str)
    killThread = pyqtSignal(str)
    addMessage = pyqtSignal(dict)
    updateUser = pyqtSignal(str, str, str)
    updateGroup = pyqtSignal(str, str, str)
    updateGroups = pyqtSignal(str, str, bool)
    updateFriends = pyqtSignal(str, str, bool)

    def __init__(self):
        print "loading ..."
        QApplication.__init__(self, sys.argv)

        self.cwd = dirname(realpath(__file__))
        self.window       =       Window(self)
        self.db           =    Databaser(self)
        self.preferences  =  Preferencer(self)
        self.filters      =     Filterer(self)
        self.icons        =       Iconer(self)
        self.accounts     =    Accounter(self)
        self.updates      =      Updater(self)
        self.threads      =     Threader(self)
        self.reader       =       Reader(self)
        self.notifier     =     Notifier(self)

        controllers = [self.window, self.db, self.preferences,
                       self.filters, self.accounts, self.updates,
                       self.icons, self.threads, self.reader,
                       self.notifier]

        for controller in controllers:
            controller.setup()
        # need to be seperated
        for controller in controllers:
            controller.connect()


    def updateMessageView(self, maxcount = 0):
        self.window.updateMessageView(maxcount)


    def run(self):
        win = self.window.ui
        win.show()
        win.update()
        win.repaint()
        self.updateMessageView(42)
        win.statusBar.showMessage("Ready ...", 3000)
        print "done."
        sys.exit(self.exec_())


if __name__ == "__main__":
    Blain().run()
