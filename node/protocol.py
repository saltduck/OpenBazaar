from node import constants


def shout(data):
    data['type'] = 'shout'
    return data


def proto_page(uri, pubkey, guid, text, nickname, pgp_pub_key, email,
               arbiter, notary, notary_description, notary_fee,
               arbiter_description, sin, homepage, avatar_url):
    data = {
        'type': 'page',
        'uri': uri,
        'pubkey': pubkey,
        'senderGUID': guid,
        'text': text,
        'nickname': nickname,
        'PGPPubKey': pgp_pub_key,
        'email': email,
        'arbiter': arbiter,
        'notary': notary,
        'notary_description': notary_description,
        'notary_fee': notary_fee,
        'arbiter_description': arbiter_description,
        'sin': sin,
        'homepage': homepage,
        'avatar_url': avatar_url,
        'v': constants.VERSION
    }
    return data


def query_page(guid):
    data = {
        'type': 'query_page',
        'findGUID': guid,
        'v': constants.VERSION
    }
    return data


def proto_store(key, value, original_publisher_id, age):
    data = {
        'type': 'store',
        'key': key,
        'value': value,
        'originalPublisherID': original_publisher_id,
        'age': age,
        'v': constants.VERSION
    }
    return data
