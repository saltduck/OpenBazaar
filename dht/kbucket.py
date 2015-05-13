"""
Collection of KBucket classes storing contacts for RoutingTables.

Classes:
    KBucket -- A classic k-bucket.
    CachingKBucket -- A KBucket with a replacement cache.

Exceptions:
    FullBucketError -- Raised when adding a contact to a full KBucket.
"""

import collections
import time

from dht import constants, util


class FullBucketError(Exception):
    """Raised when attempting to add a contact in a full KBucket."""
    pass


class KBucket(collections.Sequence):
    """A simple k-bucket for a Kademlia routing table."""

    def __init__(self, range_min, range_max):
        """
        Make a new KBucket with the specified range.

        Args:
            range_min, range_max: The lower and upper limits for the
                range in the ID space covered by this KBucket, as integers.
                This is a half-open range: [range_min, range_max)
        """
        self.last_accessed = int(time.time())
        self.range_min = range_min
        self.range_max = range_max

        # This list of contacts implements an LRU-protocol:
        # Fresh or updated contacts are near the tail of the list,
        # while stale contacts are near the head.
        self._contacts = []

    def __getitem__(self, key):
        return self._contacts[key]

    def __len__(self):
        return len(self._contacts)

    def add_contact(self, contact):
        """
        Add a contact to the contact list.

        The new contact is always appended to the contact list after
        removing any prior occurences of the same contact. This is the
        intended behaviour; the fresh contact may have updated add-on
        data (e.g. optimization-specific stuff).

        Args:
            contact: The contact to add, as a contact.Contact.

        Raises:
            FullBucketError: The bucket is full and the contact to add
                is not already in it.
        """
        try:
            self._contacts.remove(contact)
        except ValueError:
            pass

        if len(self._contacts) < constants.K:
            self._contacts.append(contact)
        else:
            raise FullBucketError('No space in bucket to insert contact')

    def get_contact(self, guid):
        """
        Return the contact with the specified guid or None if not present.

        Args:
            guid: The guid to search for, as a string or a unicode,
                in hexadecimal.

        Returns:
            A contact.Contact with the given guid or None
        """
        for contact in self._contacts:
            if contact.guid == guid:
                return contact
        return None

    def get_contacts(self, count=-1, excluded_guid=None):
        """
        Return a list of contacts from the KBucket.

        Args:
            count: The amount of contacts to return, as an int;
                if negative, return all contacts.
            excluded_guid: A guid to exclude, as a string or unicode;
                if a contact with this guid is in the list of returned
                values, it will be discarded before returning.
        Returns:
            List of (at most) `count` contacts from the contact list.
            This amount is capped by the available contacts and the
            bucket size, of course. Newer contacts are preferred.
            If no contacts are present, an empty list is returned.
        """
        current_len = len(self._contacts)
        if current_len == 0 or count == 0:
            return []

        if count < 0:
            count = current_len
        else:
            count = min(count, current_len)

        if excluded_guid is None:
            # Get the last `count` contacts.
            contact_list = self._contacts[-count:]
        else:
            contact_list = []
            for contact in reversed(self._contacts):
                if contact.guid == excluded_guid:
                    continue
                contact_list.append(contact)
                if len(contact_list) >= count:
                    break
        return contact_list

    def remove_contact(self, contact):
        """
        Remove given contact from contact list.

        Args:
            contact: The contact to remove, as a contact.Contact.

        If no such contact exists, do nothing.
        """
        try:
            self._contacts.remove(contact)
        except ValueError:
            pass

    def remove_guid(self, guid):
        """
        Remove contact with given guid from contact list.

        Args:
            guid: The guid of the contact that we want removed,
                as a string or unicode, in hexadecimal.

        If no such contact exists, do nothing.
        """
        self._contacts = [
            contact
            for contact in self._contacts
            if contact.guid != guid
        ]

    def split_kbucket(self):
        """
        Split the high half of this KBucket's range and assign it
        to a new KBucket. Relocate all relevant contacts to the new
        KBucket.

        Note: If multiple threads attempt to split the same KBucket,
        data corruption may occur.

        Returns:
            The new KBucket, which covers the high part of the
            halved ID space.
        """
        cur_range_size = self.range_max - self.range_min
        half_point = self.range_min + cur_range_size // 2

        # Ensure no empty range is created.
        assert self.range_min < half_point < self.range_max

        # Make the instantiation dependent on the actual class,
        # for easy inheritance.
        new_kbucket = self.__class__(half_point, self.range_max)

        # Halve the ID space of the split KBucket.
        self.range_max = half_point

        # Split the contact list into two, according to the new ranges.
        self._contacts, new_kbucket._contacts = util.partition(
            self._contacts,
            self.contact_in_range
        )

        return new_kbucket

    def contact_in_range(self, contact):
        """
        Test whether the given contact is in the range of the ID
        space covered by this KBucket.

        Args:
            contact: The contact to test, as contact.Contact

        Returns:
            True if `contact` is in this KBucket's range, False otherwise.
        """
        return self.guid_in_range(contact.guid)

    def guid_in_range(self, guid):
        """
        Test whether the given guid is in the range of the ID space
        covered by this KBucket.

        Args:
            guid: The guid to test, as a string or unicode, in
                hexadecimal.

        Returns:
            True if `guid` is in this KBucket's range, False otherwise.
        """
        return self.range_min <= util.guid_to_num(guid) < self.range_max

    def touch(self):
        """
        Update the `last_accessed` timestamp of the KBucket by setting
        it to current local time.
        """
        self.last_accessed = int(time.time())


class CachingKBucket(KBucket):
    """A KBucket with a replacement cache."""

    def __init__(self, range_min, range_max):
        super(CachingKBucket, self).__init__(range_min, range_max)

        # Cache containing nodes eligible to replace stale entries.
        # Entries at the tail (right) of the cache are preferred
        # than entries at the head (left).
        self._replacement_cache = collections.deque()

    def cache_contact(self, contact):
        """
        Store a contact in the KBucket's replacement cache. Evict any
        existing contact with the same guid.

        Args:
            contact: The contact to cache, as a contact.Contact

        If the cache is full, `contact` will replace the oldest
        contact in the cache.
        """
        try:
            self._replacement_cache.remove(contact)
        except ValueError:
            pass

        self._replacement_cache.append(contact)
        if len(self._replacement_cache) > constants.CACHE_K:
            self._replacement_cache.popleft()

    def get_cached_contacts(self):
        """
        Return all contacts in cache.

        Returns:
            A list of all cached contacts, oldest first.
        """
        return list(self._replacement_cache)

    def remove_contact(self, contact):
        """
        Remove given contact from contact list.

        Args:
            contact: The contact to remove, as a contact.Contact.

        If no such contact exists, do nothing. In any case, refill the
        main list from the cache.
        """
        super(CachingKBucket, self).remove_contact(contact)
        self.fill_from_cache()

    def remove_guid(self, guid):
        """
        Remove contact with given guid from contact list.

        Args:
            guid: The guid of the contact that we want removed,
                as a string or unicode.

        If no such contact exists, do nothing. In any case, refill the
        main list from the cache.
        """
        super(CachingKBucket, self).remove_guid(guid)
        self.fill_from_cache()

    def split_kbucket(self):
        """
        Split the high half of this KBucket's range and assign it
        to a new KBucket. Relocate all relevant contacts to the new
        KBucket.

        Note: If multiple threads attempt to split the same KBucket,
        the operation may cause data corruption.

        Returns:
            The new KBucket, which covers the high part of the
            halved ID space.

        In addition to splitting the contacts, this method also
        splits the cache of the existing bucket, according to the
        guids. Then, it refills the contact lists from the caches.
        """
        new_kbucket = super(CachingKBucket, self).split_kbucket()

        cache_self, cache_new = util.partition(
            self._replacement_cache,
            self.contact_in_range
        )

        # Replacement caches are deques, so we can't directly assign
        # the values returned by partition.
        new_kbucket._replacement_cache.extend(cache_new)
        self._replacement_cache.clear()
        self._replacement_cache.extend(cache_self)

        self.fill_from_cache()
        new_kbucket.fill_from_cache()

        return new_kbucket

    def fill_from_cache(self):
        """
        Move contacts from the cache to the main list, until the
        cache is exhausted or the main list is full.
        """
        move_count = min(
            len(self._replacement_cache),
            constants.K - len(self._contacts)
        )

        for _ in range(move_count):
            self.add_contact(self._replacement_cache.pop())
