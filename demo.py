"""A short, readable walkthrough of the inventory system's key operations.

Run it with ``python demo.py`` from the project root. It seeds a small
catalogue, then shows a point lookup, a price-range query, a reorder report, and
a live quantity change rippling through to the reorder priority queue.
"""

from __future__ import annotations

from inventory import InventorySystem, Product


def build_sample_catalogue() -> InventorySystem:
    """Create a system and load a handful of hand-written products."""
    system = InventorySystem(skiplist_seed=7)
    catalogue = [
        Product("SKU-1001", "USB-C Cable 1m", 7.99, 120, "accessories", 40),
        Product("SKU-1002", "Wireless Mouse", 24.50, 8, "accessories", 15),
        Product("SKU-1003", "27in Monitor", 189.00, 30, "displays", 10),
        Product("SKU-1004", "Mechanical Keyboard", 89.99, 3, "accessories", 12),
        Product("SKU-1005", "Laptop Stand", 34.95, 55, "accessories", 20),
        Product("SKU-1006", "4K Webcam", 119.00, 6, "video", 10),
        Product("SKU-1007", "Desk Lamp", 29.99, 200, "lighting", 25),
        Product("SKU-1008", "Noise-Cancel Headset", 149.99, 9, "audio", 10),
    ]
    for product in catalogue:
        system.add_product(product)
    return system


def main() -> None:
    system = build_sample_catalogue()
    print(f"Loaded {len(system)} products.\n")

    print("== Point lookup by SKU (hash table, O(1)) ==")
    found = system.get_product("SKU-1003")
    print(f"  SKU-1003 -> {found.name} at ${found.price}, qty {found.quantity}\n")

    print("== Price range $20 - $90, cheapest first (skip list, O(log n + k)) ==")
    for product in system.products_in_price_range(20.0, 90.0):
        print(f"  ${product.price:>7.2f}  {product.name}")
    print()

    print("== Most urgent reorder right now (heap peek, O(1)) ==")
    urgent = system.most_urgent_reorder()
    print(f"  {urgent.name}: {urgent.quantity} on hand vs threshold "
          f"{urgent.reorder_threshold}\n")

    print("== Everything below its reorder threshold, most urgent first ==")
    for product in system.items_needing_reorder():
        print(f"  {product.name}: qty {product.quantity} "
              f"(threshold {product.reorder_threshold})")
    print()

    print("== A sale drops the keyboard to 0; the queue updates (O(log n)) ==")
    system.update_quantity("SKU-1004", 0)
    urgent = system.most_urgent_reorder()
    print(f"  New most urgent: {urgent.name} with {urgent.quantity} on hand\n")

    print("== A restock lifts the headset well above threshold ==")
    system.update_quantity("SKU-1008", 250)
    print("  Reorder list after restock:")
    for product in system.items_needing_reorder():
        print(f"    {product.name}: qty {product.quantity}")


if __name__ == "__main__":
    main()
