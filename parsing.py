
import re
import time
import calendar
from datetime import datetime, timedelta


class drug():
    def __init__(self, **kwargs):
        for k in kwargs:
            setattr(self, k, kwargs[k])


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
    return post


def parse_identica(post):
    post['user']['profile_url'] = post['user']['statusnet_profile_url']
    return post


#from pprint import pprint
def parse_post(service, post):
    #pprint(post)
    post = services[service].parse(post)
    post = drug(**post)
    post.user = drug(**post.user)
    post.text = parse_text(post.text, services[service].url)
    post.time = parse_date(post.created_at)
    post.info = '<a href="%s">%s</a> (<a href="%s">%s</a>) via %s on %s' % \
        (post.url, post.user.name, post.user.profile_url, post.user.screen_name,
         post.source, post.time.strftime("%a %d %b %Y %H:%M:%S"))
    return post


services = services()

