import sys
import shutil
import urllib2
from traceback import print_exc

lxml = None
HEADERS = {
    'User-Agent': 'urllib2 (Python %s)' % sys.version.split()[0],
    'Connection': 'close',
}


def get_image(url):
    request = urllib2.Request(url, headers=HEADERS)
    try:
        return urllib2.urlopen(request).read()
    except(urllib2.HTTPError, urllib2.URLError):
        print "[ERROR] cannot fetch image {0}".format(url)
        print_exc()
    return None


def get_favicon(url, path=None):
    global lxml
    def has_lxml():
        global lxml
        if lxml is None:
            try:
                from lxml import html as _lxml
                lxml = _lxml
                return True
            except:
                from warnings import warn
                warn("lxml not found, so dont blame me when favicon loading fails!")
                lxml = False
                return False
        return lxml != False
    def guess():
        if not has_lxml():
            return None
        icon = None
        request = urllib2.Request(url, headers=HEADERS)
        try:
            content = urllib2.urlopen(request).read(2048) # 2048 bytes should be enought for most of websites
        except(urllib2.HTTPError, urllib2.URLError):
            return None
        icon_path = lxml.fromstring(content).xpath(
            '//link[@rel="icon" or @rel="shortcut icon"]/@href'
        )
        for icon_url in icon_path:
            icon = get_image(icon_url)
            if icon is not None:
                return icon
        return None

    def try_next():
        request = urllib2.Request(url + path.pop(), headers=HEADERS)
        try:
            return urllib2.urlopen(request).read()
        except(urllib2.HTTPError, urllib2.URLError):
            if len(path):
                return try_next()
            else:
                return guess()

    if path is None:
        path = ['favicon.ico', "favicon.png"]
    if type(path) is not list:
        path = [path]
    if not url.endswith('/'):
        url += '/'
    if len(path):
        return try_next()
    else:
        return None


if __name__ == '__main__':
    print "Twitter:"
    print get_favicon('http://twitter.com')
    print "Idenci.ca:"
    print get_favicon('http://identi.ca')
    #print "google:"
    #print get_image("http://google.com/images/logos/ps_logo2.png")
