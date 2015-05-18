import collections


class Contact(collections.Hashable):
    """
    A node in the DHT.

    Contains all information specified by the Kademlia protocol
    (aka: IP, PORT, GUID).
    """
    def __init__(self, ip, port, guid):
        """
        Make a new Contact.

        Args:
            ip: The IP of the Contact as a string or unicode. It may
                be an IPv4 or an IPv6.
            port: The port of the Contact as an integer
            guid: The unique ID of the Contact as a hex string of
                proper length (see constants module)
        """
        self.ip = ip
        self.port = port
        self.guid = guid

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.guid == other.guid
        return NotImplemented

    def __hash__(self):
        return hash(self.guid)

    def __repr__(self):
        return 'Contact({0}, {1}, {2})'.format(self.ip, self.port, self.guid)
