from db import model


def setup_models(db):
    return (
        model(db, "Post",
            pid = 'integer',
            time = 'datetime',
            text = 'string', # parsed message text with html
            plain = 'string', # plain message text
            reply = 'integer', # pid
            source = 'string',
            unread = 'boolean',
            service = 'string',
            user_id = 'string', # screen_name
            user_url = 'string',
            user_name = 'string',
            author_id = 'string',
            author_url = 'string',
            author_name = 'string',
            user_fgcolor = 'string',
            user_bgcolor = 'string',
            replied_user = 'string',
            by_conversation = 'boolean', # all posts only reference by conversation (not by timeline)
            user_profile_url = 'string',
            profile_image_url = 'string',
            author_profile_url = 'string',
            ),
        model(db, "Cache",
            pid = "integer", # Post.id
            ),
        model(db, "Conversation",
            pid = 'integer',
            ids = 'string', # space seperated

            ),
        )

