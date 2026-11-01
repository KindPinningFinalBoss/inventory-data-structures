"""A deliberately simple, list-backed inventory used as the performance baseline.

This is the proof-of-concept version: correct and easy to read, but every
operation walks the whole list. It exists so the optimised
:class:`~inventory.system.InventorySystem` has something honest to be measured
against. The benchmark compares the two directly.
"""

from __future__ import annotations

from typing import Optional

from .product import Product


class NaiveInventory:
    """Inventory stored as a flat Python list.

    Lookup, update and removal are O(n) because they scan from the front.
    Price-range queries are O(n log n) because the list is re-sorted on demand.
    Finding items that need reordering is O(n log n) for the same reason.
    """

    def __init__(self) -> None:
        self._items: list[Product] = []

    def add_product(self, product: Product) -> None:
        """Append a product after a linear duplicate check. O(n)."""
        for existing in self._items:
            if existing.sku == product.sku:
                raise KeyError(f"duplicate sku: {product.sku}")
        self._items.append(product)

    def bulk_add(self, products: list[Product]) -> None:
        """Append many products at once, trusting the caller for uniqueness.

        This skips the per-item duplicate scan, so it is O(n) overall instead of
        O(n^2). It exists only to set up benchmark fixtures quickly; normal code
        should use :meth:`add_product`.
        """
        self._items.extend(products)

    def get_product(self, sku: str) -> Optional[Product]:
        """Return the product with ``sku`` by scanning the list. O(n)."""
        for product in self._items:
            if product.sku == sku:
                return product
        return None

    def remove_product(self, sku: str) -> None:
        """Find and delete a product by SKU. O(n)."""
        for i, product in enumerate(self._items):
            if product.sku == sku:
                self._items.pop(i)
                return
        raise KeyError(sku)

    def update_quantity(self, sku: str, quantity: int) -> None:
        """Scan for the product and set its quantity. O(n)."""
        product = self.get_product(sku)
        if product is None:
            raise KeyError(sku)
        if quantity < 0:
            raise ValueError("quantity must be >= 0")
        product.quantity = quantity

    def products_in_price_range(self, low: float, high: float) -> list[Product]:
        """Filter every product, then sort the matches by price. O(n log n)."""
        matches = [p for p in self._items if low <= p.price <= high]
        matches.sort(key=lambda p: p.price)
        return matches

    def items_needing_reorder(self, limit: Optional[int] = None) -> list[Product]:
        """Scan for low-stock items and sort them by urgency. O(n log n)."""
        low_stock = [p for p in self._items if p.needs_reorder]
        low_stock.sort(key=lambda p: p.urgency)
        return low_stock if limit is None else low_stock[:limit]

    def __len__(self) -> int:
        return len(self._items)
