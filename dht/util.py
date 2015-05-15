"""
Collection of utility functions not bound to a particular class.
"""

import random

from dht import constants


class BadGUIDError(Exception):

    """Exception raised on detecting a bad guid."""

    pass


def partition(sequence, predicate):
    """
    Partition the sequence into two lists, according to the
    function provided.

    Args:
        sequence: A sequence of elements.
        predicate: A function of one argument, returning bool.

    Returns:
        A tuple of lists, where the first list contains all
        elements that pass the test, and the second list all
        other elements.
    """
    list1, list2 = [], []
    for elem in sequence:
        if predicate(elem):
            list1.append(elem)
        else:
            list2.append(elem)
    return list1, list2


def distance(guid1, guid2):
    """
    Calculate the XOR result between two guids, which represents
    the distance between these guids in the Kademlia protocol.

    Args:
        guid1, guid2: The first and second guid, respectively,
            as strings or unicodes, in hexadecimal.

    Returns:
        XOR of the integers corresponding to the guids.

    Raises:
        BadGUIDError: Some guid was of improper length.
    """
    if len(guid1) != constants.HEX_NODE_ID_LEN:
        raise BadGUIDError('guid of improper length: {0}'.format(guid1))
    if len(guid2) != constants.HEX_NODE_ID_LEN:
        raise BadGUIDError('guid of improper length: {0}'.format(guid2))

    return int(guid1, base=16) ^ int(guid2, base=16)


def num_to_guid(num):
    """
    Converts an integer to a DHT guid.

    It is the caller's responsibility to ensure the resulting
    guid falls in the ID space.

    Args:
        num: The integer to convert.

    Returns:
        A string in hexadecimal, corresponding to the number given.
    """
    guid = hex(num).lstrip('0x').rstrip('L')
    # Pad to proper length.
    return guid.rjust(constants.HEX_NODE_ID_LEN, '0')

def guid_to_num(guid):
    """
    Convert a DHT guid to an integer.

    Args:
        guid: The guid to convert, as a string or unicode, in
            hexadecimal.

    Returns:
        An integer corresponding to the DHT guid given.
    """
    return int(guid.rstrip('L'), base=16)

def random_guid_in_range(range_min, range_max):
    """
    Get a random guid from a half-open range of the ID space.

    Args:
        range_min, range_max: The lower and upper limit
            of the target (half-open) range, as integers.

    Returns:
        A random guid that falls inside the range given.
    """
    random_int = random.randrange(range_min, range_max)
    return num_to_guid(random_int)
