
description = """
<b>Hide Conversation</b><br/>
Hide Posts that are answers on other Posts.
"""


def filter_fun(settings, posts):
    return filter(lambda p: p.reply is None, posts)


def install(settings, config):
    pass


def instance(settings):
    return ""


def info():
    return {'id'     : "hideconversations",
            'name'   : "hide conversations",
            'install': install,
            'filter' : filter_fun,
            'filter_description': description,
            'instance_description': instance,
            'config': {},
           }

