from db import model


def setup_models(db):
    return (
        model(db, "Post",
            pid = 'integer',
            text = 'string', # parsed message text with html
            plain = 'string', # plain message text
            time = 'datetime',
            source = 'string',
            service = 'string',
            user_id = 'string', # screen_name
            user_url = 'string',
            user_name = 'string',
            user_profile_url = 'string',
            profile_image_url = 'string',
            ),
        )

