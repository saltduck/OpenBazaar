import unittest

from dht import constants, util


class TestUtil(unittest.TestCase):

    """
    Test the utility functions.
    """

    def test_partition(self):
        sequence = list(range(6))
        predicate = lambda n: n % 2 == 0
        even, odd = util.partition(sequence, predicate)

        self.assertEqual(len(even) + len(odd), len(sequence))
        for elem in sequence:
            if predicate(elem):
                self.assertIn(elem, even)
            else:
                self.assertIn(elem, odd)

    @staticmethod
    def _pad_guid(guid):
        return guid.rjust(constants.HEX_NODE_ID_LEN, '0')

    def test_distance_simple(self):
        self.assertEqual(
            util.distance(self._pad_guid('a'), self._pad_guid('a')),
            0
        )

        self.assertEqual(
            util.distance(self._pad_guid('a'), self._pad_guid('b')),
            1
        )

        self.assertEqual(
            util.distance(self._pad_guid('1'), self._pad_guid('4')),
            5
        )

        self.assertEqual(
            util.distance(
                'f' * constants.HEX_NODE_ID_LEN,
                'e' * constants.HEX_NODE_ID_LEN
            ),
            97433442488726861213578988847752201310395502865
        )

    def test_distance_unicode(self):
        self.assertEqual(
            util.distance(self._pad_guid(u"1"), self._pad_guid("4")),
            5
        )
        self.assertEqual(
            util.distance(self._pad_guid("1"), self._pad_guid(u"4")),
            5
        )
        self.assertEqual(
            util.distance(self._pad_guid(u"1"), self._pad_guid(u"4")),
            5
        )

    def test_distance_bad_guid(self):
        self.assertRaises(
            AssertionError,
            util.distance,
            'a',
            'a' * constants.HEX_NODE_ID_LEN
        )

        self.assertRaises(
            AssertionError,
            util.distance,
            'a' * constants.HEX_NODE_ID_LEN,
            'a'
        )

    def test_num_to_guid(self):
        test_tuples = (
            (0, '0000000000000000000000000000000000000000'),
            (42, '000000000000000000000000000000000000002a'),
            (
                2**constants.BIT_NODE_ID_LEN - 1,
                'ffffffffffffffffffffffffffffffffffffffff'
            )
        )

        for num, guid in test_tuples:
            self.assertEqual(util.num_to_guid(num), guid)

    def test_guid_to_num(self):
        test_tuples = (
            (0, '0000000000000000000000000000000000000000'),
            (42, '000000000000000000000000000000000000002a'),
            (
                2**constants.BIT_NODE_ID_LEN - 1,
                'ffffffffffffffffffffffffffffffffffffffff'
            ),
            (
                2**constants.BIT_NODE_ID_LEN - 1,
                'ffffffffffffffffffffffffffffffffffffffffL'
            ),
            (
                2**constants.BIT_NODE_ID_LEN - 1,
                '0xffffffffffffffffffffffffffffffffffffffffL'
            )
        )

        for num, guid in test_tuples:
            self.assertEqual(util.guid_to_num(guid), num)

    def test_random_guid_in_range_is_random(self):
        range_min, range_max = 0, 2**constants.BIT_NODE_ID_LEN
        guid1 = util.random_guid_in_range(range_min, range_max)
        guid2 = util.random_guid_in_range(range_min, range_max)

        # There is a tiny chance that the same guid is returned
        # in consecutive calls, but there is a much higher chance
        # of a bad (i.e non-random) implementation.
        self.assertNotEqual(guid1, guid2)

    def test_random_guid_in_range_is_half_open(self):
        range_min, range_max = 0, 4
        guids = (
            util.random_guid_in_range(range_min, range_max)
            for _ in range(100)
        )
        numbers = tuple(int(guid, base=16) for guid in guids)
        for number in numbers:
            self.assertLessEqual(range_min, number)
            self.assertLess(number, range_max)

        # There is a tiny chance that the guid corresponding
        # to the lower limit is not returned, but there is a
        # much higher chance of a bad implementation.
        self.assertIn(range_min, numbers)


if __name__ == '__main__':
    unittest.main()
