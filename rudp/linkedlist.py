__author__ = 'brianhoffman'

import logging


class Node(object):

    def __init__(self, value):
        self.value = value
        self._child_node = None


# TODO: do note that this is an ordered linked-list. Perhaps this class should
#     be renamed to better indicate that.
# TODO: use a generator/iterator pattern for looping through the list.
class LinkedList(object):

    insertion_result = {'INSERTED': 'inserted', 'EXISTS': 'exists', 'FAILED': 'failed'}

    def __init__(self, order_by):
        self._child_node = None
        self._order_by = order_by
        self._current_node = None

        self.log = logging.getLogger(
            '%s' % self.__class__.__name__
        )

    def insert(self, obj):
        if not self._child_node:
            self._child_node = Node(obj)
            self._current_node = self._child_node
            return LinkedList.insertion_result.get('INSERTED')

        return self._insert(self, obj)

    def clear(self):
        self._child_node = None
        self._current_node = None

    def reset_index(self):
        self._current_node = self._child_node

    def seek(self):
        if not self._current_node:
            return False

        if not self._current_node._child_node:
            return False

        self._current_node = self._current_node._child_node
        return True

    def current_value(self):
        if not self._current_node:
            raise LookupError('There aren\'t any nodes on the list.')

        return self._current_node.value

    def has_value(self):
        return bool(self._child_node)

    def next_value(self):
        if not self._current_node:
            raise LookupError('There aren\'t any nodes on the list.')
        elif not self._current_node._child_node:
            raise LookupError('The current node does not have any child nodes')

        return self._current_node._child_node.value

    def has_next(self):
        return bool(self._current_node._child_node)

    def to_array(self):
        return self._to_array(self, [])

    def to_array_value(self):
        return self._to_array(self, [], True)

    def _to_array(self, node, accum, value=False):
        if not node._child_node:
            return accum
        if value and node._child_node:
            return self._to_array(node._child_node, accum + [node._child_node.value])
        else:
            return self._to_array(node._child_node, accum + [node._child_node.value])

    def _insert(self, parent_node, obj):
        if not parent_node._child_node:
            parent_node._child_node = Node(obj)
            return LinkedList.insertion_result.get('INSERTED')

        order = self._order_by(obj, parent_node._child_node.value)

        if order <= -1:
            node = Node(obj)
            node._child_node = parent_node._child_node
            parent_node._child_node = node
            return LinkedList.insertion_result.get('INSERTED')
        elif order >= 1:
            return self._insert(parent_node._child_node, obj)
        elif order == 0:
            return LinkedList.insertion_result.get('EXISTS')

        return LinkedList.insertion_result.get('FAILED')
