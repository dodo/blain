
from PyQt4.Qt import QSettings

from json_hack import json
from parsing import parse_post
from microblogging import api_call

MAX_PAGE_COUNT = 200


def get_page(service, user, count, page, opts={}):
    options = {
            'page': page,
            'count': count,
            'id': user,
            'include_rts': 'true', #get all 200 tweets from twitter
            }
    options.update(opts)
    return api_call(service, 'statuses/user_timeline', options)


class Pager:

    def __init__(self, globalsettings):
        print "TODO  order post in the last 3 pages by time after update"
        self.settings = globalsettings
        self.users = QSettings("blain", "users")


    def get_page_count(self, service, user):
        return self.users.value("pages/"+service+user,0).toInt()[0]


    def update(self, service, user): # returns list with new posts
        if not service or not user:
            return None
        n = 1
        _id = ''
        page = 1
        step = 200

        pagenr, _ = self.users.value("pages/"+service+user, 1).toInt()
        last = self.users.value("lastids/"+user, "").toString()
        setts = QSettings("blain", "%s-%s-%i"%(user, service, pagenr))
        count, _ = setts.value("id/count", 0).toInt()

        servicecount = api_call(service, 'users/show', {'id': user})['statuses_count']
        while servicecount > 0:
            fetch_count = min(n==1 and int(step/10) or step, servicecount)
            print "%i Fetching %i from page %i, %i updates remaining (%s)" % \
                (n, fetch_count, page, servicecount, service)
            new_statuses = get_page(service,user,fetch_count,page,page == 2 and _id and {'max_id':_id} or {})
            stop = False
            if n > 1:
                servicecount -= len(new_statuses)
            #new_statuses.reverse()
            for status in new_statuses:
                _id = str(status['id'])
                id = service + _id
                print id
                if id == last:
                    print "found lastid. stopping"
                    stop = True
                if not setts.contains("post/"+id):
                    dump = json.dumps(status)
                    setts.setValue("post/"+id, dump)
                    setts.setValue("id/%i"%count, id)
                    count += 1
                    if count >= MAX_PAGE_COUNT:
                        setts.setValue("id/count", count)
                        count = 0
                        pagenr += 1
                        setts = QSettings("blain", "%s-%s-%i"%(user, service, pagenr))
                elif n != 1 and n > 2:
                    print "found known id. stopping"
                    stop = True
            n += 1
            if stop: break
            if fetch_count != int(step/10):
                page += 1
        setts.setValue("id/count", count)
        self.users.setValue("lastid/"+user, service+str(new_statuses[0]['id']))
        self.users.setValue("pages/"+service+user, pagenr)


    def load_page(self, service, user, page=1):
        if not service or not user or page > self.get_page_count(service, user):
            return None
        setts = QSettings("blain", "%s-%s-%i"%(user, service, page))
        count, _ = setts.value("id/count", 0).toInt()
        page = []
        for n in range(count):
            id = setts.value("id/%i"%n, "").toString()
            if id:
                post = str(setts.value("post/"+id, "").toString())
                if post:
                    page.append(parse_post(service, json.loads(post)))
        return page



