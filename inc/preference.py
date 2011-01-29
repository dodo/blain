
from os.path import join as pathjoin

from PyQt4.uic import loadUi
from PyQt4.Qt import QSettings, QDialog, QIcon, QPixmap, QDialogButtonBox,\
                     QColor, QColorDialog, QEvent

from inc.ascii import get_logo
from inc.parse import drug


class PreferencesDialog(QDialog):

    def __init__(self, app, *args):
        QDialog.__init__(self, *args)
        self.app = app
        self.row = -1
        loadUi(pathjoin(app.cwd, "gui", "preferences.ui"), self)
        self.darkradioButton.setIcon(QIcon(QPixmap(get_logo())))
        self.lightradioButton.setIcon(QIcon(QPixmap(get_logo(dark=False))))
        self.filterList.currentRowChanged.connect(self.previousRow)
        self.filterList.installEventFilter(self)

    def closeEvent(self, event):
        self.hide()
        event.ignore()

    def hideEvent(self, event):
        self.app.window.enable()

    def eventFilter(self, sender, event):
        # only possibility to get an event on internalmove from qlistwidget
        if event.type() == QEvent.ChildRemoved:
            cur = self.filterList.currentRow()
            self.app.filters.move(self.row, cur)
            self.row = cur
        return False # no interput

    def previousRow(self, row):
        self.row = row



class Preferencer:

    def __init__(self, app):
        self.app = app
        self.settings = QSettings("blain", "blain")
        self.ui = PreferencesDialog(app)


    def connect(self):
        ui, ft = self.ui, self.app.filters
        self.app.window.ui.actionPreferences.triggered.connect(self.show)
        #connect preference window
        ui.fgcolorButton.clicked.connect(self.change_fgcolor)
        ui.bgcolorButton.clicked.connect(self.change_bgcolor)
        ui.resetcolorButton.clicked.connect(self.reset_color)
        ui.buttonBox.accepted.connect(self.accept)
        ui.buttonBox.rejected.connect(self.reject)
        ui.buttonBox.button(QDialogButtonBox.Apply).clicked.connect(self.save)
        ui.listWidget.currentRowChanged.connect(
            ui.stackedWidget.setCurrentIndex)


    def setup(self):
        self.load()


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
        st.setValue("color/messages/fg", self.fgcolor.name())
        st.setValue("color/messages/bg", self.bgcolor.name())
        self.app.notifier.saveRadioButtons()
        self.app.icons.update_window_icon()
        self.app.icons.update_tray()
        if self.fgcolor != self.old.fgcolor or self.bgcolor != self.old.bgcolor:
            self.old = drug(fgcolor = self.fgcolor, bgcolor = self.bgcolor)
            self.app.reader.update_messages_colors()


    def load(self):
        st, ui = self.settings, self.ui
        self.fgcolor = QColor(st.value("color/messages/fg",
            self.app.palette().buttonText().color().name()).toString())
        self.bgcolor = QColor(st.value("color/messages/bg",
            self.app.palette().button().color().name()).toString())
        self.old = drug(fgcolor = self.fgcolor, bgcolor = self.bgcolor)

        ui.identicaidEdit.setText(st.value("account/identica/id").toString())
        ui.twitteridEdit.setText(st.value("account/twitter/id").toString())
        b = st.value("icon/isdark",True).toBool()
        ui.darkradioButton.setChecked(b)
        ui.lightradioButton.setChecked(not b)
        ui.fgcolorButton.setStyleSheet("background-color:"+self.fgcolor.name())
        ui.bgcolorButton.setStyleSheet("background-color:"+self.bgcolor.name())
        if self.app.notifier.buttons:
            self.app.notifier.resetRadioButtons()


    def change_fgcolor(self):
        self.change_color('fgcolor')


    def change_bgcolor(self):
        self.change_color('bgcolor')


    def change_color(self, color_name):
        if not hasattr(self, color_name): return
        color = getattr(self, color_name)
        color = QColorDialog.getColor(color, self.ui)
        setattr(self, color_name, color)
        getattr(self.ui, color_name+"Button").setStyleSheet(
            "background-color:" + color.name())


    def reset_color(self):
        app, ui = self.app, self.ui
        self.fgcolor = app.palette().buttonText().color()
        self.bgcolor = app.palette().button().color()
        ui.fgcolorButton.setStyleSheet("background-color:"+self.fgcolor.name())
        ui.bgcolorButton.setStyleSheet("background-color:"+self.bgcolor.name())


