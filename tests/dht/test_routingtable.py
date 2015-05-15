import unittest

from dht import constants, contact, kbucket, routingtable, util

class TestRoutingTable(unittest.TestCase):

    """Test implementation of RoutingTable."""

    @classmethod
    def setUpClass(cls):
        cls.range_min = 0
        cls.range_max = 2**constants.BIT_NODE_ID_LEN
        cls.own_num_guid = 1
        cls.own_guid = util.num_to_guid(cls.own_num_guid)
        cls.bad_guid = 'f' * (constants.HEX_NODE_ID_LEN + 1)
        cls.bad_contact = contact.Contact('123.45.67.89', 12345, cls.bad_guid)

    @staticmethod
    def _make_contact_from_num(i):
        return contact.Contact('123.45.67.89', 12345, util.num_to_guid(i))

    def setUp(self):
        self.rt = routingtable.RoutingTable(self.own_guid, 42)

    def test_getitem(self):
        bucket = self.rt[0]
        self.assertIsInstance(bucket, kbucket.CachingKBucket)
        self.assertEqual(bucket.range_min, self.range_min)
        self.assertEqual(bucket.range_max, self.range_max)

    def test_init(self):
        self.assertEqual(self.rt.own_guid, self.own_guid)

        self.assertEqual(len(self.rt), 1)
        self.assertEqual(self.rt[0].range_min, self.range_min)
        self.assertEqual(self.rt[0].range_max, self.range_max)

    def test_add_new_contact(self):
        new_contact = self._make_contact_from_num(self.range_max - 1)
        self.rt.add_contact(new_contact)
        self.assertEqual(len(self.rt), 1)
        self.assertEqual(list(self.rt[0]), [new_contact])

    def test_add_self_contact(self):
        self_contact = contact.Contact('123.45.67.89', 12345, self.own_guid)
        self.rt.add_contact(self_contact)
        self.assertIsNone(self.rt.get_contact(self.own_guid))
        self.assertEqual(len(self.rt), 1)
        self.assertEqual(list(self.rt[0]), [])

    def test_add_existing_contact_in_full_bucket(self):
        for i in range(constants.K):
            self.rt.add_contact(
                self._make_contact_from_num(self.own_num_guid + i + 1)
            )

        self.rt.add_contact(self._make_contact_from_num(self.own_num_guid + 1))
        self.assertEqual(len(self.rt), 1)
        self.assertEqual(len(self.rt[0]), constants.K)

    def test_add_new_contact_and_split(self):
        # Add K contacts that belong to the same bucket as own_guid
        base = self.own_num_guid + 1
        for i in range(constants.K):
            self.rt.add_contact(
                self._make_contact_from_num(base + i)
            )

        new_contact = self._make_contact_from_num(self.range_max - 1)
        self.rt.add_contact(new_contact)

        self.assertEqual(
            len(self.rt),
            2,
            'Overflowing KBucket containing own_guid was not split properly.'
        )
        self.assertEqual(
            len(self.rt[0]) + len(self.rt[1]),
            constants.K + 1,
            'Contacts not preserved during KBucket split.'
        )
        self.assertEqual(
            self.rt[0].range_max,
            self.rt[1].range_min,
            'ID spaces of consecutive KBuckets not alinged properly.'
        )

    def test_add_new_contact_and_cache(self):
        # Add K + 1 contacts to initial KBucket, to force a split.
        base = util.guid_to_num(self.own_guid) + 1
        for i in range(constants.K):
            self.rt.add_contact(
                self._make_contact_from_num(base + i)
            )
        self.rt.add_contact(self._make_contact_from_num(self.range_max - 1))

        # Create a guid that is at maximal distance from own_guid,
        # thus must be at a different bucket.
        self.assertEqual(len(self.rt), 2)
        max_base = (2**constants.BIT_NODE_ID_LEN - 1) ^ self.own_num_guid
        self.assertTrue(self.rt[0].guid_in_range(self.own_guid))
        self.assertTrue(self.rt[1].guid_in_range(util.num_to_guid(max_base)))

        # Add contacts to the other KBucket, until it is full.
        for i in range(constants.K):
            if len(self.rt[1]) == constants.K:
                break
            self.rt.add_contact(
                self._make_contact_from_num(max_base - i)
            )

        # Create and add a contact that is in the range of the other
        # KBucket.
        new_contact = self._make_contact_from_num(max_base - constants.K)
        self.rt.add_contact(new_contact)

        self.assertEqual(
            len(self.rt),
            2,
            'A KBucket not containing own_guid was split.'
        )

        # Assert the new contact was cached properly.
        self.assertNotIn(new_contact, self.rt[0])
        self.assertNotIn(new_contact, self.rt[1])
        self.assertEqual([], self.rt[0].get_cached_contacts())
        self.assertEqual([new_contact], self.rt[1].get_cached_contacts())

    def test_add_contact_max_recursion(self):
        # Add K + 1 contacts that are so close together and to
        # own_guid, that they force recursive bucket splits.
        base = util.guid_to_num(self.own_guid) + 1
        for i in range(constants.K + 1):
            self.rt.add_contact(
                self._make_contact_from_num(base + i)
            )

        # The actual number of KBuckets created is dependend upon K,
        # so this test will probably break if K changes. In such a case,
        # please update the test.
        self.assertEqual(len(self.rt), 157)

    def test_get_existing_contact(self):
        new_contact = self._make_contact_from_num(self.range_max - 1)
        self.rt.add_contact(new_contact)
        self.assertEqual(self.rt.get_contact(new_contact.guid), new_contact)

    def test_get_absent_contact(self):
        new_guid = util.num_to_guid(self.range_max - 1)
        self.assertIsNone(self.rt.get_contact(new_guid))

    def test_remove_existing_contact(self):
        new_contact = self._make_contact_from_num(self.range_max - 1)
        self.rt.add_contact(new_contact)
        self.rt.remove_contact(new_contact)
        self.assertNotIn(new_contact, self.rt[0])

    def test_remove_absent_contact(self):
        absent_contact = self._make_contact_from_num(self.range_max - 1)
        # Removing an absent contact shouldn't raise an error.
        try:
            self.rt.remove_contact(absent_contact)
        except Exception:
            self.fail('RoutingTable crashed on removing absent contact.')

    def test_remove_existing_guid(self):
        new_contact = self._make_contact_from_num(self.range_max - 1)
        self.rt.add_contact(new_contact)
        self.rt.remove_guid(new_contact.guid)
        self.assertNotIn(new_contact, self.rt[0])

    def test_remove_absent_guid(self):
        absent_guid = util.num_to_guid(self.range_max - 1)
        # Removing an absent guid shouldn't raise an error.
        try:
            self.rt.remove_guid(absent_guid)
        except Exception:
            self.fail('RoutingTable crashed on removing absent contact.')

    def _make_rt_with_n_buckets(self, n):
        rt = routingtable.RoutingTable(self.own_guid, 42)
        # Fill the first Kbucket and cause it to split. Since all
        # contacts are near the high end, but own_guid is near the
        # low end, all contacts are put in the new KBucket, leaving
        # the original KBucket empty. We can then force the first
        # KBucket to split N times by adding another N contacts.
        for _ in range(n - 1):
            range_max = rt[0].range_max
            for i in range(constants.K):
                rt.add_contact(
                    self._make_contact_from_num(range_max - 1 - i)
                )
            rt.add_contact(
                self._make_contact_from_num(range_max - 1 - constants.K)
            )
        self.assertEqual(len(rt), n)
        return rt

    def test_find_close_nodes_from_single_kbucket(self):
        rt = self._make_rt_with_n_buckets(3)
        mid_bucket = rt[1]
        self.assertEqual(len(mid_bucket), constants.K)

        r_guid = util.random_guid_in_range(
            mid_bucket.range_min,
            mid_bucket.range_max
        )
        node_list = rt.find_close_nodes(r_guid)
        self.assertEqual(len(node_list), constants.K)
        for node in node_list:
            self.assertIn(node, mid_bucket)

    def test_find_close_nodes_except_sender_guid(self):
        rt = self._make_rt_with_n_buckets(3)
        sender_num_guid = rt[0].range_min
        sender_contact = self._make_contact_from_num(sender_num_guid)
        rt.add_contact(sender_contact)
        self.assertIn(sender_contact, rt[0])

        r_guid = util.num_to_guid(sender_num_guid + 1)
        node_list = rt.find_close_nodes(
            r_guid,
            sender_guid=sender_contact.guid
        )
        self.assertEqual(len(node_list), constants.K)
        self.assertNotIn(sender_contact, node_list)

    def test_find_close_nodes_with_count(self):
        rt = self._make_rt_with_n_buckets(3)
        mid_bucket = rt[1]
        self.assertEqual(len(mid_bucket), constants.K)

        r_guid = util.random_guid_in_range(
            mid_bucket.range_min,
            mid_bucket.range_max
        )
        node_list = rt.find_close_nodes(r_guid, count=2)
        self.assertEqual(len(node_list), 2)
        for node in node_list:
            self.assertIn(node, mid_bucket)

    def test_find_close_nodes_from_many_buckets(self):
        rt = self._make_rt_with_n_buckets(3)
        self.assertLess(len(rt[0]), constants.K)
        self.assertEqual(len(rt[1]), constants.K)

        r_guid = util.random_guid_in_range(rt[0].range_min, rt[0].range_max)
        node_list = rt.find_close_nodes(r_guid)
        self.assertEqual(len(node_list), constants.K)
        for node in node_list:
            self.assertTrue(node in rt[0] or node in rt[1])

    def test_get_refresh_list_noforce(self):
        now = util.now()
        minimal_bad_timestamp = now - constants.REFRESH_TIMEOUT

        rt = self._make_rt_with_n_buckets(5)
        stale_idxs = (0, 3)
        for idx in stale_idxs:
            rt[idx].last_accessed = minimal_bad_timestamp

        refresh_list = sorted(rt.get_refresh_list())
        self.assertEqual(len(refresh_list), 2)
        self.assertTrue(rt[0].guid_in_range(refresh_list[0]))
        self.assertTrue(rt[3].guid_in_range(refresh_list[1]))

    def test_get_refresh_list_force(self):
        rt = self._make_rt_with_n_buckets(5)
        refresh_list = sorted(rt.get_refresh_list(force=True))

        self.assertEqual(len(refresh_list), 5)
        for bucket, guid in zip(rt, refresh_list):
            self.assertTrue(bucket.guid_in_range(guid))

    # Tests for out-of-range contacts/guids
    def test_get_contact_out_of_range(self):
        with self.assertRaises(util.BadGUIDError):
            self.rt.get_contact(self.bad_guid)

    def test_add_contact_out_of_range(self):
        with self.assertRaises(util.BadGUIDError):
            self.rt.add_contact(self.bad_contact)

    def test_remove_contact_out_of_range(self):
        with self.assertRaises(util.BadGUIDError):
            self.rt.add_contact(self.bad_contact)

    def test_remove_guid_out_of_range(self):
        with self.assertRaises(util.BadGUIDError):
            self.rt.get_contact(self.bad_guid)

    def test_find_close_nodes_out_of_range(self):
        with self.assertRaises(util.BadGUIDError):
            self.rt.find_close_nodes(self.bad_guid)

if __name__ == "__main__":
    unittest.main()
