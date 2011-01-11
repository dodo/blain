
description = """
<b>Show Only Unread</b><br/>
Hide all as read marked Posts.
"""


def filter_fun(settings, posts):
    return [ post for post in posts if post.unread ]


def install(settings, config):
    pass


def instance(settings):
    return ""


def info():
    return {'id'     : "unreads",
            'name'   : "only unread posts",
            'install': install,
            'filter' : filter_fun,
            'filter_description': description,
            'instance_description': instance,
            'config': {},
           }

