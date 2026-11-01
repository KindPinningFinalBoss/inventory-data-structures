"""An indexed binary min-heap used as the reorder priority queue.

The inventory system keeps one of these keyed by reorder urgency, so the item
most in need of restocking is always at the root and can be read in O(1). A
plain heap cannot change an element's priority once it is inside, but stock
levels change constantly, so this version keeps a position map (item -> index).
That map turns "this item's urgency just changed" into an O(log n) sift instead
of an O(n) rebuild, which is the classic decrease-key trick (Williams, 1964).
"""

from __future__ import annotations

from typing import Any, Optional


class MinHeap:
    """A binary min-heap with O(log n) priority updates and removals.

    Each entry is a ``[priority, item]`` pair. Items must be unique and hashable,
    because the position map relies on them as dictionary keys. The root is the
    entry with the smallest priority (ties broken by item).
    """

    def __init__(self) -> None:
        self._heap: list[list] = []
        self._pos: dict[Any, int] = {}  # item -> its index in self._heap

    def push(self, priority: float, item: Any) -> None:
        """Add ``item`` with ``priority``, or update it if already present."""
        if item in self._pos:
            self.update(item, priority)
            return
        self._heap.append([priority, item])
        index = len(self._heap) - 1
        self._pos[item] = index
        self._sift_up(index)

    def peek(self) -> Optional[tuple[float, Any]]:
        """Return the smallest ``(priority, item)`` without removing it. O(1)."""
        if not self._heap:
            return None
        priority, item = self._heap[0]
        return priority, item

    def pop(self) -> tuple[float, Any]:
        """Remove and return the smallest ``(priority, item)``. O(log n)."""
        if not self._heap:
            raise IndexError("pop from an empty heap")
        priority, item = self._heap[0]
        last = self._heap.pop()
        del self._pos[item]
        if self._heap:
            self._heap[0] = last
            self._pos[last[1]] = 0
            self._sift_down(0)
        return priority, item

    def update(self, item: Any, new_priority: float) -> None:
        """Change ``item``'s priority and restore the heap. O(log n)."""
        if item not in self._pos:
            raise KeyError(item)
        index = self._pos[item]
        old_priority = self._heap[index][0]
        self._heap[index][0] = new_priority
        if new_priority < old_priority:
            self._sift_up(index)
        else:
            self._sift_down(index)

    def remove(self, item: Any) -> None:
        """Remove ``item`` wherever it sits in the heap. O(log n)."""
        if item not in self._pos:
            raise KeyError(item)
        index = self._pos[item]
        last = self._heap.pop()
        del self._pos[item]
        if index < len(self._heap):
            self._heap[index] = last
            self._pos[last[1]] = index
            # The replacement may need to travel either direction.
            self._sift_up(index)
            self._sift_down(self._pos[last[1]])

    def _swap(self, i: int, j: int) -> None:
        """Exchange two entries and keep the position map in step."""
        self._heap[i], self._heap[j] = self._heap[j], self._heap[i]
        self._pos[self._heap[i][1]] = i
        self._pos[self._heap[j][1]] = j

    def _sift_up(self, index: int) -> None:
        """Swap the entry toward the root while it is smaller than its parent."""
        while index > 0:
            parent = (index - 1) // 2
            if self._heap[parent][:2] <= self._heap[index][:2]:
                break
            self._swap(parent, index)
            index = parent

    def _sift_down(self, index: int) -> None:
        """Swap the entry down until both children are at least as large."""
        size = len(self._heap)
        while True:
            left = 2 * index + 1
            right = 2 * index + 2
            smallest = index
            if left < size and self._heap[left][:2] < self._heap[smallest][:2]:
                smallest = left
            if right < size and self._heap[right][:2] < self._heap[smallest][:2]:
                smallest = right
            if smallest == index:
                break
            self._swap(index, smallest)
            index = smallest

    def __len__(self) -> int:
        return len(self._heap)

    def __contains__(self, item: Any) -> bool:
        return item in self._pos
