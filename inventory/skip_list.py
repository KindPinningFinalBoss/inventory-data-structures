"""A probabilistic skip list for ordered lookups and range queries.

The inventory system uses this as a price-ordered index. Keys are
``(price, sku)`` tuples, which keeps every key unique while still sorting by
price first. That lets the system answer "give me every product priced between
$20 and $50" by walking a short stretch of the bottom level instead of scanning
and sorting the whole catalogue.

A skip list keeps several linked lists stacked on top of each other. The bottom
list holds every element in sorted order; each higher list is a sparse express
lane built by coin flips. Searching drops down the lanes, skipping large chunks
of the data, which gives O(log n) expected time for search, insert and delete
without the rotation bookkeeping a balanced tree needs (Pugh, 1990).
"""

from __future__ import annotations

import random
from typing import Any, Iterator, Optional


class _SkipNode:
    """A single node holding a key, a value, and one forward pointer per level."""

    __slots__ = ("key", "value", "forward")

    def __init__(self, key: Any, value: Any, level: int) -> None:
        self.key = key
        self.value = value
        # forward[i] is the next node on level i. Index 0 is the bottom lane.
        self.forward: list[Optional["_SkipNode"]] = [None] * (level + 1)


class SkipList:
    """An ordered map supporting search, insert, delete and range queries.

    Args:
        max_level: Hard cap on the number of express lanes. 16 levels comfortably
            index millions of items when ``p`` is 0.5.
        p: Probability that a node is promoted to the next level up. 0.5 is the
            classic choice and gives the best time/space balance (Pugh, 1990).
        seed: Optional seed for the level generator, used to make benchmarks and
            tests reproducible.
    """

    def __init__(self, max_level: int = 16, p: float = 0.5,
                 seed: Optional[int] = None) -> None:
        self._max_level = max_level
        self._p = p
        self._level = 0  # highest lane currently in use
        self._head = _SkipNode(None, None, max_level)
        self._size = 0
        self._rng = random.Random(seed)

    def _random_level(self) -> int:
        """Flip coins to decide how tall a new node should be."""
        level = 0
        while self._rng.random() < self._p and level < self._max_level:
            level += 1
        return level

    def insert(self, key: Any, value: Any) -> None:
        """Insert ``key`` (or update its value if already present). O(log n)."""
        update: list[_SkipNode] = [self._head] * (self._max_level + 1)
        node = self._head
        for i in range(self._level, -1, -1):
            while node.forward[i] is not None and node.forward[i].key < key:
                node = node.forward[i]
            update[i] = node

        candidate = node.forward[0]
        if candidate is not None and candidate.key == key:
            candidate.value = value  # key already here, just refresh the value
            return

        new_level = self._random_level()
        if new_level > self._level:
            for i in range(self._level + 1, new_level + 1):
                update[i] = self._head
            self._level = new_level

        new_node = _SkipNode(key, value, new_level)
        for i in range(new_level + 1):
            new_node.forward[i] = update[i].forward[i]
            update[i].forward[i] = new_node
        self._size += 1

    def search(self, key: Any) -> Any:
        """Return the value stored at ``key`` or ``None`` if absent. O(log n)."""
        node = self._head
        for i in range(self._level, -1, -1):
            while node.forward[i] is not None and node.forward[i].key < key:
                node = node.forward[i]
        node = node.forward[0]
        if node is not None and node.key == key:
            return node.value
        return None

    def delete(self, key: Any) -> bool:
        """Remove ``key``. Return True if it was present. O(log n)."""
        update: list[Optional[_SkipNode]] = [None] * (self._max_level + 1)
        node = self._head
        for i in range(self._level, -1, -1):
            while node.forward[i] is not None and node.forward[i].key < key:
                node = node.forward[i]
            update[i] = node

        target = node.forward[0]
        if target is None or target.key != key:
            return False

        for i in range(self._level + 1):
            if update[i] is not None and update[i].forward[i] is target:
                update[i].forward[i] = target.forward[i]
        # Drop any now-empty top lanes.
        while self._level > 0 and self._head.forward[self._level] is None:
            self._level -= 1
        self._size -= 1
        return True

    def range_query(self, low: Any, high: Any) -> Iterator[tuple[Any, Any]]:
        """Yield every ``(key, value)`` with ``low <= key <= high``, in order.

        Costs O(log n) to find the start plus O(k) to walk the ``k`` matches.
        """
        node = self._head
        for i in range(self._level, -1, -1):
            while node.forward[i] is not None and node.forward[i].key < low:
                node = node.forward[i]
        node = node.forward[0]
        while node is not None and node.key <= high:
            yield node.key, node.value
            node = node.forward[0]

    def __iter__(self) -> Iterator[tuple[Any, Any]]:
        """Walk the bottom lane, yielding every pair in sorted key order."""
        node = self._head.forward[0]
        while node is not None:
            yield node.key, node.value
            node = node.forward[0]

    def __len__(self) -> int:
        return self._size
