import unittest
from node import protocol, constants

def create_inital_data(datatype):
    initial = {
        'type': datatype,
        'v': constants.VERSION
    }
    return initial

def expected_proto_store():
    expected_data = create_inital_data('store')
    expected_data['key'] = 'test_key'
    expected_data['value'] = 'test_value'
    expected_data['originalPublisherID'] = 'test_pub'
    expected_data['age'] = 'test_age'
    return expected_data

class TestProtocol(unittest.TestCase):
    """Allow testing of Protocol methods"""

    def expected_proto_page(self):
        expected = create_inital_data('page')
        expected['uri'] = 'test_uri'
        expected['pubkey'] = 'test_pubkey'
        expected['senderGUID'] = self.guid
        expected['text'] = 'test_text'
        expected['nickname'] = 'test_nickname'
        expected['PGPPubKey'] = 'test_pgp'
        expected['email'] = 'test_email'
        expected['arbiter'] = 'test_arbiter'
        expected['notary'] = 'test_notary'
        expected['notary_description'] = 'test_notarydesc'
        expected['notary_fee'] = 'test_notaryfee'
        expected['arbiter_description'] = 'test_arbiterdesc'
        expected['sin'] = 'test_sin'
        expected['homepage'] = 'test_homepage'
        expected['avatar_url'] = 'test_avatar'
        return expected

    def expected_query_page(self):
        expected_data = create_inital_data('query_page')
        expected_data['findGUID'] = self.guid
        return expected_data

    def expected_shout(self):
        expected_data = self.expected_proto_page()
        expected_data['type'] = 'shout'
        return expected_data

    def setUp(self):
        self.guid = "test_guid"

    def test_proto_page_sets_values_correctly(self):
        expected_data = self.expected_proto_page()
        data = protocol.proto_page('test_uri', 'test_pubkey', self.guid,
                                   'test_text', 'test_nickname', 'test_pgp',
                                   'test_email', 'test_arbiter', 'test_notary',
                                   'test_notarydesc', 'test_notaryfee',
                                   'test_arbiterdesc', 'test_sin',
                                   'test_homepage', 'test_avatar')
        self.assertEqual(data, expected_data)

    def test_shout_sets_value_correctly(self):
        expected_data = self.expected_shout()
        returned_data = protocol.shout(self.expected_proto_page())
        self.assertEqual(returned_data, expected_data)

    def test_query_page_sets_value_correctly(self):
        expected_data = self.expected_query_page()
        returned_data = protocol.query_page(self.guid)
        self.assertEqual(returned_data, expected_data)

    def test_proto_store_sets_values_correctly(self):
        returned_data = protocol.proto_store('test_key', 'test_value', 'test_pub',
                                             'test_age')
        self.assertEqual(returned_data, expected_proto_store())
