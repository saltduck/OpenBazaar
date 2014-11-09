"""
A module to deal with identity management.
"""


class GUIDMixin(object):
    """
    An interface for a GUID.

    Any class that is meant to be used as a GUID
    should inherit this one.
    """
    def __init__(self, guid):
        self.guid = guid

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.guid == other.guid
        elif isinstance(other, basestring):
            # FIXME: This functionality is deprecated. You should
            # compare GUIDMixin against other GUIDMixin only.
            return self.guid == other
        return False

    def __hash__(self):
        return hash(self.guid)

    def __repr__(self):
        return repr(self.guid)
