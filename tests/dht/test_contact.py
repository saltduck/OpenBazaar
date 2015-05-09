import unittest

from dht import contact


class TestContact(unittest.TestCase):
    """
    Test the API of dht.contact.
    """
    @classmethod
    def setUpClass(cls):
        cls.guid1 = '1' * 40
        cls.guid2 = 'f' * 40
        cls.ipv4 = '123.45.67.89'
        cls.ipv6 = '2001:db8:85a3::8a2e:370:7334'
        cls.port1 = 12345
        cls.port2 = 12346

    def _test_init_scenario(self, ip, port, guid):
        contact1 = contact.Contact(ip, port, guid)
        self.assertEqual(contact1.ip, ip)
        self.assertEqual(contact1.port, port)
        self.assertEqual(contact1.guid, guid)

    def test_init_classic(self):
        self._test_init_scenario(self.ipv4, self.port1, self.guid1)

    def test_init_unicode(self):
        self._test_init_scenario(self.ipv4, self.port1, unicode(self.guid1))

    def test_init_ipv6(self):
        self._test_init_scenario(self.ipv6, self.port1, self.guid1)

    def test_eq_hash(self):
        c1 = contact.Contact(self.ipv4, self.port1, self.guid1)
        c2 = contact.Contact(self.ipv6, self.port2, self.guid1)
        self.assertIsNot(c1, c2)
        self.assertEqual(c1, c2)
        self.assertEqual(hash(c1), hash(c2))

    def test_uneq(self):
        c1 = contact.Contact(self.ipv4, self.port1, self.guid1)
        c2 = contact.Contact(self.ipv4, self.port1, self.guid2)
        self.assertNotEqual(c1, c2)

    def test_repr(self):
        c1 = contact.Contact(self.ipv4, self.port1, self.guid1)
        cr = repr(c1)
        self.assertEqual(
            cr,
            'Contact({0}, {1}, {2})'.format(self.ipv4, self.port1, self.guid1)
        )


if __name__ == "__main__":
    unittest.main()
