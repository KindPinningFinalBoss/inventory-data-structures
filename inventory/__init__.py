"""Dynamic inventory management built on custom data structures.

Public surface:
    * :class:`~inventory.product.Product` - the stock record.
    * :class:`~inventory.hash_table.HashTable` - O(1) SKU index.
    * :class:`~inventory.skip_list.SkipList` - O(log n) ordered / range index.
    * :class:`~inventory.min_heap.MinHeap` - O(1)-peek reorder priority queue.
    * :class:`~inventory.system.InventorySystem` - the optimised, multi-index API.
    * :class:`~inventory.naive.NaiveInventory` - the list-based baseline.
"""

from .hash_table import HashTable
from .min_heap import MinHeap
from .naive import NaiveInventory
from .product import Product
from .skip_list import SkipList
from .system import InventorySystem

__all__ = [
    "Product",
    "HashTable",
    "SkipList",
    "MinHeap",
    "InventorySystem",
    "NaiveInventory",
]
