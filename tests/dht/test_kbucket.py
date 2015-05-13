import random
import time
import unittest

from dht import constants, contact, kbucket, util


class TestModuleMisc(unittest.TestCase):

    def test_error(self):
        self.assertTrue(issubclass(kbucket.FullBucketError, Exception))


class TestKBucket(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.range_min = 1
        cls.range_max = 2**constants.BIT_NODE_ID_LEN
        cls.init_contact_count = constants.K - 1
        cls.kbucket_class = kbucket.KBucket

    def setUp(self):
        self.bucket = self._make_kbucket()

    @classmethod
    def _make_kbucket(cls, count=0):
        new_kbucket = cls.kbucket_class(cls.range_min, cls.range_max)

        for i in range(cls.range_min, cls.range_min + count):
            new_kbucket.add_contact(cls._make_contact_from_num(i))

        return new_kbucket

    @staticmethod
    def _make_contact_from_num(i):
        return contact.Contact('123.45.67.89', 12345, util.num_to_guid(i))

    def test_init(self):
        now = int(time.time())
        bucket = self.kbucket_class(1, 2)
        self.assertEqual(bucket.range_min, 1)
        self.assertEqual(bucket.range_max, 2)
        self.assertGreaterEqual(bucket.last_accessed, now)
        self.assertEqual(len(bucket), 0)

    def test_len(self):
        new_contact = self._make_contact_from_num(self.range_max - 1)
        self.bucket.add_contact(new_contact)
        self.assertEqual(len(self.bucket), 1)
        self.bucket.remove_contact(new_contact)
        self.assertEqual(len(self.bucket), 0)

    def test_getitem(self):
        new_contact1 = self._make_contact_from_num(self.range_min)
        new_contact2 = self._make_contact_from_num(self.range_min + 1)
        self.bucket.add_contact(new_contact1)
        self.bucket.add_contact(new_contact2)
        self.assertEqual(self.bucket[0], new_contact1)
        self.assertEqual(self.bucket[1], new_contact2)

    def test_get_existing_contact(self):
        new_contact = self._make_contact_from_num(self.range_max - 1)
        self.bucket.add_contact(new_contact)
        self.assertEqual(
            self.bucket.get_contact(new_contact.guid),
            new_contact,
            'Did not find requested contact {0}.'.format(new_contact.guid)
        )

    def test_get_absent_contact(self):
        absent_guid = util.num_to_guid(self.range_max - 2)
        self.assertIsNone(
            self.bucket.get_contact(absent_guid),
            'Nonexistent contact found.'
        )

    def _test_get_contacts_scenario(self, bucket, request_count, expect_count):
        contacts = bucket.get_contacts(count=request_count)
        contacts_count = len(contacts)
        self.assertEqual(expect_count, contacts_count)

    def test_get_no_contacts_from_empty_bucket(self):
        self._test_get_contacts_scenario(self.bucket, -1, 0)

    def test_get_zero_contacts(self):
        self._test_get_contacts_scenario(self.bucket, 0, 0)

    def test_get_all_available_contacts(self):
        count = constants.K // 2
        bucket = self._make_kbucket(count)
        self._test_get_contacts_scenario(bucket, count, count)

    def test_get_no_more_than_available_contacts(self):
        count = constants.K // 2
        bucket = self._make_kbucket(count)
        self._test_get_contacts_scenario(bucket, count + 1, count)

    def test_get_contacts_excluding_existing(self):
        bucket = self._make_kbucket(constants.K)

        # Pick a random contact to exclude...
        random_contact = random.choice(bucket)
        random_guid = random_contact.guid
        rest_contacts = bucket.get_contacts(excluded_guid=random_guid)

        # ... check it was indeed excluded ...
        self.assertNotIn(random_contact, rest_contacts)

        # ... and ensure no other contact was excluded.
        for other_contact in bucket:
            if other_contact != random_contact:
                self.assertIn(other_contact, rest_contacts)

    def test_get_contacts_excluding_absent(self):
        bucket = self._make_kbucket(constants.K)
        absent_guid = util.num_to_guid(self.range_max - 1)
        try:
            rest_contacts = bucket.get_contacts(excluded_guid=absent_guid)
        except Exception:
            self.fail('Crashed while excluding contact absent from bucket.')
        else:
            self.assertEqual(len(rest_contacts), len(bucket))

    def test_get_contacts_from_tail(self):
        bucket = self._make_kbucket(constants.K)
        contacts = bucket.get_contacts(count=constants.K // 2)
        self.assertEqual(contacts, bucket[-(constants.K // 2):])

    def test_add_new_contact(self):
        new_contact = self._make_contact_from_num(self.range_max - 1)
        prev_count = len(self.bucket)
        try:
            self.bucket.add_contact(new_contact)
        except kbucket.FullBucketError:
            self.fail('Failed to add new contact in non-full bucket.')
            return

        # Assert new contact appears at end of contact list.
        self.assertEqual(
            self.bucket[-1],
            new_contact,
            'New contact is not at end of list'
        )

        # Naively assert the list didn't lose an element by accident.
        cur_count = len(self.bucket)
        self.assertEqual(
            prev_count + 1,
            cur_count,
            'Expected list length: %d\tGot: %d\tInitial: %d' % (
                prev_count + 1,
                cur_count,
                prev_count
            )
        )

    def test_add_existing_contact(self):
        bucket = self._make_kbucket(constants.K)
        new_contact = random.choice(bucket)
        prev_count = len(bucket)
        try:
            bucket.add_contact(new_contact)
        except kbucket.FullBucketError:
            self.fail('Failed to add existing contact in non-full bucket.')
            return

        # Assert new contact appears at end of contact list.
        self.assertEqual(
            bucket[-1],
            new_contact,
            'New contact is not at end of list'
        )

        # Assert the list didn't change size.
        cur_count = len(bucket)
        self.assertEqual(
            prev_count,
            cur_count,
            "Expected list length: %d\tGot: %d\tInitial: %d" % (
                prev_count,
                cur_count,
                prev_count
            )
        )

    def test_add_contact_when_full(self):
        full_bucket = self._make_kbucket(count=constants.K)
        prev_list = full_bucket.get_contacts()

        new_contact = self._make_contact_from_num(self.range_max - 1)
        with self.assertRaises(kbucket.FullBucketError):
            full_bucket.add_contact(new_contact)

        # Assert list is intact despite exception.
        for elem in prev_list:
            self.assertIn(
                elem,
                full_bucket,
                'Contact list was modified before raising exception.'
            )

    def test_remove_contact_existing_contact(self):
        new_contact = self._make_contact_from_num(self.range_max - 1)
        self.bucket.add_contact(new_contact)
        self.bucket.remove_contact(new_contact)
        self.assertNotIn(new_contact, self.bucket)

    def test_remove_contact_existing_guid(self):
        new_contact = self._make_contact_from_num(self.range_max - 1)
        self.bucket.add_contact(new_contact)
        self.bucket.remove_guid(new_contact.guid)
        self.assertNotIn(new_contact, self.bucket)

    def test_remove_absent_contact(self):
        new_contact = self._make_contact_from_num(self.range_max - 1)
        try:
            self.bucket.remove_contact(new_contact.guid)
        except Exception:
            self.fail('Crashed while removing absent contact.')

    def test_remove_absent_guid(self):
        new_contact = self._make_contact_from_num(self.range_max - 1)
        try:
            self.bucket.remove_guid(new_contact.guid)
        except Exception:
            self.fail('Crashed while removing absent guid.')

    @classmethod
    def _make_split_kbucket(cls):
        bucket = cls.kbucket_class(cls.range_min, cls.range_max)

        for i in range(1, constants.K // 2):
            bucket.add_contact(cls._make_contact_from_num(cls.range_min + i))
            bucket.add_contact(cls._make_contact_from_num(cls.range_max - i))
        return bucket

    def test_split_kbucket(self, bucket=None):
        if bucket is None:
            bucket = self._make_split_kbucket()

        all_contacts = bucket.get_contacts()
        r_min, r_max = bucket.range_min, bucket.range_max
        new_bucket = bucket.split_kbucket()

        self.assertEqual(bucket.range_min, r_min)
        self.assertEqual(bucket.range_max, r_min + (r_max - r_min) // 2)
        self.assertEqual(new_bucket.range_min, bucket.range_max)
        self.assertEqual(new_bucket.range_max, r_max)

        for s_contact in all_contacts:
            if bucket.contact_in_range(s_contact):
                self.assertIn(s_contact, bucket)
                self.assertNotIn(s_contact, new_bucket)
            else:
                self.assertNotIn(s_contact, bucket)
                self.assertIn(s_contact, new_bucket)

        return new_bucket

    def test_contact_in_range(self):
        range_min, range_max = 2, 16
        bucket = self.kbucket_class(range_min, range_max)
        low_out, low_in, mid, high_in, high_out = (
            range_min - 1,
            range_min,
            range_min + (range_max - range_min) // 2,
            range_max - 1,
            range_max
        )

        for num in (low_in, mid, high_in):
            new_contact = self._make_contact_from_num(num)
            self.assertTrue(bucket.contact_in_range(new_contact))

        for num in (low_out, high_out):
            new_contact = self._make_contact_from_num(num)
            self.assertFalse(bucket.contact_in_range(new_contact))

    def test_guid_in_range(self):
        range_min, range_max = 2, 16
        bucket = self.kbucket_class(range_min, range_max)
        low_out, low_in, mid, high_in, high_out = (
            range_min - 1,
            range_min,
            range_min + (range_max - range_min) // 2,
            range_max - 1,
            range_max
        )

        for num in (low_in, mid, high_in):
            self.assertTrue(bucket.guid_in_range(util.num_to_guid(num)))

        for num in (low_out, high_out):
            self.assertFalse(bucket.guid_in_range(util.num_to_guid(num)))


class TestCachingKBucket(TestKBucket):

    @classmethod
    def setUpClass(cls):
        super(TestCachingKBucket, cls).setUpClass()
        cls.kbucket_class = kbucket.CachingKBucket

    @classmethod
    def _make_split_kbucket(cls):
        bucket = super(TestCachingKBucket, cls)._make_split_kbucket()
        for i in range(1, constants.K // 2):
            bucket.cache_contact(cls._make_contact_from_num(cls.range_min + i))
            bucket.cache_contact(cls._make_contact_from_num(cls.range_max - i))
        return bucket

    def test_cache_new_contact(self):
        new_contact = self._make_contact_from_num(self.range_max - 1)
        prev_cache = self.bucket.get_cached_contacts()
        self.bucket.cache_contact(new_contact)
        cur_cache = self.bucket.get_cached_contacts()
        self.assertEqual(cur_cache, prev_cache + [new_contact])

    def test_cache_existing_contact(self):
        new_contact1 = self._make_contact_from_num(self.range_max - 1)
        new_contact2 = self._make_contact_from_num(self.range_max - 2)
        self.bucket.cache_contact(new_contact1)
        self.bucket.cache_contact(new_contact2)
        self.bucket.cache_contact(new_contact1)
        self.assertEqual(
            self.bucket.get_cached_contacts(),
            [new_contact2, new_contact1]
        )

    def test_cache_contact_with_full_cache(self):
        for i in range(constants.CACHE_K):
            self.bucket.cache_contact(
                self._make_contact_from_num(self.range_max - i)
            )
        prev_cache = self.bucket.get_cached_contacts()

        over_contact = self._make_contact_from_num(self.range_min)
        self.bucket.cache_contact(over_contact)
        cur_cache = self.bucket.get_cached_contacts()

        self.assertEqual(cur_cache, prev_cache[1:] + [over_contact])

    def test_get_cached_contacts(self):
        new_contact1 = self._make_contact_from_num(self.range_max - 1)
        new_contact2 = self._make_contact_from_num(self.range_max - 2)
        self.bucket.cache_contact(new_contact1)
        self.bucket.cache_contact(new_contact2)
        self.assertEqual(
            self.bucket.get_cached_contacts(),
            [new_contact1, new_contact2]
        )

    def test_remove_contact_replace(self):
        new_contact1 = self._make_contact_from_num(self.range_max - 1)
        new_contact2 = self._make_contact_from_num(self.range_min)
        self.bucket.cache_contact(new_contact1)
        self.bucket.add_contact(new_contact2)
        self.bucket.remove_contact(new_contact2)
        self.assertIn(new_contact1, self.bucket)
        self.assertNotIn(new_contact1, self.bucket.get_cached_contacts())

    def test_remove_guid_replace(self):
        new_contact1 = self._make_contact_from_num(self.range_max - 1)
        new_contact2 = self._make_contact_from_num(self.range_min)
        self.bucket.cache_contact(new_contact1)
        self.bucket.add_contact(new_contact2)
        self.bucket.remove_guid(new_contact2.guid)
        self.assertIn(new_contact1, self.bucket)
        self.assertNotIn(new_contact1, self.bucket.get_cached_contacts())

    def test_split_kbucket(self, bucket=None):
        if bucket is None:
            bucket = self._make_split_kbucket()
        main_contacts = list(bucket)
        cached_contacts = bucket.get_cached_contacts()

        new_bucket = super(TestCachingKBucket, self).test_split_kbucket(bucket)
        for m_contact in main_contacts:
            if bucket.contact_in_range(m_contact):
                self.assertIn(m_contact, bucket)
                self.assertNotIn(m_contact, new_bucket)
            else:
                self.assertNotIn(m_contact, bucket)
                self.assertIn(m_contact, new_bucket)

        cached_contacts1 = bucket.get_cached_contacts()
        cached_contacts2 = new_bucket.get_cached_contacts()
        for c_contact in cached_contacts:
            if bucket.contact_in_range(c_contact):
                self.assertTrue(
                    c_contact in bucket or c_contact in cached_contacts1
                )
                self.assertFalse(
                    c_contact in new_bucket or c_contact in cached_contacts2
                )
            else:
                self.assertFalse(
                    c_contact in bucket or c_contact in cached_contacts1
                )
                self.assertTrue(
                    c_contact in new_bucket or c_contact in cached_contacts2
                )

    def test_fill_from_cache(self):
        for i in range(1, constants.K):
            self.bucket.cache_contact(
                self._make_contact_from_num(self.range_max - i)
            )

        old_main_count = len(self.bucket)
        old_cache_count = len(self.bucket._replacement_cache)

        self.bucket.fill_from_cache()

        main_count = len(self.bucket)
        cache_count = len(self.bucket._replacement_cache)

        self.assertEqual(
            main_count + cache_count,
            old_main_count + old_cache_count,
        )
        self.assertGreater(main_count, old_main_count)

if __name__ == "__main__":
    unittest.main()
