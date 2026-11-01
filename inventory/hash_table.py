"""A hash table with separate chaining and dynamic resizing.

This is the primary index of the inventory system: it maps a SKU string to its
:class:`~inventory.product.Product`. Lookups, insertions and deletions run in
O(1) on average. The table grows automatically once the load factor passes a
threshold, which keeps the average chain short as the data set gets bigger.

Separate chaining (each bucket holds a small list of entries that collide) was
chosen over open addressing because deletions stay simple and the structure
degrades gracefully when the hash function spreads keys unevenly.
"""

from __future__ import annotations

from typing import Any, Iterator, Optional


class HashTable:
    """A dictionary-like map built on separate chaining.

    The table keeps the load factor (entries / buckets) under
    ``_MAX_LOAD_FACTOR`` by doubling its bucket count and rehashing whenever an
    insertion would cross that line. Rehashing is O(n), but because it happens
    rarely and spreads over many insertions, each insertion is still O(1)
    amortised.
    """

    _INITIAL_CAPACITY = 8
    _MAX_LOAD_FACTOR = 0.75
    _GROWTH_FACTOR = 2

    def __init__(self) -> None:
        self._capacity: int = self._INITIAL_CAPACITY
        self._size: int = 0
        self._buckets: list[list[list]] = [[] for _ in range(self._capacity)]

    def _hash(self, key: str) -> int:
        """Return a non-negative hash code for a string key.

        Uses a djb2-style polynomial rolling hash. It is simple, fast, and
        spreads typical SKU strings well. Non-string keys fall back to Python's
        built-in ``hash`` so the table still works for them.
        """
        if isinstance(key, str):
            h = 5381
            for char in key:
                h = ((h << 5) + h + ord(char)) & 0xFFFFFFFF  # h * 33 + c
            return h
        return hash(key) & 0xFFFFFFFF

    def _index(self, key: str, capacity: Optional[int] = None) -> int:
        """Map a key to a bucket index for the current (or given) capacity."""
        cap = capacity if capacity is not None else self._capacity
        return self._hash(key) % cap

    def put(self, key: str, value: Any) -> None:
        """Insert or update ``key`` with ``value`` (average O(1))."""
        bucket = self._buckets[self._index(key)]
        for entry in bucket:
            if entry[0] == key:
                entry[1] = value  # update in place
                return
        bucket.append([key, value])
        self._size += 1
        if self.load_factor > self._MAX_LOAD_FACTOR:
            self._resize(self._capacity * self._GROWTH_FACTOR)

    def get(self, key: str, default: Any = None) -> Any:
        """Return the value for ``key`` or ``default`` if absent (average O(1))."""
        bucket = self._buckets[self._index(key)]
        for entry in bucket:
            if entry[0] == key:
                return entry[1]
        return default

    def remove(self, key: str) -> Any:
        """Delete ``key`` and return its value, or raise ``KeyError``."""
        bucket = self._buckets[self._index(key)]
        for i, entry in enumerate(bucket):
            if entry[0] == key:
                bucket.pop(i)
                self._size -= 1
                return entry[1]
        raise KeyError(key)

    def _resize(self, new_capacity: int) -> None:
        """Grow the bucket array and rehash every entry into it (O(n))."""
        new_buckets: list[list[list]] = [[] for _ in range(new_capacity)]
        for bucket in self._buckets:
            for key, value in bucket:
                new_buckets[self._index(key, new_capacity)].append([key, value])
        self._buckets = new_buckets
        self._capacity = new_capacity

    @property
    def load_factor(self) -> float:
        """Current ratio of stored entries to available buckets."""
        return self._size / self._capacity

    @property
    def capacity(self) -> int:
        """Number of buckets currently allocated."""
        return self._capacity

    def items(self) -> Iterator[tuple[str, Any]]:
        """Yield every ``(key, value)`` pair. Order is not meaningful."""
        for bucket in self._buckets:
            for key, value in bucket:
                yield key, value

    def __contains__(self, key: str) -> bool:
        bucket = self._buckets[self._index(key)]
        return any(entry[0] == key for entry in bucket)

    def __getitem__(self, key: str) -> Any:
        bucket = self._buckets[self._index(key)]
        for entry in bucket:
            if entry[0] == key:
                return entry[1]
        raise KeyError(key)

    def __len__(self) -> int:
        return self._size

    def __iter__(self) -> Iterator[str]:
        for bucket in self._buckets:
            for key, _ in bucket:
                yield key
