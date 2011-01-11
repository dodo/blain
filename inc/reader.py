

from inc.parse import patchStyleSheet

class Reader:

    def __init__(self, app):
        if not hasattr(app, 'window'):
            print("reader: need 'window' from app.")
            exit(1)
        if not hasattr(app, 'icons'):
            print("reader: need 'icons' from app.")
            exit(1)
        self.app = app


    def connect(self):
        win = self.app.window.ui
        win.actionUndo_mark.triggered.connect(self.mark_all_as_unread)
        win.messageTable.itemSelectionChanged.connect(self.mark_as_read)
        win.actionMark_all_as_read.triggered.connect(self.mark_all_as_read)


    def setup(self):
        self.updateMenuButton()
        self.update()


    def update(self):
        app = self.app
        count = app.db.get_unread_count()
        app.icons.update_tray(count)
        app.window.ui.actionMark_all_as_read.setEnabled(count is not None)


    def updateMenuButton(self):
        action = self.app.window.ui.actionUndo_mark
        count = self.app.db.get_unread_marked_count()
        if count is None:
            action.setEnabled(False)
            action.setText("no posts to reset")
            return
        action.setEnabled(True)
        action.setText("reset {0} posts as unread".format(count))


    def mark_as_read(self):
        mt = self.app.window.ui.messageTable
        msg = mt.itemWidget(mt.currentItem(), 0)
        if "color" in msg.messageLabel.styleSheet():
            id = int(msg.id.text())
            self.app.window.update_messages_stylesheet(
                {'background-color':None, 'color':None}, [id])
            self.app.db.set_unread_status(id, False)
            self.update()


    def update_messages_colors(self):
        app, pref = self.app, self.app.preferences
        ids = list(map(lambda p: p.pid, app.db.get_cached_unread()))
        app.window.update_messages_stylesheet(
            {'background-color':pref.bgcolor.name(),
             'color':pref.fgcolor.name()}, ids)


    def mark_all_as_read(self):
        self.app.window.update_messages_stylesheet(
            {'background-color':None, 'color':None})
        self.app.db.set_all_unread_status(False)
        self.updateMenuButton()
        self.update()


    def mark_all_as_unread(self): # reset
        self.app.db.reset_all_unread_status(True)
        self.update_messages_colors()
        self.updateMenuButton()
        self.update()

