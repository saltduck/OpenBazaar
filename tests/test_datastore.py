import unittest
import UserDict

import mock

from node import datastore, db_store


class TestSqliteDatastore(unittest.TestCase):
    def setUp(self):
        self.db_mock = mock.MagicMock(spec=db_store.Obdb)
        data = {
            'datastore': [
                {'key': 'Zurich'.encode('hex')},
                {'key': 'CH'.encode('hex')}
                ]
        }
        self.db_mock.select_entries.side_effect = data.__getitem__
        self.sqlite_datastore = datastore.SqliteDataStore(self.db_mock)

    def test_init(self):
        self.assertIs(self.sqlite_datastore.db_connection, self.db_mock)
        self.assertIsInstance(self.sqlite_datastore, UserDict.DictMixin)

    def test_keys(self):
        keys = self.sqlite_datastore.keys()
        self.assertEqual(len(keys), 2)
        self.assertIn('Zurich', keys)
        self.assertIn('CH', keys)

    def test_get_last_published(self):
        pass

    def test_get_original_publisher_id(self):
        pass

    def test_get_original_publish_time(self):
        pass

    def test_set_item(self):
        pass
