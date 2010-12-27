
from os.path import join as pathjoin
from datetime import datetime

from PyQt4.uic import loadUi
from PyQt4.Qt import QSystemTrayIcon, QTreeWidgetItem

from inc.parse import patchStyleSheet, prepare_post


class Window:

    def __init__(self, app):
        self.app = app
        self.ui = loadUi(pathjoin(app.cwd, "window.ui"))


    def connect(self):
        app, ui = self.app, self.ui
        ui.sendButton.clicked.connect(self.sendMessage)
        ui.messageEdit.returnPressed.connect(self.sendMessage)
        ui.messageEdit.textChanged.connect(self.sendButtonController)
        ui.actionMinimize.triggered.connect(ui.hide)
        ui.actionQuit.triggered.connect(self.app.quit)
        ui.actionSilence.triggered.connect(self.test)
        ui.actionUpdate_view.triggered.connect(self.updateMessageView)
        app.logStatus.connect(self.logStatus)


    def setup(self):
        self.ui.messageTable.hideColumn(0)


    def enable(self):
        self.ui.setEnabled(True)


    def disable(self):
        self.ui.setEnabled(False)


    def clickTray(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.ui.setVisible(not self.ui.isVisible())


    def sendMessage(self):
        # TODO send message instead of printing it
        txt = self.ui.messageEdit.text()
        if txt != "":
            self.app.addMessage.emit( ####
                {'time':datetime.now(),'text':txt,'info':"test"})
            self.ui.messageEdit.setText("")
            self.app.updateMessageView() ####


    def sendButtonController(self, text):
        self.ui.sendButton.setEnabled( text != "" )


    def test(self):
        from inc.update import get_friends, get_user
        from pprint import pprint
        #pprint(get_friends('twitter', 'dodothelast'))
        #pprint(get_friends('identica', 'dodothelast'))
        pprint(get_user('twitter', 'dodothelast'))
        pprint(get_user('identica', 'dodothelast'))
        print "done."


    def logStatus(self, msg, time=5000):
        print msg
        self.ui.statusBar.showMessage(msg, time)
        self.ui.statusBar.update()


    def updateMessageView(self, maxcount = 0):
        maxcount = maxcount or 200
        mt = self.ui.messageTable
        self.app.icons.avatar_cache = {}
        n = 0
        mt.clear()
        messages = self.app.db.get_messages_from_cache(maxcount)
        print "* update message view", len(messages)
        for _blob in messages:
            blob = prepare_post(_blob.__dict__)
            time = blob.time.strftime("%Y-%m-%d %H:%M:%S")
            msg = loadUi(pathjoin(self.app.cwd, "message.ui")) # TODO chache this
            msg.messageLabel.setText(blob.text)
            msg.infoLabel.setText(blob.info)
            self.app.icons.do_mask_on_(msg)
            msg.avatarLabel.setStyleSheet(patchStyleSheet(patchStyleSheet(
                msg.avatarLabel.styleSheet(),
                'background-color', blob.user_bgcolor),
                'color', blob.user_fgcolor))
            self.app.icons.do_service_icon_on_(msg, blob.service)

            if 'imageinfo' in blob.__dict__:
                self.app.icons.do_avatar_on_(msg, blob.imageinfo)
            i = QTreeWidgetItem(mt)
            i.setText(0, time)
            mt.setItemWidget(i, 1, msg)
            #n += 1
            #if not n%13:
                #mt.update()
                #mt.repaint()

