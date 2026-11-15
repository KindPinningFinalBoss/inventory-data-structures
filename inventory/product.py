"""Product record used across every index in the inventory system.

A :class:`Product` is the single source of truth for one stock item. The hash
table stores the canonical object; the skip list and the reorder heap only hold
the SKU (a key) that points back here, so a product's data lives in exactly one
place.
"""

from __future__ import annotations

import math
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

    def __setattr__(self, name: str, value) -> None:
        """Validate on every write, so a bad value can never be stored.

        ``__init__`` goes through here too, which means construction and later
        edits (``product.quantity = -3``) are held to the same rules. The check
        runs before the assignment, so a rejected write leaves the old value.
        """
        self._check(name, value)
        object.__setattr__(self, name, value)

    @staticmethod
    def _check(name: str, value) -> None:
        """Raise TypeError or ValueError if ``value`` is illegal for ``name``."""
        if name == "sku":
            if not isinstance(value, str):
                raise TypeError(f"sku must be a string, got {type(value).__name__}")
            if not value.strip():
                raise ValueError("sku must be a non-empty string")
        elif name == "price":
            # bool is a subclass of int, so it has to be turned away by hand.
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError(f"price must be a number, got {type(value).__name__}")
            if not math.isfinite(value):
                raise ValueError(f"price must be a finite number, got {value}")
            if value < 0:
                raise ValueError(f"price must be >= 0, got {value}")
        elif name in ("quantity", "reorder_threshold"):
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(
                    f"{name} must be a whole number, got {type(value).__name__}"
                )
            if name == "quantity" and value < 0:
                raise ValueError(f"quantity must be >= 0, got {value}")
            if name == "reorder_threshold" and value <= 0:
                raise ValueError(f"reorder_threshold must be > 0, got {value}")

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
