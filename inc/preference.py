
from os.path import join as pathjoin

from PyQt4.uic import loadUi
from PyQt4.Qt import QSettings, QDialog, QIcon, QPixmap, QDialogButtonBox

from inc.ascii import get_logo



class PreferencesDialog(QDialog):

    def __init__(self, app, *args):
        QDialog.__init__(self, *args)
        self.app = app
        loadUi(pathjoin(app.cwd, "gui", "preferences.ui"), self)
        self.darkradioButton.setIcon(QIcon(QPixmap(get_logo())))
        self.lightradioButton.setIcon(QIcon(QPixmap(get_logo(dark=False))))


    def closeEvent(self, event):
        self.hide()
        self.app.window.enable()
        event.ignore()



class Preferencer:

    def __init__(self, app):
        if not hasattr(app, 'filters'):
            print("preferences: need 'filters' from app.")
            exit(1)
        self.app = app
        self.settings = QSettings("blain", "blain")
        self.ui = PreferencesDialog(app)


    def connect(self):
        ui, ft = self.ui, self.app.filters
        self.app.window.ui.actionPreferences.triggered.connect(self.show)
        # connect filters
        ui.filtersComboBox.currentIndexChanged.connect(ft.changeDescription)
        ui.filtersComboBox_new.currentIndexChanged.connect(ft.changeNew)
        ui.addfilterButton.clicked.connect(ft.install)
        ui.updatefilterButton.clicked.connect(lambda: ft.update())
        ui.removefilterButton.clicked.connect(ft.remove)
        #connect preference window
        ui.buttonBox.accepted.connect(self.accept)
        ui.buttonBox.rejected.connect(self.reject)
        ui.buttonBox.button(QDialogButtonBox.Apply).clicked.connect(self.save)
        ui.listWidget.currentRowChanged.connect(
            ui.stackedWidget.setCurrentIndex)


    def setup(self):
        self.load()
        self.app.filters.changeNew(0)
        self.app.filters.changeDescription(0)


    def show(self, _):
        self.app.window.disable()
        self.ui.show()


    def hide(self):
        self.ui.hide()
        self.app.window.enable()


    def reject(self):
        self.hide()
        self.load()


    def accept(self):
        self.hide()
        self.save()


    def save(self):
        app, st, ui = self.app, self.settings, self.ui
        st.setValue("account/twitter/id", ui.twitteridEdit.text())
        st.setValue("account/identica/id", ui.identicaidEdit.text())
        st.setValue("icon/isdark", ui.darkradioButton.isChecked())
        self.app.icons.loadWindow()


    def load(self):
        st, ui = self.settings, self.ui
        ui.identicaidEdit.setText(st.value("account/identica/id").toString())
        ui.twitteridEdit.setText(st.value("account/twitter/id").toString())
        b = st.value("icon/isdark",True).toBool()
        ui.darkradioButton.setChecked(b)
        ui.lightradioButton.setChecked(not b)




