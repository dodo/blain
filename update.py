
from PyQt4.Qt import QThread


class MicroblogThread(QThread):

    def __init__(self, app, user, service, icon=None):
        QThread.__init__(self, app)
        self.app = app
        self.icon = icon
        self.user = user
        self.service = service

    def run(self):
        if self.user == "":
            self.app.logStatus.emit("Error: no user given! ("+self.service+")")
            self.quit()
        self.app.pager.update(self.service, self.user)
        updates =  self.app.pager.load_page(self.service, self.user)
        if not updates:
            self.app.logStatus.emit("Error: no results! ("+self.service+")")
            self.quit()
        self.app.logStatus.emit("Amount of updates:  %i" % len(updates))
        print
        for update in updates:
            update.icon = self.icon
            self.app.addMessage.emit(update.__dict__)
        print self.service + " done."
        self.quit()