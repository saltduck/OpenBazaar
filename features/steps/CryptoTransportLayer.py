#pylint: disable=function-redefined
from behave import given, then, when
from tornado import ioloop

from node.db_store import Obdb
from node.setup_db import setup_db
from node.openbazaar_daemon import OpenBazaarContext
from node.transport import CryptoTransportLayer
from features.test_util import ip_address, nickname, get_db_path

PORT = 12345


def create_layers(context, num_layers):
    layers = []

    for i in range(num_layers):
        # dev_mode is True because otherwise the layer's ip is set to the
        # public ip of the node
        ob_ctx = OpenBazaarContext.create_default_instance()
        ob_ctx.dev_mode = True
        ob_ctx.server_ip = ip_address(i)
        ob_ctx.server_port = PORT
        db_path = get_db_path(i)
        setup_db(db_path, ob_ctx.disable_sqlite_crypt)
        layers.append(CryptoTransportLayer(ob_ctx, Obdb(db_path)))
    context.layers = layers


@given('{num_layers} layers')
def step_impl(context, num_layers):
    create_layers(context, int(num_layers))


@when('layer {i} connects to layer {j}')
def step_impl(context, i, j):
    i = int(i)
    j = int(j)
    i_layer = context.layers[i]
    j_layer = context.layers[j]

    j_layer.join_network([])

    def callback(msg):
        ioloop.IOLoop.current().stop()

    i_layer.join_network([ip_address(j)], callback=callback)
    ioloop.IOLoop.current().start()


@then('layer {i} is aware of layer {j}')
def step_impl(context, i, j):
    i = int(i)
    j = int(j)
    i_layer = context.layers[i]
    j_layer = context.layers[j]

    known_node = (ip_address(j), PORT, j_layer.guid, nickname(j))
    assert known_node in i_layer.dht.knownNodes

    # j is not necessarily in the database of i
    # db_peers = i_layer._db.selectEntries("peers")
    # assert(j_layer._uri in map(lambda x: x['uri'], known_peers))

    # j is not necessarily in activePeers of i
    # assert(j_layer._guid in map(lambda x: x._guid, i_layer.dht._activePeers))

    # j is not necessarily in peers of i
    # assert(j_layer._uri in i_layer._peers)
