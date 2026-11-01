"""Product record used across every index in the inventory system.

A :class:`Product` is the single source of truth for one stock item. The hash
table stores the canonical object; the skip list and the reorder heap only hold
the SKU (a key) that points back here, so a product's data lives in exactly one
place.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Product:
    """One item of stock.

    Attributes:
        sku: Unique stock-keeping unit. Acts as the primary key everywhere.
        name: Human-readable product name.
        price: Unit price in dollars. Must be non-negative.
        quantity: Units currently on hand. Must be non-negative.
        category: Product category label (e.g. ``"electronics"``).
        reorder_threshold: When ``quantity`` falls to this level or below, the
            item is considered to need replenishment. Must be positive.
    """

    sku: str
    name: str
    price: float
    quantity: int
    category: str
    reorder_threshold: int = 10

    def __post_init__(self) -> None:
        """Validate the record so bad data never reaches an index."""
        if not self.sku:
            raise ValueError("sku must be a non-empty string")
        if self.price < 0:
            raise ValueError(f"price must be >= 0, got {self.price}")
        if self.quantity < 0:
            raise ValueError(f"quantity must be >= 0, got {self.quantity}")
        if self.reorder_threshold <= 0:
            raise ValueError(
                f"reorder_threshold must be > 0, got {self.reorder_threshold}"
            )

    @property
    def urgency(self) -> float:
        """Reorder urgency as a ratio of stock to threshold.

        Smaller means more urgent. A value at or below ``1.0`` means the item
        is at or under its reorder threshold and should be restocked.
        """
        return self.quantity / self.reorder_threshold

    @property
    def needs_reorder(self) -> bool:
        """True when on-hand stock has reached the reorder threshold."""
        return self.quantity <= self.reorder_threshold
