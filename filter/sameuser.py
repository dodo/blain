
description = """
<b>Uniquify User</b><br/>
Merging a twitter-id and a identica-id together.<br/>
No duplicated messages will be displayed.
"""


def filter_fun(st, posts):
    res, texts = [], []
    twitterid  = unicode(st.value('twitterid' ).toString())
    identicaid = unicode(st.value('identicaid').toString())
    for post in reversed(posts):
        if (post.service == "twitter"  and post.user_id == twitterid) or \
           (post.service == "identica" and post.user_id == identicaid):
            text = post.plain.\
                replace("!", "#").\
                replace(">","&gt;").\
                replace("<","&lt;")
            if text not in texts:
                texts.append(text)
                res.append(post)
        else:
            res.append(post)
    return res


def install(settings, config):
    for key, value in config.items():
        settings.setValue(key, value)


def instance(st):
    return "{0} == {1}".format(st.value('identicaid').toString(),
                               st.value('twitterid').toString())


def info():
    return {'id'     : "uniquser",
            'name'   : "uniquify user",
            'install': install,
            'filter' : filter_fun,
            'filter_description': description,
            'instance_description': instance,
            'config': {'twitterid' : "",
                       'identicaid': "",
                      },
           }

