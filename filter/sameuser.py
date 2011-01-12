
description = """
<b>Uniquify User</b><br/>
Merging a twitter-id and a identica-id together.<br/>
No duplicated messages will be displayed.
"""


def filter_fun(st, posts):
    res, texts, patched = [], [], []
    twitterid  = unicode(st.value('twitterid' ).toString())
    identicaid = unicode(st.value('identicaid').toString())
    for post in reversed(posts):
        if (post.service.startswith("twitter")  and post.user_id == twitterid) or\
           (post.service.startswith("identica") and post.user_id == identicaid):
            text = post.plain.\
                replace("!", "#").\
                replace(">","&gt;").\
                replace("<","&lt;")
            if text not in texts:
                texts.append(text)
                res.append(post)
            else:
                i = texts.index(text)
                if i not in patched:
                    if len(post.service) < 9:
                        if len(res[i].service) > 8:
                            post.service = res[i].service
                        else:
                            post.service += res[i].service
                    patched.append(i)
                    res[i] = post
        else:
            texts.append(None)
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

