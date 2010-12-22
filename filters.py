
import random
from os import listdir, mkdir, remove as fileremove
from imp import find_module, load_module
from shutil import copyfile
from traceback import format_exc
from os.path import exists, isdir, isfile, join as pathjoin
from PyQt4 import Qt as qt

from parsing import drug, prepare_post


random.seed()
__filters__ = {}
__filters_keys__ = []
__filters_instances__ = ([], []) # hashes, ids


def gen_hash():
    return "%016x" % random.getrandbits(64)


def filter_settings(id, hash):
    return qt.QSettings("blain", "filter-{0}-{1}".format(id, hash))


def show_filter_instance(app, filter, hash):
    if hash not in __filters_instances__[0]:
        __filters_instances__[0].append(hash)
        __filters_instances__[1].append(filter.id)
        app.preferences.filterList.addItem(filter.name + ": " + \
            str(filter.instance_description(filter_settings(filter.id, hash))))


def add_filter_instance(app, filter, hash):
    c = app.filters.value('count',0).toInt()[0]
    app.filters.setValue("id" + str(c), filter.id)
    app.filters.setValue("hash" + str(c), hash)
    app.filters.setValue('count', c + 1)
    show_filter_instance(app, filter, hash)



def changeFilterDescription(app):
    def change(index):
        app.preferences.descriptionText.setText(
            __filters__[__filters_keys__[int(index)]].filter_description)
    return change


def changeFilterNew(app):
    def change(index):
        filter = __filters__[__filters_keys__[int(index)]]
        ct = app.preferences.configTable
        ct.clear()
        n = 0
        ct.setRowCount(len(filter.config))
        for key, value in filter.config.items():
            twi = qt.QTableWidgetItem(key)
            twi.setFlags(qt.Qt.ItemIsSelectable)
            ct.setItem(n, 0, twi)
            ct.setItem(n, 1, qt.QTableWidgetItem(value))
            n += 1
    return change


def installFilter(app):
    def install():
        pref = app.preferences
        ct = pref.configTable
        curi = int(pref.filtersComboBox_new.currentIndex())
        filter = __filters__[__filters_keys__[curi]]
        config, hash = {}, gen_hash()
        settings = filter_settings(filter.id, hash)
        for i in range(ct.rowCount()):
            config[unicode(ct.item(i,0).text())] = unicode(ct.item(i,1).text())
        try:
            filter.install(settings, config)
        except Exception as e:
            msg = qt.QMessageBox(pref)
            msg.setIcon(qt.QMessageBox.Critical)
            msg.setWindowTitle("Installation Error ...")
            msg.setText("An Error occured during installation.");
            msg.setInformativeText("Could install filter '%s'." % filter.name);
            msg.setStandardButtons(qt.QMessageBox.Ok);
            msg.setDetailedText(format_exc());
            msg.exec_()
            return
        qt.QMessageBox.information(pref,
            "Installling "+filter.name+" ...",
            "Filter '%s' successful installed." % filter.name)
        add_filter_instance(app, filter, hash)
        pref.filtersComboBox_new.currentIndexChanged.emit(curi)
        pref.filtertabWidget.setCurrentIndex(0)
    return install


def updateFilter(app, doupdate = True):
    def update():
        Post, Cache = app.db.Post, app.db.Cache
        max = Post.find().count()
        Cache.find().delete()
        if max < 200:
           posts = apply(Post.find().order_by(Post.time.desc()).all())
        else:
            posts, got = [], 0
            while len(posts) < 200 and got < max:
                new = Post.find().order_by(
                    Post.time.desc()).offset(got).limit(400).all()
                got += len(new)
                posts += apply(new)
        list(map(lambda p: Cache(pid=p.id).add(), posts))
        app.db.session.commit()
        if doupdate: app.updateMessageView()
        print "done."
    return update


def removeFilter(app):
    def remove():
        pref = app.preferences
        n = pref.filterList.currentRow()
        filter = __filters__[__filters_instances__[1][n]]
        fst = filter_settings(filter.id, __filters_instances__[0][n])
        if 1 == qt.QMessageBox.question(pref,
          "Removing %s ..." % filter.name,
          "Are you sure you want remove filter '%s' (%s)?" % \
          (filter.name, filter.instance_description(fst)), 0, 1, 2):
            pref.filterList.takeItem(n)
            c = app.filters.value('count', 0).toInt()[0] - 1
            for i in range(n, c):
                __filters_instances__[0][i] = hs = __filters_instances__[0][i+1]
                __filters_instances__[1][i] = id = __filters_instances__[1][i+1]
                app.filters.setValue("id"   + str(i), id)
                app.filters.setValue("hash" + str(i), hs)
            app.filters.remove("id"   + str(c))
            app.filters.remove("hash" + str(c))
            app.filters.setValue('count', c)
            fileremove(fst.fileName())
    return remove

# exports

def apply(posts):
    for i in range(len(__filters_instances__[0])):
        hs = __filters_instances__[0][i]
        id = __filters_instances__[1][i]
        st = filter_settings(id, hs)
        posts = __filters__[id].filter(st, posts)
    return posts


def setup(app, settingspath):
    filterpath = pathjoin(settingspath, "filter")
    if not exists(filterpath) or not isdir(filterpath):
        mkdir(filterpath)
    localfilterpath = pathjoin(app.cwd, "filter")
    for filename in listdir(localfilterpath):
        if isfile(pathjoin(localfilterpath, filename)) and \
            filename.endswith(".py") and \
            not exists(pathjoin(filterpath, filename)):
            copyfile(pathjoin(localfilterpath, filename),
                        pathjoin(     filterpath, filename))

    pref = app.preferences
    pref.filtersComboBox.currentIndexChanged.connect(changeFilterDescription(app))
    pref.filtersComboBox_new.currentIndexChanged.connect(changeFilterNew(app))
    pref.addfilterButton.clicked.connect(installFilter(app))
    pref.updatefilterButton.clicked.connect(updateFilter(app))
    pref.removefilterButton.clicked.connect(removeFilter(app))

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
                    print "error: filter '%s' not valid." % filename
                else:
                    filterinfo = drug(**filterinfo)
                    __filters_keys__.append(filterinfo.id)
                    __filters__[filterinfo.id] = filterinfo
                    item = filterinfo.name, filterinfo.id
                    pref.filtersComboBox.addItem(*item)
                    pref.filtersComboBox_new.addItem(*item)
            finally:
                if fp: fp.close()

    for n in range(app.filters.value('count', 0).toInt()[0]):
        fid = str(app.filters.value("id" + str(n)).toString())
        fhash = str(app.filters.value("hash" + str(n)).toString())
        if fid in __filters__:
            show_filter_instance(app, __filters__[fid], fhash)
        else:
            print "doens't found filter", fid


