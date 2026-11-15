"""Phase 2 proof-of-concept walkthrough: normal use first, then the edge cases.

Run from the project root with ``python poc_demo.py``. Every step prints what it
did and what came back. Steps that are supposed to fail print the exception, so
you can see the error handling working instead of taking my word for it.
"""

from __future__ import annotations

from inventory import InventorySystem, Product


def show(title: str) -> None:
    print(f"\n--- {title} ---")


def expect_error(label: str, action) -> None:
    """Run ``action`` and print the exception it is expected to raise."""
    try:
        action()
    except (KeyError, ValueError, TypeError) as exc:
        print(f"  {label}: {type(exc).__name__}: {exc}")
    else:
        print(f"  {label}: NO ERROR (this would be a bug)")


def main() -> None:
    inv = InventorySystem(skiplist_seed=7)

    show("1. Insertion")
    for p in [
        Product("A-100", "Notebook", 4.50, 40, "paper", 10),
        Product("A-101", "Pen Pack", 4.50, 6, "paper", 12),    # same price as A-100
        Product("B-200", "Desk Lamp", 29.99, 15, "lighting", 5),
        Product("C-300", "Monitor", 189.00, 2, "displays", 4),
    ]:
        inv.add_product(p)
        print(f"  added {p.sku} ({p.name}, ${p.price})")
    print(f"  catalogue size: {len(inv)}")

    show("2. Search by SKU (hash table)")
    print(f"  A-101 -> {inv.get_product('A-101').name}")
    print(f"  Z-999 -> {inv.get_product('Z-999')}")

    show("3. Traversal in price order (skip list)")
    for p in inv:
        print(f"  ${p.price:>7.2f}  {p.sku}  {p.name}")

    show("4. Range query, including two products at the same price")
    hits = inv.products_in_price_range(4.50, 30.00)
    print("  $4.50 to $30.00:", [p.sku for p in hits])
    print("  $50 to $100    :", [p.sku for p in inv.products_in_price_range(50, 100)])

    show("5. Reorder queue (heap)")
    print(f"  most urgent: {inv.most_urgent_reorder().sku}")
    print("  needing reorder:", [p.sku for p in inv.items_needing_reorder()])
    inv.adjust_quantity("A-101", -6)     # sell the last six pens
    print(f"  after selling out A-101, most urgent: {inv.most_urgent_reorder().sku}")
    inv.update_quantity("A-101", 200)    # a delivery arrives
    print("  after restock, needing reorder:",
          [p.sku for p in inv.items_needing_reorder()])

    show("6. Update a price (the product moves inside the skip list)")
    inv.update_price("A-100", 99.00)
    print("  traversal now:", [p.sku for p in inv])

    show("7. Deletion")
    inv.remove_product("B-200")
    print(f"  removed B-200, size is {len(inv)}")
    print(f"  B-200 lookup -> {inv.get_product('B-200')}")

    show("8. Error handling (each line below is an expected failure)")
    expect_error("duplicate SKU        ", lambda: inv.add_product(
        Product("A-100", "Clone", 1.0, 1, "paper")))
    expect_error("remove missing SKU   ", lambda: inv.remove_product("Z-999"))
    expect_error("negative quantity    ", lambda: inv.update_quantity("A-100", -1))
    expect_error("oversell             ", lambda: inv.adjust_quantity("C-300", -5))
    expect_error("fractional quantity  ", lambda: inv.update_quantity("A-100", 2.5))
    expect_error("NaN price            ", lambda: inv.update_price("A-100", float("nan")))
    expect_error("negative price       ", lambda: Product("X", "Bad", -1.0, 1, "c"))
    expect_error("price given as text  ", lambda: Product("X", "Bad", "9.99", 1, "c"))
    expect_error("inverted price range ", lambda: inv.products_in_price_range(50, 10))
    expect_error("negative report limit", lambda: inv.items_needing_reorder(limit=-1))

    show("9. State after all those failures is unchanged")
    print("  traversal:", [p.sku for p in inv])
    print(f"  A-100 price {inv.get_product('A-100').price}, "
          f"qty {inv.get_product('A-100').quantity}")

    show("10. Empty system")
    empty = InventorySystem()
    print(f"  size {len(empty)}, lookup {empty.get_product('x')}, "
          f"urgent {empty.most_urgent_reorder()}, "
          f"range {empty.products_in_price_range(0, 100)}")


if __name__ == "__main__":
    main()
