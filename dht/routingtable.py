"""
Implementation of a Kademlia routing table.

Classes:
    RoutingTable
"""

import collections
import logging

from dht import constants, kbucket, util


class RoutingTable(collections.Sequence):

    """
    This class implements a Kademlia routing table.

    The implementation consists of a list of KBuckets, where each
    KBucket contains nodes with common GUID prefixes (i.e nodes that
    are `close`, per the Kademlia metric). Each KBucket covers a
    half-open range of ID space, and together all of the KBuckets
    cover the entire ID space, without any overlaps. It is intended
    that consecutive KBuckets cover adjacent ranges in the ID space;
    KBuckets at higher indexes cover ranges further away from 0.

    Note: This implementation splits and adds KBuckets on-demand, as
    described in section 2.4 of the 13-page version of the Kademlia
    paper[1]. It also uses the contact accounting optimization specified
    in section 4.1 of the said paper (optimized node accounting without
    PINGs). This results in much less network traffic, at the expense of
    some memory.

    [1]: http://pdos.csail.mit.edu/~petar/papers/maymounkov-kademlia-lncs.pdf
    """

    def __init__(self, own_guid, market_id):
        """
        Initialize a new RoutingTable.

        Args:
            own_guid: The guid of the node to which this routing
                table belongs, as a string or unicode, in hexadecimal.
            market_id: The integer id of the market related to this
                table, strictly for logging purposes.
        """
        self.own_guid = own_guid
        self._buckets = [
            kbucket.CachingKBucket(0, 2**constants.BIT_NODE_ID_LEN)
        ]
        self._log = logging.getLogger(
            '[%s] %s' % (market_id, self.__class__.__name__)
        )

    def __getitem__(self, key):
        return self._buckets[key]

    def __len__(self):
        return len(self._buckets)

    def add_contact(self, contact):
        """
        Add the given contact to the correct KBucket; if it already
        exists, update its status.

        Args:
            contact: The contact to add, as a contact.Contact.

        Raises:
            BadGUIDError: The given contact is outside the range of
                the RoutingTable.
        """
        if contact.guid == self.own_guid:
            self._log.info('Trying to add yourself. Leaving.')
            return

        kbucket_index = self._get_kbucket_index(contact.guid)
        bucket = self._buckets[kbucket_index]
        try:
            bucket.add_contact(contact)
        except kbucket.FullBucketError:
            # The bucket is full; if its range includes the node's own
            # guid, then split the KBucket into two KBuckets which
            # together cover the same range in the ID space. Then,
            # retry inserting the contact.
            # If not, the KBucket can't be split. Put the new node in the
            # corresponding KBucket's replacement cache.
            if bucket.guid_in_range(self.own_guid):
                new_kbucket = bucket.split_kbucket()
                # The new KBucket should be responsible for the high
                # half of the split range. Add it in the list of
                # buckets right after the split KBucket, to ensure the
                # ID space produced by concatenating successive KBuckets
                # is monotonic.
                self._buckets.insert(kbucket_index + 1, new_kbucket)
                self.add_contact(contact)
            else:
                bucket.cache_contact(contact)

    def get_contact(self, guid):
        """
        Return the known node with the given guid, None if not found.

        Args:
            guid: The guid of the node to search for, as string or unicode,
                in hexadecimal.

        Returns:
            The contact with the given guid or None if not found.

        Raises:
            BadGUIDError: The given guid is malformed or out-of-range.
        """
        bucket = self._get_kbucket_by_guid(guid)
        return bucket.get_contact(guid)

    def remove_contact(self, contact):
        """
        Remove the given contact from the routing table. If the
        contact does not exist, do nothing.

        Args:
            contact: The contact to remove as a contact.Contact.

        Raises:
            BadGUIDError: `contact` is outside the range of the
                RoutingTable.
        """
        bucket = self._get_kbucket_by_guid(contact.guid)
        bucket.remove_contact(contact)

    def remove_guid(self, guid):
        """
        Remove the given guid from the routing table. If such
        a contact does not exist, do nothing.

        Args:
            guid: The guid of the contact to remove, as a string
                or unicode, in hexadecimal.

        BadGUIDError: `guid` is outside the range of the RoutingTable.
        """
        bucket = self._get_kbucket_by_guid(guid)
        bucket.remove_guid(guid)

    def find_close_nodes(self, guid, count=constants.K, sender_guid=None):
        """
        Find a number of known nodes closest to the node/value with the
        given guid.

        Args:
            guid: The guid (of a node or a value) to search for, as a
                string or unicode, in hexadecimal.
            count: The amount of contacts to return, as an integer.
            sender_guid: This is the sender's node guid. The guid
                passed in the parameter is excluded from the list of
                contacts returned. (string or unicode, in hexadecimal)

        Returns:
            A list of contacts closest to the given guid. If
            possible, this method will return `count` contacts. It will
            only return fewer if the node is returning all of the
            contacts that it knows of.
        """
        def gen_indices_closest_to_furthest(idx):
            yield idx
            offset, more = 0, True
            while more:
                more = False
                offset += 1
                low, high = idx - offset, idx + offset
                if low >= 0:
                    yield low
                    more = True
                if high < len(self._buckets):
                    yield high
                    more = True

        index_of_closest_bucket = self._get_kbucket_index(guid)
        closest_nodes = []
        for i in gen_indices_closest_to_furthest(index_of_closest_bucket):
            bucket = self._buckets[i]
            closest_nodes.extend(
                bucket.get_contacts(
                    count - len(closest_nodes),
                    excluded_guid=sender_guid
                )
            )
            if len(closest_nodes) >= count:
                break
        return closest_nodes

    def get_refresh_list(self, force=False):
        """
        Find all buckets that need refreshing and return a list of
        guids that will help do so.

        Args:
            force: If True, guids from all buckets will be returned,
                regardless of the time they were last accessed.

        Returns:
            A list of guids that should be searched for in order to
            refresh the RoutingTable.
        """
        if force:
            buckets_to_refresh = self._buckets
        else:
            buckets_to_refresh = (
                bucket
                for bucket in self._buckets
                if bucket.is_stale()
            )

        return [
            util.random_guid_in_range(b.range_min, b.range_max)
            for b in buckets_to_refresh
        ]

    def _get_kbucket_by_guid(self, guid):
        """
        Return the KBucket responsible for the given guid.

        Agrs:
            guid: The guid for which to find the appropriate KBucket index,
                as a string or unicode, in hexadecimal

        Returns:
            The KBucket responsible for the given guid.

        Raises:
            BadGUIDError: The guid was no KBucket's responsibility; an
                invariant has been violated, or the guid is bad.
        """
        kbucket_index = self._get_kbucket_index(guid)
        return self._buckets[kbucket_index]

    def _get_kbucket_index(self, guid):
        """
        Return the index of the KBucket which is responsible for the
        given guid.

        Agrs:
            guid: The guid for which to find the appropriate KBucket index,
                as a string or unicode, in hexadecimal

        Returns:
            The index of the KBucket responsible for the given guid.

        Raises:
            BadGUIDError: The guid was no KBucket's responsibility; an
                invariant has been violated, or the guid is bad.
        """
        # Since the KBuckets have consecutive ID spaces,
        # we do a binary search.
        low, high = 0, len(self._buckets)
        num_guid = util.guid_to_num(guid)
        while low < high:
            mid = low + (high - low) // 2
            bucket = self._buckets[mid]
            if bucket.range_min > num_guid:
                high = mid
            elif bucket.range_max <= num_guid:
                low = mid + 1
            else:
                return mid
        raise util.BadGUIDError("No KBucket responsible for guid {0}.".format(guid))
