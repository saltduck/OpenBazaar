import unittest
from node.openbazaar_daemon import OpenBazaarContext
import mock

from node import protocol, transport


def get_mock_open_bazaar_context():
    return OpenBazaarContext(None,
                             my_market_ip='localhost',
                             my_market_port=12345,
                             http_ip='localhost',
                             http_port=-1,
                             db_path='db/ob.db',
                             log_path=None,
                             log_level=10,
                             market_id=1,
                             bm_user=None,
                             bm_pass=None,
                             bm_port=-1,
                             seed_peers=[],
                             seed_mode=False,
                             dev_mode=False,
                             dev_nodes=-1,
                             disable_upnp=True,
                             disable_stun_check=True,
                             disable_open_browser=True,
                             disable_sqlite_crypt=False,
                             enable_ip_checker=False)


class TestTransportLayerCallbacks(unittest.TestCase):
    """Test the callback features of the TransportLayer class."""

    def setUp(self):
        # For testing sections
        self.callback1 = mock.Mock()
        self.callback2 = mock.Mock()
        self.callback3 = mock.Mock()
        self.validator1 = mock.Mock()
        self.validator2 = mock.Mock()
        self.validator3 = mock.Mock()

        ob_ctx = get_mock_open_bazaar_context()
        guid = 1
        nickname = None

        self.tl = transport.TransportLayer(ob_ctx, guid, nickname)
        self.tl.add_callback('section_one', {'cb': self.callback1, 'validator_cb': self.validator1})
        self.tl.add_callback('section_one', {'cb': self.callback2, 'validator_cb': self.validator2})
        self.tl.add_callback('all', {'cb': self.callback3, 'validator_cb': self.validator3})

        # For testing validators
        self.callback4 = mock.Mock()
        self.callback5 = mock.Mock()
        self.validator4 = mock.Mock(return_value=True)
        self.validator5 = mock.Mock(return_value=False)
        self.tl.add_callback('section_two', {'cb': self.callback4, 'validator_cb': self.validator4})
        self.tl.add_callback('section_two', {'cb': self.callback5, 'validator_cb': self.validator5})

    def _assert_called(self, one, two, three):
        self.assertEqual(self.callback1.call_count, one)
        self.assertEqual(self.callback2.call_count, two)
        self.assertEqual(self.callback3.call_count, three)

    def test_fixture(self):
        self._assert_called(0, 0, 0)

    def test_callbacks(self):
        self.tl.trigger_callbacks('section_one', None)
        self._assert_called(1, 1, 1)

    def test_all_callback(self):
        self.tl.trigger_callbacks('section_with_no_register', None)
        self._assert_called(0, 0, 1)

    def test_validators(self):
        self.tl.trigger_callbacks('section_two', None)
        self.assertEqual(self.validator4.call_count, 1)
        self.assertEqual(self.validator5.call_count, 1)
        self.assertEqual(self.callback4.call_count, 1)
        self.assertEqual(self.callback5.call_count, 0)


class TestTransportLayerMessageHandling(unittest.TestCase):

    def setUp(self):
        ob_ctx = get_mock_open_bazaar_context()
        guid = 1
        nickname = None
        self.tl = transport.TransportLayer(ob_ctx, guid, nickname)

    def test_on_message_ok(self):
        """OK message should trigger no callbacks."""
        self.tl.trigger_callbacks = mock.MagicMock(
            side_effect=AssertionError()
        )
        self.tl._on_message(protocol.ok())

    def test_on_message_not_ok(self):
        """
        Any non-OK message should cause trigger_callbacks to be called with
        the type of message and the message object (dict).
        """
        data = protocol.shout({})
        self.tl.trigger_callbacks = mock.MagicMock()
        self.tl._on_message(data)
        self.tl.trigger_callbacks.assert_called_with(data['type'], data)

    def test_on_raw_message_hello_no_uri(self):
        """A hello message with no uri should not add a peer."""
        self.tl._on_raw_message(protocol.hello_request({}))
        self.assertEqual(0, len(self.tl.peers))

    def test_on_raw_message_hello_with_uri(self):
        """A hello message with a uri should result in a new peer."""
        request = protocol.hello_request({
            'uri': 'tcp://localhost:12345'
        })
        self.tl._on_raw_message(request)
        self.assertEqual(1, len(self.tl.peers))


class TestTransportLayerProfile(unittest.TestCase):

    def test_get_profile(self):
        ob_ctx = get_mock_open_bazaar_context()
        ob_ctx.my_market_ip = '1.1.1.1'
        guid = 1
        nickname = None
        tl = transport.TransportLayer(ob_ctx, guid, nickname)
        self.assertEqual(
            tl.get_profile(),
            protocol.hello_request({
                'uri': 'tcp://1.1.1.1:12345'
            })
        )

if __name__ == "__main__":
    unittest.main()
