
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



def patchStyleSheet(stylesheet, key, value):
    stylesheet = str(stylesheet)
    lines = stylesheet.replace("\n","").split(";")
    if value is None:
        if key in stylesheet:
            for i, line in enumerate(lines):
                if line.strip().startswith(key):
                    lines = lines[:i] + lines[i+1:]
                    break
    else:
        if key not in stylesheet:
            lines.append( "%s: %s" % (key, value) )
        else:
            for i, line in enumerate(lines):
                if line.strip().startswith(key):
                    lines[i] = "{0}{3}: {4}{2}".\
                        format(*(line.partition(line.strip()) + (key, value)))
                    break
    return ";\n".join(lines)




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


def parse_date(date):
    # splitting into time and timezone
    tz_str = date[-10:-5]

    # calculating raw time
    strf = "%a %b %d %H:%M:%S " +tz_str+ " %Y"
    stime = time.strptime(date, strf)
    stamp = calendar.timegm(stime)

    # determine timezone delta
    hours = int(tz_str[1:3])
    minutes = int(tz_str[3:5])
    tz_delta = timedelta(hours=hours, minutes=minutes)
    if tz_str[0] == '+':
        tz_delta *= -1

    return datetime.fromtimestamp(stamp) + tz_delta


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
    print "fetching %s profile image from %s" % (user, service)
    image = get_image(str(url))
    if image:
        image = qt.QPixmap.fromImage(qt.QImage.fromData(image)).scaled(32,32,
            qt.Qt.KeepAspectRatio, qt.Qt.SmoothTransformation)
        app.avatars.setValue(url, image)
    return (image, url)


def parse_post(service, post):
    post = services[service].parse(post)
    post = drug(**post)
    post.user = drug(**post.user)
    return {
        'pid':post.id,
        'text':parse_text(post.text, services[service].url),
        'plain':post.text,
        'source':post.source,
        'time':parse_date(post.created_at),
        'user_id':post.user.screen_name,
        'service':service,
        'user_url':post.user.url,
        'user_name':post.user.name,
        'user_fgcolor':post.user.profile_text_color or "#ddd",
        'user_bgcolor':post.user.profile_background_color or "black",
        'user_profile_url':post.user.profile_url,
        'profile_image_url':post.user.profile_image_url}


def prepare_post(blob):
    post = drug(**blob)
    post.info = '<a href="%s">%s</a> (<a href="%s">%s</a>) via %s on %s' % \
        (post.user_url, post.user_name, post.user_profile_url,
         post.user_id, post.source, post.time.strftime("%a %d %b %Y %H:%M:%S"))
    post.imageinfo = [post.service, post.user_id, post.profile_image_url]
    return post


services = services()

