#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from signal import signal, SIGINT, SIG_DFL
from locale import setlocale, LC_ALL
from os.path import dirname, realpath

from PyQt4.Qt import QApplication, pyqtSignal

from inc.main import Window
from inc.database import Databaser
from inc.preference import Preferencer
from inc.update import Updater
from inc.icons import Iconer
from inc.filters import Filterer
from inc.thread import Threader
from inc.reader import Reader

signal(SIGINT, SIG_DFL)
setlocale(LC_ALL, ('en','utf_8'))


print """TODO:
 - using models for treeview and filterlist
 - showing merged service icon for merged posts
 #- better treeview update (only insert new posts) (timer triggered?)
 - loading groups from identica
 - do smth with twitter lists (dont know what this is .. but .. i will do science on it!)
 - notifications
 - logins
 - show conversations for replied posts (posts with reply==None but in a reply by an other post)
 - interner favoriten speicher um posts als später lesen zu markieren
 - update highlighting of all entries in list for posts with the same id
 - mark reposts (redents/retweets) and/or group them [marking done] (grouping by filter)
 - pages for posts
 - grouping filters and let the user switch between them
   (for exmaple important posters filter group)
"""



class Blain(QApplication):

    logStatus = pyqtSignal(str)
    killThread = pyqtSignal(str)
    addMessage = pyqtSignal(str, dict)
    updateUser = pyqtSignal(str, str)
    updateMicroblogging = pyqtSignal(str, str, bool)

    def __init__(self):
        print "loading ..."
        QApplication.__init__(self, sys.argv)

        self.cwd = dirname(realpath(__file__))
        self.window       =       Window(self)
        self.db           =    Databaser(self)
        self.filters      =     Filterer(self)
        self.preferences  =  Preferencer(self)
        self.updates      =      Updater(self)
        self.icons        =       Iconer(self)
        self.threads      =     Threader(self)
        self.reader       =       Reader(self)

        controllers = [self.window, self.db,  self.filters,
                       self.preferences, self.updates,
                       self.icons, self.threads, self.reader]

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
