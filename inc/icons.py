

from PyQt4.Qt import QSettings, QIcon, QPixmap, QImage, QSystemTrayIcon, QColor

from inc.get_favicon import get_favicon
from inc.parse import patchStyleSheet, parse_image
from inc.ascii import get_logo


class Iconer:

    def __init__(self, app):
        if not hasattr(app, 'preferences'):
            print("icons: need 'preferences' from app.")
            exit(1)
        if not hasattr(app, 'db'):
            print("icons: need 'db' from app.")
            exit(1)
        self.app = app
        self.icons = {}
        self.avatar_cache = {}
        self.avatar_mask = None
        self.avatars = QSettings("blain", "avatars")


    def connect(self):
        self.icons['tray'].activated.connect(self.app.window.clickTray)


    def setup(self):
        st = self.app.preferences.settings
        self.icons['identica'] = self.get_service_icon(
            0, "identica", "http://identi.ca")
        self.icons['twitter']  = self.get_service_icon(
            1, "twitter", "http://twitter.com")
        if not st.contains("icon/dark"):
            st.setValue("icon/dark", True)
        self.update_window_icon()
        self.update_tray()


    def get_service_icon(self, id, name, url):
        icon, st = None, self.app.preferences.settings
        if not st.contains('icon/'+name):
            icon = get_favicon(url)
            if icon:
                icon = QIcon(QPixmap.fromImage(QImage.fromData(icon)))
                print name, "icon loaded?", not icon.isNull()
                if not icon.isNull():
                    st.setValue('icon/'+name, icon)
            else: print "error while loading", name, "icon"
        else:
            icon = st.value('icon/'+name, None)
            if icon: icon = QIcon(icon)
        if icon:
            self.app.preferences.ui.accountsTabWidget.setTabIcon(id, icon)
        return icon


    def update_window_icon(self):
        st = self.app.preferences.settings
        self.app.window.ui.setWindowIcon(QIcon(QPixmap(
            get_logo(dark=st.value("icon/isdark").toBool()))))


    def update_tray(self):
        st = self.app.preferences.settings
        ai = self.icons['app'] = QIcon(QPixmap(
            get_logo(self.app.db.get_unread_count(),
            dark=st.value("icon/isdark").toBool())))
        if 'tray' in self.icons:
            self.icons['tray'].setIcon(ai)
        else:
            self.icons['tray'] = QSystemTrayIcon(ai, self.app)
            self.icons['tray'].show()


    def do_mask_on_(self, msg):
        # set mask for given msg
        if self.avatar_mask is None:
            msg.avatarLabel.setStyleSheet(patchStyleSheet(
                msg.avatarLabel.styleSheet(),
                **{'background-color':"black", 'color':"black"}))
            msg.avatarContainer.setStyleSheet(patchStyleSheet(
                msg.avatarContainer.styleSheet(),
                **{'background-color':"red", 'color':"red"}))
            self.avatar_mask = QPixmap.grabWidget(msg.avatarContainer).\
                createMaskFromColor(QColor("red"))
            msg.avatarContainer.setStyleSheet(patchStyleSheet(
                msg.avatarContainer.styleSheet(),
                **{'background-color':None, 'color':None}))
        msg.avatarLabel.setMask(self.avatar_mask)


    def do_service_icon_on_(self, msg, service):
        if service in self.icons:
            msg.serviceLabel.setPixmap(self.icons[service].pixmap(16,16))


    def do_avatar_on_(self, msg, imageinfo):
        image = parse_image(*([self] + imageinfo))
        if image[0]:
            msg.avatarLabel.setPixmap(image[0])
            self.avatar_cache[image[1]] = msg.avatarLabel




