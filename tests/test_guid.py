import unittest

from node import guid


class TestGUIDMixin(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.guid = "42"
        cls.alt_guid = "43"
        cls.uguid = unicode(cls.guid)
        cls.alt_uguid = unicode(cls.alt_guid)

    def test_init(self):
        guid_mixin_1 = guid.GUIDMixin(self.guid)
        self.assertEqual(guid_mixin_1.guid, self.guid)

        guid_mixin_2 = guid.GUIDMixin(self.uguid)
        self.assertEqual(guid_mixin_2.guid, self.uguid)

    def _test_eq_true_scenario(self, guid1, guid2):
        guid_mixin_1 = guid.GUIDMixin(guid1)
        guid_mixin_2 = guid.GUIDMixin(guid1)
        guid_mixin_3 = guid.GUIDMixin(guid2)

        self.assertIsNot(guid_mixin_1, guid_mixin_2, "Separate instantiations produce same objects.")

        self.assertEqual(guid_mixin_1, guid_mixin_2, "GUIDMixin unequal to same GUIDMixin.")
        self.assertEqual(guid_mixin_1, guid1, "GUIDMixin unequal to own GUID.")
        self.assertEqual(
            guid_mixin_1, guid_mixin_3, "GUIDMixin unequal to string-equivalent GUIDMixin."
        )

    def _test_eq_false_scenario(self, guid1, guid2):
        guid_mixin_1 = guid.GUIDMixin(guid1)
        guid_mixin_2 = guid.GUIDMixin(guid2)
        self.assertNotEqual(guid_mixin_1, guid_mixin_2, "GUIDMixin equal to different GUIDMixin.")
        self.assertNotEqual(guid_mixin_1, guid2, "GUIDMixin equal to different GUID.")

    def test_eq_(self):
        self._test_eq_true_scenario(self.guid, self.uguid)
        self._test_eq_true_scenario(self.uguid, self.guid)

        self._test_eq_false_scenario(self.guid, self.alt_guid)
        self._test_eq_false_scenario(self.guid, self.alt_uguid)
        self._test_eq_false_scenario(self.uguid, self.alt_guid)
        self._test_eq_false_scenario(self.uguid, self.alt_uguid)

    def test_hash(self):
        guid_mixin_1 = guid.GUIDMixin(self.guid)
        self.assertEqual(hash(guid_mixin_1), hash(self.guid))
        self.assertEqual(hash(guid_mixin_1), hash(self.uguid))

        guid_mixin_2 = guid.GUIDMixin(self.uguid)
        self.assertEqual(hash(guid_mixin_2), hash(self.guid))
        self.assertEqual(hash(guid_mixin_2), hash(self.uguid))

    def test_repr(self):
        guid_mixin_1 = guid.GUIDMixin(self.guid)
        self.assertEqual(guid_mixin_1.__repr__(), str(guid_mixin_1))

        guid_mixin_2 = guid.GUIDMixin(self.uguid)
        self.assertEqual(guid_mixin_2.__repr__(), str(guid_mixin_2))

if __name__ == "__main__":
    unittest.main()
