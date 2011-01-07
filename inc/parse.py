
import re
import time
import calendar
from datetime import datetime, timedelta

from PyQt4 import Qt as qt

from inc.get_favicon import get_image


class drug():
    def __init__(self, **kwargs):
        for k in kwargs:
            setattr(self, k, kwargs[k])



def patchStyleSheet(stylesheet, **kwargs):
    if stylesheet == "None": stylesheet = None
    stylesheet = str(stylesheet or "")
    lines = stylesheet.replace("\n","").split(";")
    while "" in lines:
        lines.remove("")
    keys = list(map(lambda l:l.strip().split(":")[0].strip(), lines))
    for key, value in kwargs.items():
        if value is None:
            if key in keys:
                i = keys.index(key)
                lines = lines[:i] + lines[i+1:]
                keys  =  keys[:i] +  keys[i+1:]
        else:
            if key not in keys:
                lines.append( "{0}: {1}".format(key, value) )
                keys.append(key)
            else:
                i = keys.index(key)
                line = lines[i]
                lines[i] = "{0}{3}: {4}{2}".\
                    format(*(line.partition(line.strip()) + (key, value)))
    return ";\n".join(lines + [''])



months = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(" ")

rex = {
    'url': r'(?<!"|\()((https?|ftp|gopher|file)://(\w|\.|/|\(|\)|\?|=|%|&|:|#|_|-|~|\+)+)',
    'person': r'@(\w+)',
    'hashtag': r'#(\w+)',
    'group': r'!(\w+)'
    }
for k in rex:
    rex[k] = re.compile(rex[k])
rex = drug(**rex)


def services():
    return {
        'twitter': drug(
            url = "http://twitter.com/",
            parse = parse_twitter,
        ),
        'identica': drug(
            url = "http://identi.ca/",
            parse = parse_identica,
        )
}


def _clean_url(url):
    if url:
        url = unicode(url).replace("\/", "/")
    return url


def parse_date(date):
    date     = date.split(" ")
    
    # day_name = date[0] # we are not interested in that
    month    = months.index(date[1]) + 1
    day      = int(date[2])
    time     = map(int, date[3].split(":"))
    timezone = date[4]
    year     = int(date[5])
    hour, minute, second = time

    dt = datetime(year, month, day, hour, minute, second)
   
    # determine timezone delta
    hours = int(timezone[1:3])
    minutes = int(timezone[3:5])
    tz_delta = timedelta(hours=hours, minutes=minutes)
    if timezone[0] == '+':
        tz_delta *= -1

    return dt + tz_delta

def _parse_url(url):
    domain = url.split(':',1)[1][2:].split('/',1)
    if len(domain) == 1: domain, rest = domain[0], ""
    else:
        domain, rest = domain
        if not rest == "": rest = '/'+rest
    if domain.startswith('www.'): domain = domain[4:]
    return (url, domain, rest)



def parse_text(text, link):
    # parse link
    text = rex.url.sub(
        lambda x: ('<a href="%s" class="link" rel="nofollow">'+
            '<span class="domain">%s</span>%s</a>') % _parse_url(x.group()),text)
    # parse @person
    text = rex.person.sub(
        lambda x: '@<a href="%s" class="person" rel="nofollow">%s</a>'\
             % (link + x.group()[1:], x.group()[1:]), text)
    # parse #hashtag
    text = rex.hashtag.sub(
        lambda x: '#<a href="%s" class="tag" rel="nofollow">%s</a>'\
             % (link + x.group()[1:], x.group()[1:]), text)
    # parse !group
    return rex.group.sub(
        lambda x: '!<a href="%s" class="group" rel="nofollow">%s</a>'\
             % (link + x.group()[1:], x.group()[1:]), text)



def parse_twitter(post):
    post['user']['profile_url'] = services['twitter'].url + post['user']['screen_name']
    for k in ['profile_text_color', 'profile_background_color']:
        if post['user'][k]:
            post['user'][k] = "#" + post['user'][k]
    return post


def parse_identica(post):
    post['user']['profile_url'] = post['user']['statusnet_profile_url']
    return post


def parse_image(app, service, user, url):
    if url in app.avatar_cache:
        return (app.avatar_cache[url].pixmap(), url)
    if app.avatars.contains(url):
        return (qt.QPixmap(app.avatars.value(url)), url)
    print "fetching %s profile image from %s  (%s)" % (user, service, url)
    image = get_image(str(url))
    if image:
        image = qt.QPixmap.fromImage(qt.QImage.fromData(image)).scaled(32,32,
            qt.Qt.KeepAspectRatio, qt.Qt.SmoothTransformation)
        app.avatars.setValue(url, image)
    return (image, url)


def parse_post(service, post):
    _post = services[service].parse(post)
    post = drug(**_post)
    post.user = drug(**post.user)
    post.author = drug(screen_name = post.user.screen_name,
                       profile_url = post.user.profile_url,
                       name        = post.user.name,
                       url         = post.user.url)
    if 'retweeted_status' in _post:
        _repost = services[service].parse(post.retweeted_status)
        repost = drug(**_repost)
        repost.user = drug(**repost.user)
        post.text = repost.text
        post.author.screen_name = repost.user.screen_name
        post.author.profile_url = repost.user.profile_url
        post.author.name = repost.user.name
        post.author.url = repost.user.url
        post.user.profile_text_color = repost.user.profile_text_color
        post.user.profile_background_color=repost.user.profile_background_color
        post.user.profile_image_url = repost.user.profile_image_url
    return {
        'pid':post.id,
        'text':parse_text(_clean_url(post.text), services[service].url),
        'time':parse_date(post.created_at),
        'reply':post.in_reply_to_status_id,
        'plain':_clean_url(post.text),
        'source':_clean_url(post.source) or 'web',
        'unread':True,
        'user_id':post.user.screen_name,
        'service':service,
        'user_url':_clean_url(post.user.url),
        'user_name':post.user.name,
        'author_id':post.author.screen_name,
        'author_url':_clean_url(post.author.url),
        'author_name':post.author.name,
        'user_fgcolor':post.user.profile_text_color or "#ddd",
        'user_bgcolor':post.user.profile_background_color or "black",
        'replied_user':post.in_reply_to_screen_name,
        'by_conversation':False,
        'user_profile_url':_clean_url(post.user.profile_url),
        'profile_image_url':_clean_url(post.user.profile_image_url),
        'author_profile_url':(post.author.profile_url)}


def prepare_post(blob):
    post = drug(**blob)
    repeatstr = ""
    if post.author_id != post.user_id:
        repeatstr = ' repeated <a href="%s">%s</a> (<a href="%s">%s</a>)' % \
            (post.author_url, post.author_name,
             post.author_profile_url, post.author_id)
    post.info = '<a href="%s">%s</a> (<a href="%s">%s</a>)%s via %s on %s' % \
        (post.user_url, post.user_name, post.user_profile_url,
         post.user_id, repeatstr, post.source,
         post.time.strftime("%a %d %b %Y %H:%M:%S"))
    post.imageinfo = [post.service, post.user_id, post.profile_image_url]
    return post


def pythonize_post(blob):
    blob = dict([(str(k),blob[k]) for k in blob])
    for k in ['text','plain','source','service','user_id','user_url',
                'user_name','user_fgcolor','user_bgcolor','user_profile_url',
                'profile_image_url', 'author_name', 'author_id',
                'author_url', 'author_profile_url', 'replied_user']:
        if blob[k]:
            blob[k] = unicode(blob[k])
    return blob


services = services()

