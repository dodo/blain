#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from os.path import dirname, realpath, join as pathjoin
from datetime import datetime

from PyQt4 import uic, Qt as qt

import update
import filters
from db import Database
from ascii import get_logo
from models import setup_models
from update import MicroblogThread, UserStatusThread
from getFavicon import get_favicon
from parsing import drug, parse_image, prepare_post

print """TODO:
 - using models for treeview and filterlist
 - showing merged service icon for merged posts
 #- better treeview update (only insert new posts) (timer triggered?)
 - loading groups from identica
 - do smth with twitter lists (dont know what this is .. but .. i will do science on it!)
 - notifications
 - logins
 - highlight unread posts and show number in logo
 - mark reposts (redents/retweets) and/or group them
 - stack conversations together and show them as branch in treeview
 - pages for posts
 - clean up code
 - clean up folder
 - grouping filters and let the user switch between them
   (for exmaple important posters filter group)
"""


def patchStyleSheet(stylesheet, key, value):
    stylesheet = str(stylesheet)
    lines = stylesheet.replace("\n","").split(";")
    if value is None:
        if key in stylesheet:
            for i, line in enumerate(lines):
                if line.strip().startswith(key):
                    lines = lines[:i] + lines[i+1:]
                    break
    else:
        if key not in stylesheet:
            lines.append( "%s: %s" % (key, value) )
        else:
            for i, line in enumerate(lines):
                if line.strip().startswith(key):
                    lines[i] = "{0}{3}: {4}{2}".\
                        format(*(line.partition(line.strip()) + (key, value)))
                    break
    return ";\n".join(lines)


class Slots:
    def __init__(self, app):
        self.app = app
        self.threads = {}

    def connect(self):
        win = self.app.window
        win.actionDoUpdates.setChecked(
            self.app.settings.value("timer/active",True).toBool())
        win.sendButton.clicked.connect(self.sendMessage)
        win.messageEdit.returnPressed.connect(self.sendMessage)
        win.messageEdit.textChanged.connect(self.sendButtonController)
        win.actionDoUpdates.triggered.connect(self.doUpdates)
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
            self.app.updateMessageView()

    def sendButtonController(self, text):
        self.app.window.sendButton.setEnabled( text != "" )

    def showPref(self, _):
        self.app.window.setEnabled(False)
        self.app.preferences.show()

    def hidePref(self):
        self.app.preferences.hide()
        self.app.window.setEnabled(True)

    def updateMicroblogging(self, service, user, updateusers=True):
        service, user = str(service), unicode(user)
        if service in self.threads and self.threads[service].isRunning():
            print "update %s already running" % service
            return
        self.threads[service]=MicroblogThread(self.app,user,service,updateusers)
        self.threads[service].start()

    def updateTwitter(self):
        self.updateMicroblogging('twitter',
            self.app.preferences.twitteridEdit.text())

    def updateIdentica(self):
        self.updateMicroblogging('identica',
            self.app.preferences.identicaidEdit.text())


    def doUpdates(self, checked):
        if checked: self.app.timer.start()
        else:       self.app.timer.stop()
        self.app.settings.setValue("timer/active", checked)

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
        uic.loadUi(pathjoin(app.cwd, "preferences.ui"), self)
        self.darkradioButton.setIcon(qt.QIcon(qt.QPixmap(get_logo())))
        self.lightradioButton.setIcon(qt.QIcon(qt.QPixmap(get_logo(dark=False))))

    def closeEvent(self, event):
        self.hide()
        self.app.window.setEnabled(True)
        event.ignore()



class Blain(qt.QApplication):

    logStatus = qt.pyqtSignal(str)
    killThread = qt.pyqtSignal(str)
    addMessage = qt.pyqtSignal(dict)
    updateUser = qt.pyqtSignal(str, str)
    updateMicroblogging = qt.pyqtSignal(str, str, bool)

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

        cwd = self.cwd = dirname(realpath(__file__))
        self.icons = {}
        self.threads = {}
        self.avatar_cache = {}
        self.avatar_mask = None
        self.threadwatcher = None
        self.logStatus.connect(self._logStatus)
        self.addMessage.connect(self._addMessage)
        self.killThread.connect(self._killThread)
        self.updateUser.connect(self._updateUser)

        self.window = uic.loadUi(pathjoin(cwd, "window.ui"))
        self.window.messageTable.hideColumn(0)
        self.preferences = PreferencesDialog(self)

        st = self.settings = qt.QSettings("blain", "blain")
        self.avatars = qt.QSettings("blain", "avatars")
        settingspath = dirname(str(st.fileName()))
        db = self.db = Database(location=pathjoin(settingspath, "blain.sqlite"))
        setup_models(db)

        self.filters = qt.QSettings("blain", "filters")
        filters.setup(self, settingspath)
        if st.contains("account/twitter/id") or \
           st.contains("account/identica/id"):
            update.setup(self)

        self.appIcon = qt.QIcon(qt.QPixmap(get_logo(dark=st.value("icon/isdark",True).toBool())))
        self.setWindowIcon(self.appIcon)
        self.trayIcon = qt.QSystemTrayIcon(self.appIcon, self)
        self.trayIcon.show()

        # load settings
        self.icons['identica'] = load_icon(0, "identica", "http://identi.ca")
        self.icons['twitter']  = load_icon(1, "twitter", "http://twitter.com")

        self.slots = Slots(self)
        self.slots.loadSettings()
        self.slots.connect()
        self.updateMicroblogging.connect(self.slots.updateMicroblogging)
        self.window.actionUpdate_view.triggered.connect(self.updateMessageView)

    def run(self):
        self.window.show()
        self.window.update()
        self.window.repaint()
        self.updateMessageView(42)
        self.window.statusBar.showMessage("Ready ...", 3000)
        print "done."
        sys.exit(self.exec_())

    def updateMessageView(self, maxcount = 0):
        maxcount = maxcount or 200
        mt = self.window.messageTable
        self.avatar_cache = {}
        n = 0
        mt.clear()
        Post, Cache = self.db.Post, self.db.Cache
        messages = Post.find().order_by(Post.time.desc()).\
            filter(Post.id.in_(self.db.session.query(Cache.pid))).\
            limit(maxcount).all()
        print "* update message view", len(messages)
        for _blob in messages:
            blob = prepare_post(_blob.__dict__)
            time = blob.time.strftime("%Y-%m-%d %H:%M:%S")
            msg = uic.loadUi(pathjoin(self.cwd, "message.ui")) # TODO chache this
            msg.messageLabel.setText(blob.text)
            msg.infoLabel.setText(blob.info)
            if self.avatar_mask is None:
                msg.avatarLabel.setStyleSheet(patchStyleSheet(
                    patchStyleSheet(msg.avatarLabel.styleSheet(),
                    'background-color', "black"), 'color', "black"))
                msg.avatarContainer.setStyleSheet(patchStyleSheet(
                    patchStyleSheet(msg.avatarContainer.styleSheet(),
                    'background-color', "red"), 'color', "red"))
                self.avatar_mask = qt.QPixmap.grabWidget(msg.avatarContainer).\
                    createMaskFromColor(qt.QColor("red"))
                msg.avatarContainer.setStyleSheet(patchStyleSheet(
                    patchStyleSheet(msg.avatarContainer.styleSheet(),
                    'background-color', None), 'color', None))
            msg.avatarLabel.setMask(self.avatar_mask)
            msg.avatarLabel.setStyleSheet(patchStyleSheet(patchStyleSheet(
                msg.avatarLabel.styleSheet(),
                'background-color', blob.user_bgcolor),
                'color', blob.user_fgcolor))
            if blob.service in self.icons:
                msg.serviceLabel.setPixmap(self.icons[blob.service].pixmap(16,16))
            if 'imageinfo' in blob.__dict__:
                image = parse_image(*([self]+blob.imageinfo))
                if image[0]:
                    msg.avatarLabel.setPixmap(image[0])
                    self.avatar_cache[image[1]] = msg.avatarLabel
            i = qt.QTreeWidgetItem(mt)
            i.setText(0, time)
            mt.setItemWidget(i, 1, msg)
            #n += 1
            #if not n%13:
                #mt.update()
                #mt.repaint()

    def _logStatus(self, msg, time=5000):
        print msg
        self.window.statusBar.showMessage(msg, time)
        self.window.statusBar.update()

    def _addMessage(self, blob):
        blob = dict([(str(k),blob[k]) for k in blob])
        for k in ['text','plain','source','service','user_id','user_url',
                  'user_name','user_fgcolor','user_bgcolor','user_profile_url',
                  'profile_image_url']:
            if blob[k]:
                blob[k] = unicode(blob[k])
        self.db.Post(**blob).add()

    def _killThread(self, id):
        id = str(id)
        if id in self.threads:
            del self.threads[id]
        print len(self.threads),"threads still running:  ",", ".join(self.threads.keys()),"-"*40
        self.db.session.commit()
        if not self.threads:
            filters.updateFilter(self, False)() # FIXME do incremental update
            self.updateMessageView(42)
        else:
            filters.updateFilter(self, False)() # FIXME do incremental update
            self.updateMessageView(10)

    def _updateUser(self, service, user):
        service, user = unicode(service), unicode(user)
        id = service + user
        if id in self.threads and self.threads[id].isRunning():
            print user, "thread still running. (%s)" % service
        else:
            Post = self.db.Post
            knownids = Post.find(Post.pid).order_by(Post.time.desc()).\
                filter_by(user_id = user).limit(2000).all()
            knownids = list(map(lambda i:i.pid, knownids))
            self.threads[id] = UserStatusThread(
                self, id, user, service, knownids)
            self.threads[id].start()



if __name__ == "__main__":
    Blain().run()