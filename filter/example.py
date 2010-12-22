
description = """Example
This is an example filter.
It doens't do anything.
"""


def filter_fun(settings, posts):
    return posts


def install(settings, config):
    pass


def instance(settings):
    return ""


def info():
    return {'id'     : "example",
            'name'   : "example filter",
            'install': install,
            'filter' : filter_fun,
            'filter_description': description,
            'instance_description': instance,
            'config': {},
           }

