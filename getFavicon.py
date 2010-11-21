import sys
import shutil
import urllib2
import lxml.html


HEADERS = {
    'User-Agent': 'urllib2 (Python %s)' % sys.version.split()[0],
    'Connection': 'close',
}


def get_favicon(url, path=None):
    def guess():
        icon = None
        request = urllib2.Request(url, headers=HEADERS)
        try:
            content = urllib2.urlopen(request).read(2048) # 2048 bytes should be enought for most of websites
        except(urllib2.HTTPError, urllib2.URLError):
            return None
        icon_path = lxml.html.fromstring(x).xpath(
            '//link[@rel="icon" or @rel="shortcut icon"]/@href'
        )
        if icon_path:
            request = urllib2.Request(url + icon_path[:1], headers=HEADERS)
            try:
                return urllib2.urlopen(request).read()
            except(urllib2.HTTPError, urllib2.URLError):
                pass
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
