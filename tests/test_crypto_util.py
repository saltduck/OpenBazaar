import unittest

from bitcoin import main as arithmetic

from node import crypto_util


class TestCryptoUtil(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.privkey_hex = (
            'e9873d79c6d87dc0fb6a5778633389f4453213303da61f20bd67fc233aa33262'
        )
        cls.privkey_bin = crypto_util.privkey_to_pyelliptic(cls.privkey_hex)

        cls.pubkey_hex = arithmetic.privkey_to_pubkey(cls.privkey_hex)
        cls.pubkey_bin = crypto_util.pubkey_to_pyelliptic(cls.pubkey_hex)
        cls.pubkey_hex_strip = cls.pubkey_hex[2:]

        cls.plaintext = "YELLOW SUBMARINE"

    def test_exported_names(self):
        self.assertEqual('secp256k1', crypto_util.BTC_CURVE)
        self.assertEqual('02ca', crypto_util.BTC_CURVE_OPENSSL_ID_HEX)
        self.assertEqual(32, crypto_util.BTC_EC_POINT_LENGTH)
        self.assertEqual('0020', crypto_util.BTC_EC_POINT_LENGTH_HEX)

    def test_pubkey_to_pyelliptic(self):
        pubkey_bin_fmt = crypto_util.pubkey_to_pyelliptic(self.pubkey_hex)

        point_len = crypto_util.BTC_EC_POINT_LENGTH
        header_bin = crypto_util.BTC_CURVE_OPENSSL_ID_HEX.decode('hex')
        length_bin = crypto_util.BTC_EC_POINT_LENGTH_HEX.decode('hex')
        pubkey_bin = arithmetic.changebase(
            self.pubkey_hex_strip, 16, 256, minlen=2*point_len
        )

        self.assertEqual(pubkey_bin_fmt[:2], header_bin)
        self.assertEqual(pubkey_bin_fmt[2:4], length_bin)
        self.assertEqual(pubkey_bin_fmt[4:4+point_len], pubkey_bin[:point_len])
        self.assertEqual(pubkey_bin_fmt[4+point_len:6+point_len], length_bin)
        self.assertEqual(pubkey_bin_fmt[6+point_len:], pubkey_bin[point_len:])

    def test_privkey_to_pyelliptic(self):
        privkey_bin_fmt = crypto_util.privkey_to_pyelliptic(self.privkey_hex)

        header_bin = crypto_util.BTC_CURVE_OPENSSL_ID_HEX.decode('hex')
        length_bin = crypto_util.BTC_EC_POINT_LENGTH_HEX.decode('hex')
        privkey_bin = arithmetic.changebase(
            self.privkey_hex, 16, 256, minlen=crypto_util.BTC_EC_POINT_LENGTH
        )

        self.assertEqual(privkey_bin_fmt[:2], header_bin)
        self.assertEqual(privkey_bin_fmt[2:4], length_bin)
        self.assertEqual(privkey_bin_fmt[4:], privkey_bin)

    def _init_cryptors(self):
        self.pub_cryptor = crypto_util.Cryptor(pubkey_hex=self.pubkey_hex)
        self.priv_cryptor = crypto_util.Cryptor(privkey_hex=self.privkey_hex)
        self.dual_cryptor = crypto_util.Cryptor(
            pubkey_hex=self.pubkey_hex,
            privkey_hex=self.privkey_hex
        )

    def test_init(self):
        self._init_cryptors()
        self.assertFalse(self.pub_cryptor.has_privkey)
        self.assertTrue(self.priv_cryptor.has_privkey)
        self.assertTrue(self.dual_cryptor.has_privkey)
        self.assertRaises(ValueError, crypto_util.Cryptor)

    def test_get_pubkey(self):
        self._init_cryptors()
        self.assertEqual(self.pub_cryptor.get_pubkey(), self.pubkey_bin)
        self.assertEqual(self.priv_cryptor.get_pubkey(), self.pubkey_bin)
        self.assertEqual(self.dual_cryptor.get_pubkey(), self.pubkey_bin)

    def test_get_privkey(self):
        self._init_cryptors()
        self.assertIsNone(self.pub_cryptor.get_privkey())
        self.assertEqual(self.priv_cryptor.get_privkey(), self.privkey_bin)
        self.assertEqual(self.dual_cryptor.get_privkey(), self.privkey_bin)

    def test_encrypt_decrypt(self):
        self._init_cryptors()

        ciphertext1 = self.pub_cryptor.encrypt(self.plaintext)
        ciphertext2 = self.priv_cryptor.encrypt(self.plaintext)
        ciphertext3 = self.dual_cryptor.encrypt(self.plaintext)

        self.assertRaises(
            RuntimeError,
            self.pub_cryptor.decrypt,
            ciphertext1
        )
        self.assertEqual(self.plaintext, self.priv_cryptor.decrypt(ciphertext1))
        self.assertEqual(self.plaintext, self.priv_cryptor.decrypt(ciphertext2))
        self.assertEqual(self.plaintext, self.priv_cryptor.decrypt(ciphertext3))

        self.assertEqual(self.plaintext, self.dual_cryptor.decrypt(ciphertext1))
        self.assertEqual(self.plaintext, self.dual_cryptor.decrypt(ciphertext2))
        self.assertEqual(self.plaintext, self.dual_cryptor.decrypt(ciphertext3))

        bad_ciphertext = ciphertext1[:-4] + "0123"
        self.assertRaises(
            RuntimeError, self.priv_cryptor.decrypt, bad_ciphertext
        )
        self.assertRaises(
            RuntimeError, self.dual_cryptor.decrypt, bad_ciphertext
        )

    def test_sign_verify(self):
        self._init_cryptors()

        plain_sig1 = self.priv_cryptor.sign(self.plaintext)
        plain_sig2 = self.dual_cryptor.sign(self.plaintext)
        self.assertRaises(
            RuntimeError,
            self.pub_cryptor.sign,
            self.plaintext
        )

        ciphertext = self.pub_cryptor.encrypt(self.plaintext)
        crypto_sig1 = self.priv_cryptor.sign(ciphertext)
        crypto_sig2 = self.dual_cryptor.sign(ciphertext)

        self.assertTrue(self.pub_cryptor.verify(plain_sig1, self.plaintext))
        self.assertTrue(self.pub_cryptor.verify(plain_sig2, self.plaintext))
        self.assertTrue(self.pub_cryptor.verify(crypto_sig1, ciphertext))
        self.assertTrue(self.pub_cryptor.verify(crypto_sig2, ciphertext))

        self.assertTrue(self.priv_cryptor.verify(plain_sig1, self.plaintext))
        self.assertTrue(self.priv_cryptor.verify(plain_sig2, self.plaintext))
        self.assertTrue(self.priv_cryptor.verify(crypto_sig1, ciphertext))
        self.assertTrue(self.priv_cryptor.verify(crypto_sig2, ciphertext))

        self.assertTrue(self.dual_cryptor.verify(plain_sig1, self.plaintext))
        self.assertTrue(self.dual_cryptor.verify(plain_sig2, self.plaintext))
        self.assertTrue(self.dual_cryptor.verify(crypto_sig1, ciphertext))
        self.assertTrue(self.dual_cryptor.verify(crypto_sig2, ciphertext))


if __name__ == "__main__":
    unittest.main()
