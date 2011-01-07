

from PyQt4.Qt import QMessageBox

from inc.parse import patchStyleSheet

class Reader:

    def __init__(self, app):
        if not hasattr(app, 'window'):
            print("reader: need 'window' from app.")
            exit(1)
        self.app = app


    def connect(self):
        win = self.app.window.ui
        win.messageTable.itemSelectionChanged.connect(self.mark_as_read)
        win.actionMark_all_as_read.triggered.connect(self.mark_all_as_read)


    def setup(self):
        pass


    def update(self):
        self.app.icons.loadWindow()


    def mark_as_read(self):
        mt = self.app.window.ui.messageTable
        msg = mt.itemWidget(mt.currentItem(), 0)
        if "color" in msg.messageLabel.styleSheet():
            self.app.db.set_unread_status(int(msg.id.text()), False)
            msg.messageLabel.setStyleSheet(patchStyleSheet(
                msg.messageLabel.styleSheet(),
                **{'background-color':None, 'color':None}))
            self.update()


    def mark_all_as_read(self):
        msg = QMessageBox(self.app.window.ui)
        msg.setIcon(QMessageBox.Question)
        msg.setWindowTitle("Mark all as read ...")
        msg.setText("Are you sure you want all posts marked as read?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        if msg.exec_() == QMessageBox.Yes:
            self.app.window.update_messages_as_read()
            self.app.db.set_all_unread_status(False)
            self.update()


