

from PyQt4.Qt import QSettings, QListWidgetItem, QLabel

from inc.parse import drug
from inc.microblogging import add_service

services = [
drug(name=None, url=None, type="statusnet", title="Statusnet"),
drug(name="identica",url="http://identi.ca",type="statusnet",title="Identi.ca"),
drug(name="twitter", url="http://twitter.com", type="twitter", title="Twitter")]


apis = {
    "statusnet": drug(
        api =    "{0}/api/",
        search = "{0}/api/search.json",
        ),
    "twitter": drug(
        api =    "http://api.twitter.com/1/",
        search = "http://search.twitter.com/search.json",
        ),
    }


class Account:

    def __init__(self, drug):
        api = apis[drug.type]
        self.groups = None
        self.api = api.api.format(drug.url)
        self.search = api.search.format(drug.url)
        self.url = u"{0}/".format(drug.url)
        self.service = drug.service
        self.name = drug.name
        self.type = drug.type
        self.friends = QSettings("blain", u"{0}-{1}-friends".\
            format(self.service, self.name))
        if self.type == "statusnet":
            self.groups = QSettings("blain", u"{0}-{1}-groups".\
                format(self.service, self.name))



class Accounter:

    def __init__(self, app):
        if not hasattr(app, 'preferences'):
            print("accounts: need 'preferences' from app.")
            exit(1)
        if not hasattr(app, 'icons'):
            print("accounts: need 'icons' from app.")
            exit(1)
        self.app = app
        self.urls = {}
        self.services = {}
        self.accounts = {}
        self._accounts = []
        self.settings = QSettings("blain", "accounts")


    def connect(self):
        ui = self.app.preferences.ui
        ui.addaccountButton.clicked.connect(self.addAccount)
        ui.removeaccountButton.clicked.connect(self.removeAccount)
        cb = ui.accountserviceComboBox
        cb.currentIndexChanged.connect(self.changeAccountservice)
        for service in services:
            cb.addItem(service.title)
        cb.setCurrentIndex(1)


    def setup(self):
        st = self.settings
        st.beginGroup("url")
        for service in map(unicode, st.allKeys()):
            self.urls[service] = unicode(st.value(service).toString())
        st.endGroup()
        st.beginGroup("service")
        for service in map(unicode, st.allKeys()):
            self.services[service] = unicode(st.value(service).toString())
        st.endGroup()
        st.beginGroup("account")
        for key in map(unicode, st.allKeys()):
            service = unicode(st.value(key).toString())
            self.accounts[key] = drug(
                service = service,
                name = key.partition("/")[2],
                type = self.services[service],
                url = self.urls[service])
        st.endGroup()
        for key, account in self.accounts.items():
            self._accounts.append(key)
            self.add_account_to_list(account)
            self.accounts[key] = account = Account(account)
            add_service(account.service,
                {'api':account.api, 'search':account.search})


    def add_account_to_list(self, account):
        at = self.app.preferences.ui.accountList
        n = at.count()
        icon = self.app.icons.get_service_icon(account.service, account.url)
        li = QListWidgetItem( u"{0}   ({1})".format(
            account.name, account.service))
        if icon is not None:
            li.setIcon(icon)
        at.insertItem(n, li)
        at.setCurrentRow(n)


    def addAccount(self):
        pref = self.app.preferences.ui
        if pref.addaccountButton.text() == "wait":
            return # already adding an account
        if pref.accountidEdit.text() == "":
            return # is empty
        index = pref.accountserviceComboBox.currentIndex()
        if index == 0 and pref.accounturlEdit.text() == "":
            return # is empty too
        account = drug(service = services[index].name,
                       name = unicode(pref.accountidEdit.text()),
                       type = services[index].type,
                       url = services[index].url)
        if account.url is None:
            url = unicode(pref.accounturlEdit.text())
            if url.endswith("/"):
                url = url[:-1]
            if not "://" in url:
                url = u"http://" + url
            account.url = url
        if account.service is None:
            s = account.url.partition("//")[2].partition("/")[0].split(".")
            account.service = s[-2] + s[-1]
        # save new account
        pref.addaccountButton.setText("wait")
        st = self.settings
        key = u"account/{0}/{1}".format(account.service, account.name)
        if st.contains(key):
            return # allready existing -> skip
        st.setValue(key, account.service)
        key = u"service/" + account.service
        if not st.contains(key):
            st.setValue(key, account.type)
            st.setValue(u"url/" + account.service, account.url)
            self.urls[account.service] = account.url
        pref.accountsTabWidget.setCurrentIndex(0)
        self.add_account_to_list(account)
        key = u"{0}/{1}".format(account.service, account.name)
        self._accounts.append(key)
        self.accounts[key] = account = Account(account)
        # create timer events for new account
        self.app.updates.add_timer("friends", account.service, account.name, "")
        self.app.updates.add_timer(
            "user", account.service, account.name, account.name)
        if account.groups is not None:
            self.app.updates.add_timer("groups",account.service,account.name,"")
        # install service
        if account.service not in self.services:
            self.services[account.service] = account.type
            add_service(account.service,
                {'api':account.api, 'search':account.search})
        pref.addaccountButton.setText("add")


    def removeAccount(self):
        at = self.app.preferences.ui.accountList
        n = at.currentRow()
        if n == -1:
            return # no items
        acc = self._accounts.pop(n)
        self.settings.remove(u"account/" + acc)
        account = self.accounts[acc]
        self.app.updates.remove_timer("friends",account.service,account.name,"")
        self.app.updates.remove_timer("user"   ,account.service,account.name,"")
        self.app.updates.remove_timer("groups" ,account.service,account.name,"")
        self.app.updates.remove_timer("group"  ,account.service,account.name,"")
        del self.accounts[acc]
        at.takeItem(n)


    def changeAccountservice(self, index):
        ui = self.app.preferences.ui
        if index in range(len(services)):
            visible = services[index].url is None
            ui.accounturlLabel.setVisible(visible)
            ui.accounturlEdit.setVisible(visible)


    def get_services(self, services): # returning merged services as list
        active,merged,services = self.get_active_services(),unicode(services),[]
        while merged:
            matched = []
            for service in active:
                if service in merged:
                    i = merged.index(service)
                    matched.append((i, service))
            if not matched: break
            matched.sort(key=lambda x:x[0])
            service = matched[0][1]
            services.append(service)
            merged = merged[len(service):]
        # prefer statusnet
        services.sort(key=lambda s:self.services[s] == "twitter" * 1)
        return services


    def get_active_services(self):
        return list(set(account.service for account in self.accounts.values()))


    def get(self, service = None, user = None):
        if service is None and user is None:
            return self.accounts.values()
        return self.accounts[u"{0}/{1}".format(service, user)]



