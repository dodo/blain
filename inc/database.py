
from os.path import dirname, join as pathjoin
from traceback import print_exc

from PyQt4.Qt import QSettings

from inc.db import Database
from inc.models import setup_models
from inc.parse import drug, parse_post, prepare_post, pythonize_post
from inc.microblogging import api_call


class Databaser:

    def __init__(self, app):
        self.app = app
        self.db = None


    def connect(self):
        self.app.addMessage.connect(self.addMessage)
#get messages by cache or smth

    def setup(self):
        st = QSettings("blain", "blain")
        st.setValue("_", 0)
        st.sync()
        settingspath = dirname(str(st.fileName()))
        self.db = db = Database(location=pathjoin(settingspath, "blain.sqlite"))
        setup_models(db)


    def commit(self):
        self.db.session.commit()


    def get_cached_unread(self, maxcount = 200):
        Post, Cache = self.db.Post, self.db.Cache
        return Post.find().order_by(Post.time.desc()).filter_by(unread = True).\
            filter(Post.id.in_(self.db.session.query(Cache.pid))).\
            limit(maxcount).all()


    def get_messages_from_cache(self, maxcount = 200):
        Post, Cache = self.db.Post, self.db.Cache
        return Post.find().order_by(Post.time.desc()).\
            filter(Post.id.in_(self.db.session.query(Cache.pid))).\
            limit(maxcount).all()


    def get_knownids(self, sid):
        Post = self.db.Post
        knownids = Post.find(Post.pid).order_by(Post.time.desc()).\
            filter_by(source_id = sid).limit(2000).all()
        knownids = list(map(lambda i:i.pid, knownids))
        return knownids


    def update_cache(self):
        apply = self.app.filters.apply
        Post, Cache = self.db.Post, self.db.Cache
        max = Post.find().count()
        Cache.find().delete()
        if max < 200:
            posts = apply(Post.find().order_by(Post.time.desc())\
                .filter_by(by_conversation=False).all())
        else:
            posts, got = [], 0
            while len(posts) < 200 and got < max:
                new = Post.find().filter_by(by_conversation=False).order_by(
                    Post.time.desc()).offset(got).limit(400).all()
                got += len(new)
                posts += apply(new)
        list(map(lambda p: Cache(pid=p.id).add(), posts))
        self.db.session.commit()
        return posts


    def get_unread_count(self):
        return self.db.Post.find().filter_by(unread = True).count() or None


    def get_unread_marked_count(self):
        return self.db.UnreadCache.find().count() or None


    def set_unread_status(self, pid, status):
        self.db.Post.find().filter_by(pid = pid).update({'unread':status})
        self.commit()


    def set_all_unread_status(self, status):
        Post, UnreadCache = self.db.Post, self.db.UnreadCache
        UnreadCache.find().delete()
        postids = Post.find(Post.id).filter_by(unread = True).all()
        Post.find().filter_by(unread = True).update({'unread':status})
        for post in postids:
            UnreadCache(pid = post.id).add()
        self.commit()


    def reset_all_unread_status(self, status):
        Post, UnreadCache = self.db.Post, self.db.UnreadCache
        Post.find().filter(Post.id.in_(self.db.session.query(
            UnreadCache.pid))).update({'unread':status}, 'fetch')
        UnreadCache.find().delete()
        self.commit()



    def get_conversation_messages(self, pid):
        Post, Conversation = self.db.Post, self.db.Conversation
        msgs, convs = [], Conversation.find().filter_by(pid = pid).all()
        if not convs:
            post = Post.find().filter_by(pid = pid).one()
            if post.reply is not None:
                self.build_conversation(post.service, post.__dict__)
                convs = Conversation.find().filter_by(pid = pid).all()
        for conv in convs:
            ids = list(map(int, conv.ids.split()))
            msgs += Post.find().filter(Post.pid.in_(ids)).all()
        return msgs


    def build_conversation(self, service, previous):
        if not previous: return # nothing to do
        previous = [drug(**previous)]
        service = unicode(service)
        print "try to build conversation", previous[0].pid, "(%s)" % service
        Post, Conversation = self.db.Post, self.db.Conversation
        while True:
            posts = Post.find().filter_by(pid = previous[-1].reply).all()
            if posts:
                previous.append(prepare_post(posts[0].__dict__))
            else:
                try:
                    status = api_call(service, 'statuses/user_timeline',
                        {'id': previous[-1].replied_user,
                         'max_id':previous[-1].reply,
                         'count': 1})
                except:
                    print_exc()
                    break
                if not status: break # nothing fetched or empty list
                update = parse_post(service, "", status[0])
                update['source_id'] = update['user_id']
                print service, "con", update['pid']
                update['by_conversation'] = True
                Post(**update).add()
                previous.append(drug(**update))
            if previous[-1].reply is None: break
        if len(previous) == 1: return # still no conversation
        ids = " ".join(list(map(lambda p: str(p.pid), previous[1:])))
        Conversation(pid = previous[0].pid, ids = ids).save()
        print "conversation", previous[0].pid, "build."
        self.app.reader.update()


    def addMessage(self, service, blob):
        blob = pythonize_post(blob)
        #if not blob['by_conversation'] or blob['reply'] is not None:
        #    self.build_conversation(service, blob)
        self.db.Post(**blob).add()

