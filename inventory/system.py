"""The optimised inventory system that wires the three indexes together.

Each product is stored once as a :class:`~inventory.product.Product` object
inside the hash table (the single source of truth). The skip list and the
reorder heap only hold keys that point back to it, so there is never a second
copy of a product's data to keep in sync.

Index map:
    * hash table  -> SKU to Product            (O(1) point lookup)
    * skip list   -> (price, SKU) to Product   (O(log n) ordered / range query)
    * min-heap    -> urgency to SKU            (O(1) peek at the most urgent)

The skip list stores the same Product object the hash table holds, by
reference, not a copy. There is still one canonical record per product; the
indexes just point at it from different angles.
"""

from __future__ import annotations

import math
from typing import Iterator, Optional

from .hash_table import HashTable
from .min_heap import MinHeap
from .product import Product
from .skip_list import SkipList


class InventorySystem:
    """A multi-index inventory supporting fast lookup, range and reorder queries."""

    def __init__(self, skiplist_seed: Optional[int] = None) -> None:
        self._by_sku = HashTable()
        self._by_price = SkipList(seed=skiplist_seed)
        self._reorder = MinHeap()

    def add_product(self, product: Product) -> None:
        """Register a product in all three indexes. O(log n).

        Raises:
            TypeError: ``product`` is not a :class:`Product`.
            KeyError: a product with the same SKU is already stored. Nothing is
                written to any index in that case.
        """
        if not isinstance(product, Product):
            raise TypeError(
                f"add_product expects a Product, got {type(product).__name__}"
            )
        if product.sku in self._by_sku:
            raise KeyError(f"duplicate sku: {product.sku}")
        self._by_sku.put(product.sku, product)
        self._by_price.insert((product.price, product.sku), product)
        self._reorder.push(product.urgency, product.sku)

    def get_product(self, sku: str) -> Optional[Product]:
        """Return a product by SKU. O(1) average."""
        return self._by_sku.get(sku)

    def remove_product(self, sku: str) -> None:
        """Remove a product from every index. O(log n)."""
        product = self._require(sku)
        self._by_sku.remove(sku)
        self._by_price.delete((product.price, product.sku))
        self._reorder.remove(sku)

    def update_quantity(self, sku: str, quantity: int) -> None:
        """Set a product's quantity and refresh its reorder priority. O(log n)."""
        product = self._require(sku)
        # Assigning runs Product's own validation first, so a bad quantity
        # raises here before the heap is touched and nothing is half-updated.
        product.quantity = quantity
        self._reorder.update(sku, product.urgency)

    def adjust_quantity(self, sku: str, delta: int) -> None:
        """Add ``delta`` (negative for a sale) to a product's quantity. O(log n).

        Raises:
            KeyError: unknown SKU.
            ValueError: the result would be below zero (stock is left as it was).
        """
        product = self._require(sku)
        if product.quantity + delta < 0:
            raise ValueError(
                f"cannot remove {-delta} of {sku}: only {product.quantity} on hand"
            )
        self.update_quantity(sku, product.quantity + delta)

    def update_price(self, sku: str, price: float) -> None:
        """Change a product's price, re-keying it in the price index. O(log n)."""
        product = self._require(sku)
        # Validate first. If the delete below ran and the assignment then failed,
        # the product would vanish from the price index.
        Product._check("price", price)
        # The price index is keyed on price, so the old key must move.
        self._by_price.delete((product.price, sku))
        product.price = price
        self._by_price.insert((price, sku), product)

    def products_in_price_range(self, low: float, high: float) -> list[Product]:
        """Return products priced in ``[low, high]``, cheapest first. O(log n + k).

        The skip list already holds the products in price order, so the matches
        come straight off the bottom lane with no extra lookup or sort.

        Raises:
            TypeError: a bound is not a number.
            ValueError: a bound is NaN or ``low`` is greater than ``high``.
        """
        for bound in (low, high):
            if isinstance(bound, bool) or not isinstance(bound, (int, float)):
                raise TypeError(
                    f"price bounds must be numbers, got {type(bound).__name__}"
                )
            if math.isnan(bound):
                raise ValueError("price bounds cannot be NaN")
        if low > high:
            raise ValueError(f"low ({low}) must not exceed high ({high})")
        return [
            product
            for _key, product in self._by_price.range_query(
                (low, ""), (high, chr(0x10FFFF))
            )
        ]

    def most_urgent_reorder(self) -> Optional[Product]:
        """Return the single item most in need of restocking. O(1)."""
        top = self._reorder.peek()
        if top is None:
            return None
        return self._by_sku.get(top[1])

    def items_needing_reorder(self, limit: Optional[int] = None) -> list[Product]:
        """Return low-stock items in urgency order, most urgent first.

        Pops up to ``limit`` entries off the heap, then pushes them back, so the
        heap is left unchanged. Costs O(k log n) for ``k`` items returned, versus
        the baseline's O(n log n) scan-and-sort of the entire catalogue.

        Raises:
            ValueError: ``limit`` is negative. ``None`` means no limit.
        """
        if limit is not None and limit < 0:
            raise ValueError(f"limit must be >= 0, got {limit}")
        taken: list[tuple[float, str]] = []
        results: list[Product] = []
        while self._reorder and (limit is None or len(results) < limit):
            urgency, sku = self._reorder.pop()
            taken.append((urgency, sku))
            product = self._by_sku.get(sku)
            if product is not None and product.needs_reorder:
                results.append(product)
            elif product is not None and not product.needs_reorder:
                # The smallest urgency is already above threshold, so every
                # remaining item is too. Stop early.
                break
        for urgency, sku in taken:
            self._reorder.push(urgency, sku)
        return results

    def _require(self, sku: str) -> Product:
        """Return the product for ``sku`` or raise a KeyError that names it."""
        product = self._by_sku.get(sku)
        if product is None:
            raise KeyError(f"unknown sku: {sku}")
        return product

    def __iter__(self) -> Iterator[Product]:
        """Traverse every product in (price, SKU) order via the skip list."""
        for _key, product in self._by_price:
            yield product

    def __len__(self) -> int:
        return len(self._by_sku)

    def __contains__(self, sku: str) -> bool:
        return sku in self._by_sku
