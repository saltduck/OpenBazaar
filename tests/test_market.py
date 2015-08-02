import unittest
import mock
from testfixtures import log_capture

from node import db_store
from node.market import Market
from node.transport import CryptoTransportLayer

class TestMarket(unittest.TestCase):

    def setUp(self):
        self.transport = mock.MagicMock(spec=CryptoTransportLayer)
        self.dht_mock = mock.MagicMock()
        self.settings_mock = {'welcome':'enable', 'secret':'test_key'}
        self.transport.dht = self.dht_mock
        self.transport.market_id = 1
        self.transport.settings = self.settings_mock
        self.db_mock = mock.MagicMock(spec=db_store.Obdb)
        self.db_mock.select_entries.return_value = '6'
        self.test_market = Market(self.transport, self.db_mock)

    def test_init(self):
        self.assertIs(self.test_market.db_connection, self.db_mock)
        self.assertEqual(self.test_market.dht, self.dht_mock)
        self.assertEqual(self.test_market.market_id, 1)
        self.assertEqual(self.test_market.settings, self.settings_mock)

    def test_disable_welcome_screen(self):
        self.assertIs(self.test_market.settings['welcome'], 'enable')
        self.test_market.disable_welcome_screen()
        self.test_market.db_connection.update_entries.assert_called_once_with(
            "settings", {"welcome": "disable"},
            {'market_id': self.transport.market_id})
        self.assertIs(self.test_market.settings['welcome'], 'disable')

    def test_private_key(self):
        self.assertEqual(self.test_market.private_key(), 'test_key')

    def test_generate_new_pubkey(self):
        expected = ('0474089da7ea6382daa65ed8b4af78a8445dc0fa35254a794ac558e5'
                    'dbc1fceb2258abd3c5d8ba5afc67326ed6f5d0a3f1bc455fb7f4ce47'
                    'd26e7f48d56e8caaad')
        self.assertEqual(self.test_market.generate_new_pubkey(4), expected)
        self.test_market.db_connection.insert_entry.assert_called_once_with(
            "keystore", {'contract_id': 4})

    @log_capture()
    def test_get_contracts_empty_contract_body(self, l):
        db_contracts = [{
            'id': 1, 'market_id':1, 'contract_body':'',
            'signed_contract_body':'', 'deleted':0, 'state': '', 'key': ''}]
        expected_contracts = {"contracts": [], "page": 0, "total_contracts": 1}
        self.db_mock.select_entries.return_value = db_contracts
        returned_contracts = self.test_market.get_contracts()
        self.assertEqual(expected_contracts, returned_contracts)
        self.test_market.db_connection.select_entries.assert_any_call(
            "contracts", {"market_id": 1, "deleted": 0}, limit=10,
            limit_offset=(0 * 10))
        self.test_market.db_connection.select_entries.assert_any_call(
            "contracts", {"deleted": "0"})
        l.check(
            ('[1] Market', 'INFO', 'Getting contracts for market: 1'),
            ('[1] Market', 'ERROR', ('Problem loading the contract body JSON:'
                                     ' No JSON object could be decoded'))
        )

    @log_capture()
    def test_get_contracts_contract_body_wrong_format(self, l):
        db_contracts = [{
            'id': 1, 'market_id':1, 'contract_body':'["Wrong", {}]',
            'signed_contract_body':'', 'deleted':0, 'state': '', 'key': ''}]
        expected_contracts = {"contracts": [], "page": 0, "total_contracts": 1}
        self.db_mock.select_entries.return_value = db_contracts
        returned_contracts = self.test_market.get_contracts()
        self.assertEqual(expected_contracts, returned_contracts)
        self.test_market.db_connection.select_entries.assert_any_call(
            "contracts", {"market_id": 1, "deleted": 0}, limit=10,
            limit_offset=(0 * 10))
        self.test_market.db_connection.select_entries.assert_any_call(
            "contracts", {"deleted": "0"})
        l.check(
            ('[1] Market', 'INFO', 'Getting contracts for market: 1'),
            ('[1] Market', 'ERROR', "Malformed contract_body: [u'Wrong', {}]")
        )

    @log_capture()
    def test_get_contracts_contract_field_not_found(self, l):
        db_contracts = [{
            'id': 1, 'market_id':1,
            'contract_body':'{"Unknown": {"title": "D"} }',
            'signed_contract_body':'', 'deleted':0, 'state': '', 'key': ''}]
        expected_contracts = {"contracts": [], "page": 0, "total_contracts": 1}
        self.db_mock.select_entries.return_value = db_contracts
        returned_contracts = self.test_market.get_contracts()
        self.assertEqual(expected_contracts, returned_contracts)
        self.test_market.db_connection.select_entries.assert_any_call(
            "contracts", {"market_id": 1, "deleted": 0}, limit=10,
            limit_offset=(0 * 10))
        self.test_market.db_connection.select_entries.assert_any_call(
            "contracts", {"deleted": "0"})
        l.check(
            ('[1] Market', 'INFO', 'Getting contracts for market: 1'),
            ('[1] Market', 'ERROR', 'Contract field not found in contract_body')
        )

    @log_capture()
    def test_get_contracts_item_delivery_field_not_found(self, l):
        db_contracts = [{
            'id': 1, 'market_id':1, 'contract_body':'{"Contract": {} }',
            'signed_contract_body':'', 'deleted':0, 'state': '', 'key': ''}]
        expected_contracts = {"contracts": [], "page": 0, "total_contracts": 1}
        self.db_mock.select_entries.return_value = db_contracts
        returned_contracts = self.test_market.get_contracts()
        self.assertEqual(expected_contracts, returned_contracts)
        self.test_market.db_connection.select_entries.assert_any_call(
            "contracts", {"market_id": 1, "deleted": 0}, limit=10,
            limit_offset=(0 * 10))
        self.test_market.db_connection.select_entries.assert_any_call(
            "contracts", {"deleted": "0"})
        l.check(
            ('[1] Market', 'INFO', 'Getting contracts for market: 1'),
            ('[1] Market', 'ERROR', 'item_delivery not found in contract_field')
        )

    def test_get_contracts_single_contract_returned(self):
        db_contracts = [{
            'id': 2, 'market_id':1,
            'contract_body':('{"Contract": {"item_delivery":'
                             '{"shipping_price":10}, "item_images":"4",'
                             '"item_price": 11, "item_title":"12",'
                             '"item_desc":"13", "item_condition":"14",'
                             '"item_quantity": "15", "item_remote_images":"16",'
                             '"item_keywords":"17"}}'),
            'signed_contract_body':'5', 'deleted':0, 'state': '', 'key': '3'
        }]
        expected_contracts = {
            'contracts': [{
                'contract_body':{
                    u'Contract':{
                        u'item_delivery':{
                            u'shipping_price':10},
                        u'item_images':u'4', u'item_price': 11,
                        u'item_title':u'12', u'item_desc':u'13',
                        u'item_condition':u'14', u'item_quantity':u'15',
                        u'item_remote_images':u'16',
                        u'item_keywords':u'17'}},
                'key':'3', 'id':2,
                'item_images':u'4', 'signed_contract_body':'5',
                'shipping_price': 10, 'unit_price': 11,
                'deleted':0, 'item_title':u'12',
                'item_desc':u'13', 'item_condition':u'14',
                'item_quantity_available':u'15',
                'item_remote_images':u'16',
                'item_keywords':u'17'}],
            "page": 0, "total_contracts": 1}
        self.db_mock.select_entries.return_value = db_contracts
        returned_contracts = self.test_market.get_contracts()
        self.assertEqual(expected_contracts, returned_contracts)
        self.test_market.db_connection.select_entries.assert_any_call(
            "contracts", {"market_id": 1, "deleted": 0}, limit=10,
            limit_offset=(0 * 10))
        self.test_market.db_connection.select_entries.assert_any_call(
            "contracts", {"deleted": "0"})

    def test_ensure_pubkey_uses_correct_keystore_id(self):
        self.db_mock.select_entries.return_value = '4'
        four = self.test_market.generate_new_pubkey(4)
        self.db_mock.select_entries.return_value = '5'
        five = self.test_market.generate_new_pubkey(5)
        self.assertNotEqual(four, five)

    def test_validate_on_query_myorders(self):
        self.assertTrue(self.test_market.validate_on_query_myorders())

    def test_validate_on_inbox_message(self):
        self.assertTrue(self.test_market.validate_on_inbox_message())

    def test_validate_on_query_listing(self):
        self.assertTrue(self.test_market.validate_on_query_listing())

    def test_validate_on_peer(self):
        self.assertTrue(self.test_market.validate_on_peer())
