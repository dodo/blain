

from PyQt4.Qt import QSettings, QIcon, QPixmap, QImage, Qt,\
                     QSystemTrayIcon, QColor, QRectF, QPainter

from inc.get_favicon import get_favicon
from inc.parse import patchStyleSheet, parse_image
from inc.ascii import get_logo


def magnify_icons(a, b):
    a = a.pixmap(16,16)
    b = b.pixmap(16,16)
    img = [QPixmap(16,16), QPixmap(16,16)]
    for i in img:
        i.fill(QColor(0, 0, 0, 0))
        g = a.toImage()
        for n in range(256):
            x, y = n%16, n//16
            c = QColor(g.pixel(x, y))
            s = (c.redF() + c.greenF() + c.blueF()) / 3.0
            l = s * 4.2
            if l > 1.0: l = 1.0
            c.setRgbF(s, s, s, l)
            g.setPixel(x, y, c.rgba())
        p = QPainter()
        p.begin(i)
        p.drawImage( QRectF(6, 0,  8, 16), g, QRectF(0, 0, 10, 16))
        p.drawPixmap(QRectF(0, 0, 10, 16), b, QRectF(6, 1,  10, 15))
        p.end()
        a, b = b, a
    return tuple(map(QIcon, img))


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
        if not st.contains("icon/dark"):
            st.setValue("icon/dark", True)
        self.update_window_icon()
        #self.update_tray() # by reader


    def get_service_icon(self, name, url):
        key = "service/" + name
        if key in self.icons:
            return self.icons[key]
        icon, st = None, self.app.accounts.settings
        if not st.contains('icon/'+name):
            icon = get_favicon(url)
            if icon:
                icon = QIcon(QPixmap.fromImage(QImage.fromData(icon)))
                #print name, "icon loaded?", not icon.isNull()
                if not icon.isNull():
                    st.setValue('icon/'+name, icon)
            else: print "[ERROR] while loading", name, "icon"
        else:
            icon = st.value('icon/'+name, None)
            if icon: icon = QIcon(icon)
        if icon:
            self.icons[key] = icon
        return icon


    def update_window_icon(self):
        st = self.app.preferences.settings
        self.app.window.ui.setWindowIcon(QIcon(QPixmap(
            get_logo(dark=st.value("icon/isdark", True).toBool()))))


    def update_tray(self, count = None):
        st = self.app.preferences.settings
        ai = self.icons['app'] = QIcon(QPixmap(
            get_logo(count or self.app.db.get_unread_count(),
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
        services = self.app.accounts.get_services(service)
        if len(services) == 0:
            return # no service found - skip
        elif len(services) == 1:
            icon = self.icons["service/" + services[0]]
        else:
            key = "service/" + "".join(services[:2])
            if key in self.icons:
                icon = self.icons[key]
            else:
                a = self.icons["service/" + services[0]]
                b = self.icons["service/" + services[1]]
                img = magnify_icons(a, b)
                self.icons["service/"+"".join(reversed(services[:2]))] = img[0]
                icon = self.icons[key] = img[1]
        if icon:
            msg.serviceLabel.setPixmap(icon.pixmap(16,16))


    def do_avatar_on_(self, msg, imageinfo):
        image = parse_image(*([self] + imageinfo['author']))
        if image[0]:
            msg.avatarLabel.setPixmap(image[0])
            self.avatar_cache[image[1]] = msg.avatarLabel
        if 'user' in imageinfo:
            image = parse_image(*([self] + imageinfo['user']))
            if image[0]:
                rl = msg.repeatLabel
                rl.setPixmap(QPixmap(image[0]).scaled(rl.width(),rl.height(),
                    Qt.KeepAspectRatio, Qt.SmoothTransformation))




