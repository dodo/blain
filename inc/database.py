
from os.path import dirname, join as pathjoin

from PyQt4.Qt import QSettings

from inc.db import Database
from inc.models import setup_models

class Databaser:

    def __init__(self, app):
        self.app = app
        self.db = None


    def connect(self):
        self.app.addMessage.connect(self.addMessage)
#get messages by cache or smth

    def setup(self):
        settingspath = dirname(str(QSettings("blain", "blain").fileName()))
        self.db = db = Database(location=pathjoin(settingspath, "blain.sqlite"))
        setup_models(db)


    def commit(self):
        self.db.session.commit()


    def get_messages_from_cache(self, maxcount):
        Post, Cache = self.db.Post, self.db.Cache
        return Post.find().order_by(Post.time.desc()).\
            filter(Post.id.in_(self.db.session.query(Cache.pid))).\
            limit(maxcount).all()


    def get_knownids(self, user):
        Post = self.db.Post
        knownids = Post.find(Post.pid).order_by(Post.time.desc()).\
            filter_by(user_id = user).limit(2000).all()
        knownids = list(map(lambda i:i.pid, knownids))
        return knownids


    def update_cache(self):
        apply = self.app.filters.apply
        Post, Cache = self.db.Post, self.db.Cache
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
        self.db.session.commit()
        return posts


    def addMessage(self, blob):
        blob = dict([(str(k),blob[k]) for k in blob])
        for k in ['text','plain','source','service','user_id','user_url',
                  'user_name','user_fgcolor','user_bgcolor','user_profile_url',
                  'profile_image_url']:
            if blob[k]:
                blob[k] = unicode(blob[k])
        self.db.Post(**blob).add()

