
import random
from os import listdir, mkdir, remove as fileremove
from imp import find_module, load_module
from shutil import copyfile
from os.path import dirname, exists, isdir, isfile, join as pathjoin
from traceback import format_exc

from PyQt4.Qt import QSettings, QTableWidgetItem, QMessageBox, Qt

from inc.parse import drug

random.seed()

def gen_hash():
    return "%016x" % random.getrandbits(64)


class Filterer:

    def __init__(self, app):
        if not hasattr(app, 'db'):
            print("filters: need 'db' from app.")
            exit(1)
        self.app = app
        self._filters = {}
        self._keys = []
        self._instances = ([], [])
        self.settings = QSettings("blain", "filters")


    def connect(self):
        pass # all gui in preferences


    def setup(self):
        app, st, pref = self.app, self.settings, self.app.preferences.ui
        settingspath = dirname(str(self.settings.fileName()))
        filterpath = pathjoin(settingspath, "filter")
        # copy default filters into user config
        if not exists(filterpath) or not isdir(filterpath):
            mkdir(filterpath)
        localfilterpath = pathjoin(app.cwd, "filter")
        for filename in listdir(localfilterpath):
            if isfile(pathjoin(localfilterpath, filename)) and \
                filename.endswith(".py") and \
                not exists(pathjoin(filterpath, filename)):
                copyfile(pathjoin(localfilterpath, filename),
                         pathjoin(     filterpath, filename))
        # read filters from directory
        for filename in listdir(filterpath):
            if isfile(pathjoin(filterpath, filename)) and filename.endswith(".py"):
                mname = filename[:-3]
                fp, pathname, desc = find_module(mname,[filterpath])
                try:
                    filter = load_module(mname, fp, pathname, desc)
                    filterinfo = fi = filter.info()
                    if not isinstance(filterinfo, dict) or  \
                    not ('id' in fi and 'name' in fi and \
                            'filter' in fi and 'install' in \
                            fi and 'config' in fi and       \
                            'filter_description' in fi and  \
                            'instance_description' in fi and\
                            isinstance(fi['config'], dict)):
                        print "[ERROR] filter '%s' not valid." % filename
                    else:
                        filterinfo = drug(**filterinfo)
                        self._keys.append(filterinfo.id)
                        self._filters[filterinfo.id] = filterinfo
                        item = filterinfo.name, filterinfo.id
                        pref.filtersComboBox.addItem(*item)
                        pref.filtersComboBox_new.addItem(*item)
                finally:
                    if fp: fp.close()
        # add filters to list
        for n in range(st.value('count', 0).toInt()[0]):
            fid = str(st.value("id" + str(n)).toString())
            fhash = str(st.value("hash" + str(n)).toString())
            if fid in self._filters:
                self.show_filter_instance(self._filters[fid], fhash)
            else:
                print "[WARNING] doens't found filter", fid


    def filter_settings(self, id, hash):
        return QSettings("blain", "filter-{0}-{1}".format(id, hash))


    def apply(self, posts):
        for i in range(len(self._instances[0])):
            hs = self._instances[0][i]
            id = self._instances[1][i]
            st = self.filter_settings(id, hs)
            posts = self._filters[id].filter(st, posts)
        return posts


    def changeDescription(self, index):
        self.app.preferences.ui.descriptionText.setText(
            self._filters[self._keys[int(index)]].filter_description)


    def changeNew(self, index):
        filter = self._filters[self._keys[int(index)]]
        ct = self.app.preferences.ui.configTable
        ct.clear()
        n = 0
        ct.setRowCount(len(filter.config))
        for key, value in filter.config.items():
            twi = QTableWidgetItem(key)
            twi.setFlags(Qt.ItemIsSelectable)
            ct.setItem(n, 0, twi)
            ct.setItem(n, 1, QTableWidgetItem(value))
            n += 1


    def show_filter_instance(self, filter, hash):
        if hash not in self._instances[0]:
            self._instances[0].append(hash)
            self._instances[1].append(filter.id)
            desc = str(filter.instance_description(
                self.filter_settings(filter.id, hash)))
            text = filter.name
            if desc:
                text = "{0}: {1}".format(text, desc)
            self.app.preferences.ui.filterList.addItem(text)


    def add_filter_instance(self, filter, hash):
        st = self.settings
        c = st.value('count',0).toInt()[0]
        st.setValue("id" + str(c), filter.id)
        st.setValue("hash" + str(c), hash)
        st.setValue('count', c + 1)
        self.show_filter_instance(filter, hash)


    def install(self):
        pref = self.app.preferences.ui
        ct = pref.configTable
        curi = int(pref.filtersComboBox_new.currentIndex())
        filter = self._filters[self._keys[curi]]
        config, hash = {}, gen_hash()
        settings = self.filter_settings(filter.id, hash)
        for i in range(ct.rowCount()):
            config[unicode(ct.item(i,0).text())] = unicode(ct.item(i,1).text())
        try:
            filter.install(settings, config)
        except Exception as e:
            msg = QMessageBox(pref)
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Installation Error ...")
            msg.setText("An Error occured during installation.")
            msg.setInformativeText("Could install filter '%s'." % filter.name)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setDetailedText(format_exc())
            msg.exec_()
            return
        # success
        self.add_filter_instance(filter, hash)
        pref.filtersComboBox_new.currentIndexChanged.emit(curi)
        pref.filtertabWidget.setCurrentIndex(0)


    def update(self, doupdate = True):
        self.app.db.update_cache()
        if doupdate: self.app.updateMessageView()
        #print "done."


    def remove(self):
        st = self.settings
        pref = self.app.preferences.ui
        n = pref.filterList.currentRow()
        filter = self._filters[self._instances[1][n]]
        fst = self.filter_settings(filter.id, self._instances[0][n])
        if 1 == QMessageBox.question(pref,
          "Removing %s ..." % filter.name,
          "Are you sure you want remove filter '%s' (%s)?" % \
          (filter.name, filter.instance_description(fst)), 0, 1, 2):
            pref.filterList.takeItem(n)
            c = st.value('count', 0).toInt()[0] - 1
            if n == c:
                for i in range(2):
                    self._instances[i].pop()
            for i in range(n, c):
                self._instances[0][i] = hs = self._instances[0][i+1]
                self._instances[1][i] = id = self._instances[1][i+1]
                st.setValue("id"   + str(i), id)
                st.setValue("hash" + str(i), hs)
            st.remove("id"   + str(c))
            st.remove("hash" + str(c))
            st.setValue('count', c)
            if exists(fst.fileName()):
                fileremove(fst.fileName())


    def move(self, from_row, to_row):
        st = self.settings
        for i in range(2):
            self._instances[i].insert(to_row, self._instances[i].pop(from_row))
        for i in range(min(from_row, to_row), max(from_row, to_row) + 1):
            st.setValue("id"   + str(i), self._instances[1][i])
            st.setValue("hash" + str(i), self._instances[0][i])


