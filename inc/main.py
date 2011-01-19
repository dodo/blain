
from os.path import join as pathjoin
from datetime import datetime

from PyQt4.uic import loadUi, loadUiType
from PyQt4.Qt import Qt, QSystemTrayIcon, QTreeWidgetItem, QPalette

from inc.parse import patchStyleSheet, prepare_post



class UiLoader:

    def __init__(self, filename):
        self.Form, self.Base = loadUiType(filename)

    def new(self):
        Base, Form = self.Base, self.Form

        form = Form()
        base = Base()
        oldkeys = form.__dict__.keys()
        form.setupUi(base)
        newkeys = form.__dict__.keys()
        for key in oldkeys:
            newkeys.remove(key)
        for key in newkeys:
            setattr(base, key, getattr(form, key))
        return base



class Window:

    def __init__(self, app):
        self.app = app
        self.ui = loadUi(pathjoin(app.cwd, "gui", "window.ui"))
        self.Message = UiLoader(pathjoin(app.cwd, "gui", "message.ui"))


    def connect(self):
        app, ui = self.app, self.ui
        ui.sendButton.clicked.connect(self.sendMessage)
        ui.messageEdit.returnPressed.connect(self.sendMessage)
        ui.messageEdit.textChanged.connect(self.sendButtonController)
        ui.actionMinimize.triggered.connect(ui.hide)
        ui.actionQuit.triggered.connect(self.app.quit)
        ui.actionUpdate_view.triggered.connect(self.updateMessageView)
        ui.messageTable.itemDoubleClicked.connect(self.showConversation)
        app.logStatus.connect(self.logStatus)


    def setup(self):
        mt = self.ui.messageTable
        mt.sortItems(1, Qt.DescendingOrder)
        mt.hideColumn(1)


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
            self.app.addMessage.emit( "twitter", ####
                {'time':datetime.now(),'text':txt,'info':"test"})
            self.ui.messageEdit.setText("")
            self.app.updateMessageView() ####


    def sendButtonController(self, text):
        self.ui.sendButton.setEnabled( text != "" )


    def test(self):
        #from inc.update import get_friends, get_user
        #from pprint import pprint
        #pprint(get_friends('twitter', 'dodothelast'))
        #pprint(get_friends('identica', 'dodothelast'))
        #pprint(get_user('twitter', 'dodothelast'))
        #pprint(get_user('identica', 'dodothelast'))
        self.app.notifier.notify("This is a great Test Message!!1!")
        print "done."


    def update_messages_stylesheet(self, properties, ids = None):
        mt = self.ui.messageTable
        def work(item):
            msg = mt.itemWidget(item, 0)
            if ids is not None and int(msg.id.text()) not in ids:
                return # skip it
            msg.messageLabel.setStyleSheet(patchStyleSheet(
                msg.messageLabel.styleSheet(), **properties))
        for i in range(mt.topLevelItemCount()):
            item = mt.topLevelItem(i)
            work(item)
            for j in range(item.childCount()):
                work(item.child(j))


    def showConversation(self, item, _):
        mt = self.ui.messageTable
        msg = mt.itemWidget(item, 0)
        if item.isExpanded():
            msg.replyLabel.setVisible(True)
            return # allready added
        if not msg.replyLabel.isVisible():
            return # no conversation
        msg.replyLabel.setVisible(False)
        if item.childCount(): return # allready added
        messages = self.app.db.get_conversation_messages(int(msg.id.text()))
        for _blob in messages:
            blob = prepare_post(_blob.__dict__)
            msg, time = self.build_message_item(blob)
            msg.replyLabel.setVisible(False) # no conversation trees possible
            i = QTreeWidgetItem(item)
            i.setText(1, time)
            mt.setItemWidget(i, 0, msg)


    def logStatus(self, msg, time=5000):
        print msg
        self.ui.statusBar.showMessage(msg, time)
        self.ui.statusBar.update()


    def updateMessageView(self, maxcount = 0):
        maxcount = maxcount or 200
        mt = self.ui.messageTable
        items = [ (n, str(i.text(1)), mt.itemWidget(i, 0), i)
                  for n, i in enumerate(map(lambda n:mt.topLevelItem(n),
                              range(mt.topLevelItemCount()))) ]
        pids = [ str(item[2].id.text()) for item in items ]
        olditems = list(items)
        olds = list(pids)
        n = 0
        self.app.icons.avatar_cache = {}
        messages = self.app.db.get_messages_from_cache(maxcount)
        print "* update message view", len(messages)
        for _blob in messages:
            blob = prepare_post(_blob.__dict__)
            if str(blob.pid) in olds:
                i = olds.index(str(blob.pid))
                olditems.pop(i)
                olds.pop(i)
            if str(blob.pid) not in pids:
                pids.append(blob.pid)
                msg, time = self.build_message_item(blob)
                i = QTreeWidgetItem(mt)
                i.setText(1, time)
                mt.setItemWidget(i, 0, msg)
        # now remove the too old ones
        items.sort(key=lambda i:i[1])
        for old in list(reversed(items))[maxcount-1:] + olditems:
            mt.removeItemWidget(old[3], 0)
            item = old[2]
            del item


    def build_message_item(self, blob):
        pref = self.app.preferences
        msg = self.Message.new()
        msg.id.setVisible(False)
        if blob.reply is None:
            msg.replyLabel.setVisible(False)
        msg.id.setText(str(blob.pid))
        pal = self.app.palette()
        msg.messageLabel.setText(
            "<style>a {text-decoration:none}</style>" + blob.text)
        msg.infoLabel.setText("<style>a {text-decoration:none;color:" +
            pal.dark().color().name() + "}</style>" + blob.info)
        msg.infoLabel.setStyleSheet(patchStyleSheet(
            msg.infoLabel.styleSheet(), color = pal.mid().color().name()))
        for label, fg, bg in [(msg.repeatLabel,
                       pal.highlightedText().color().name(),
                       pal.highlight().color().name()),
                      (msg.replyLabel,
                       pal.window().color().name(),
                       pal.mid().color().name())]:
            x = label.minimumSizeHint().height()
            label.setMinimumSize(x, x)
            label.setMaximumSize(x, x)
            label.setStyleSheet(patchStyleSheet(
                label.styleSheet(), **{'background-color':bg, 'color':fg}))
        if blob.unread:
            msg.messageLabel.setStyleSheet(patchStyleSheet(
                msg.messageLabel.styleSheet(),
                **{'background-color':pref.bgcolor.name(),
                   'color':pref.fgcolor.name()}))
        self.app.icons.do_mask_on_(msg)
        msg.avatarLabel.setStyleSheet(patchStyleSheet(
            msg.avatarLabel.styleSheet(),
            **{'background-color':blob.author_bgcolor,
               'color':blob.author_fgcolor}))
        self.app.icons.do_service_icon_on_(msg, blob.service)
        if blob.author_id == blob.user_id:
            msg.repeatLabel.setVisible(False)
        else:
            style = {'background-color':blob.user_bgcolor,
                     'color':blob.user_fgcolor}
            if 'imageinfo' in blob.__dict__ and 'user' in blob.imageinfo:
                style['border-radius'] = "0em"
            msg.repeatLabel.setStyleSheet(patchStyleSheet(
                msg.repeatLabel.styleSheet(), **style))
        if 'imageinfo' in blob.__dict__:
            self.app.icons.do_avatar_on_(msg, blob.imageinfo)
        return msg, blob.time.strftime("%Y-%m-%d %H:%M:%S")

