#!/usr/bin/env python
###############################################################################
##
## digger - Digging into some data mines
## Copyright (C) 2010  core, Thammi
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU Affero General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Affero General Public License for more details.
##
## You should have received a copy of the GNU Affero General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.
##
###############################################################################

import sys
import re
import urllib
from warnings import warn

from json_batch import save_batch, json

class UnknownServiceException(Exception):

    def __init__(self, service):
        self.service = service

    def __str__(self):
        return self.service

class ServiceFailedException(Exception):

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


### NEW
class UrlOpener(urllib.FancyURLopener):

    def prompt_user_passwd(self, host, realm):
        return ("user", "password")
###

urls = {
        'identica': {
            'api': "http://identi.ca/api/",
            'search': "http://identi.ca/api/search.json",
            },
        'twitter': {
            'api': "http://api.twitter.com/1/",
            'search':"http://search.twitter.com/search.json",
            },
        'telecomix': {
            'api': "http://status.telecomix.org/api/",
            'search': "http://status.telecomix.org/api/search.json",
            },
        }

def available_services():
    return urls.keys()

def api_call(service, method, options, tries=3):
    if service not in urls:
        raise UnknownServiceException(service)

    url_parts = {
            'query': urllib.urlencode(options),
            'base_url': urls[service]['api'],
            'method': method,
            }

    res = UrlOpener().open("{base_url}{method}.json?{query}".format(**url_parts))

    # watch rate limit (twitter only)
    ratelimit = re.search("X-RateLimit-Remaining: ([0-9]+)", str(res.info()))
    if ratelimit != None:
        print "remaining API-calls: %s" % ratelimit.group(1)

    if res.getcode() < 300:
        return json.load(res)
    else:
        if tries > 1 and res.getcode() >= 500:
            print "ERROR while fetching, retrying"
            return api_call(service, method, options, tries-1)
        else:
            msg = "Unable to fetch: %i" % res.getcode()
            raise ServiceFailedException(msg)

def search(service, query, page=1):
    if service not in urls:
        raise UnknownServiceException(service)

    options = {
            'q': query,
            'rpp': 100,
            'page': page,
            }

    url_parts = {
            'query': urllib.urlencode(options),
            'url': urls[service]['search'],
            }

    res = UrlOpener().open("{url}?{query}".format(**url_parts))

    if res.getcode() < 300:
        raw = json.load(res)

        updates = raw['results']

        if raw['results_per_page'] == len(updates):
            updates.extend(search(service, query, page + 1))

        return updates
    else:
        msg = "Unable to fetch: %i" % res.getcode()
        raise ServiceFailedException(msg)

def get_page(service, user, count, page):
    options = {
            'page': page,
            'count': count,
            'id': user,
            'include_rts': 'true', #get all 200 tweets from twitter
            }

    return api_call(service, 'statuses/user_timeline', options)

def find_updates(service, query):
    api_call(service, 'search', {})

def get_statuses(service, user, limit=None):
    step = 200
    page = 1
    statuses = []

    # how many dents are there?
    count = api_call(service, 'users/show', {'id': user})['statuses_count']

    if limit:
        count = min(count, limit)

    while count > 0:
        print "Fetching page %i, %i updates remaining" % (page, count)

        # how many statuses to fetch?
        fetch_count = min(step, count)

        # fetch them
        new_statuses = get_page(service, user, fetch_count, page)

        # update the count
        count -= len(new_statuses)

        # save the statuses
        statuses.extend(new_statuses)

        # next page
        page += 1

    return statuses

def save_users(service, users):
    for user in users:
        print "===> Fetching %s on %s" % (user, service)

        updates = get_statuses(service, user)

        if not updates:
            print "ERROR: No results!"
        else:
            save_batch(user, updates, "raw_updates_%s.json" % service)

            print "Amount of updates:  %i" % len(updates)
            print

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print "Please specify at least the service (identica or twitter) and one user id"
        sys.exit(1)
    else:
        service = sys.argv[1]
        users = sys.argv[2:]

        save_users(service, users)

