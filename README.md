# Dynamic Inventory Management: Data Structures in Python

A dynamic inventory management system built on three data structures implemented
from scratch, each matched to one access pattern:

- **Hash table** (separate chaining + dynamic resizing) — O(1) average lookup by SKU
- **Skip list** (probabilistic, keyed by price) — O(log n + k) ordered and range queries
- **Indexed binary min-heap** (with decrease-key) — O(1) peek at the most urgent reorder

Everything is benchmarked against a naive list baseline so the gains are measured,
not assumed.

## Layout

```
inventory/
  product.py      Product record (single source of truth)
  hash_table.py   HashTable: chaining + resize
  skip_list.py    SkipList: ordered index + range queries
  min_heap.py     MinHeap: indexed priority queue
  naive.py        NaiveInventory: list-based baseline
  system.py       InventorySystem: wires the three indexes together
demo.py           End-to-end walkthrough of the key operations
poc_demo.py       Phase 2 walkthrough: normal use, then edge cases and errors
benchmark.py      Performance comparison + matplotlib graphs -> figures/
tests/
  test_inventory.py   21 unit tests + a differential fuzz test
  test_edge_cases.py  35 edge-case and error-handling tests (Phase 2)
report.docx       Final written report (APA)
presentation.pptx 15-minute deck with the spoken script in the notes
```

## Requirements

- Python 3.10+ (developed on 3.14)
- `matplotlib` for `benchmark.py` only (`pip install matplotlib`)
- The library, demo, and tests use the standard library only

## Running it

```bash
python demo.py                      # see the three operations in action
python -m unittest discover -s tests  # run the test suite (56 tests)
python benchmark.py                 # regenerate the timing graphs in figures/
```

## Notes

- The skip list accepts an optional `seed` so benchmarks and tests are reproducible.
- The differential test in `tests/test_inventory.py` checks the optimized system
  against the naive baseline on a random workload. It is what caught the original
  heap sift-down bug described in the report.

## Phase 2: proof-of-concept hardening

Phase 2 keeps the Phase 1 structures and adds input validation, error handling,
a traversal API and a scripted demo that shows the failures on purpose.

```bash
python poc_demo.py                    # insert, search, traverse, range, reorder, delete, then errors
python -m unittest discover -s tests  # 56 tests, standard library only
```

What was added:

- `Product` validates every write, not just construction. Wrong types raise
  `TypeError`; NaN, infinite or negative values and blank SKUs raise `ValueError`.
- `InventorySystem` raises `KeyError` for unknown or duplicate SKUs, rejects
  non-`Product` objects, and refuses inverted or NaN price ranges and negative
  report limits. A rejected call leaves all three indexes unchanged.
- New operations: `adjust_quantity(sku, delta)` (sales and deliveries, cannot go
  below zero) and iteration over the system in `(price, SKU)` order.
- `tests/test_edge_cases.py`: empty structures, equal prices, heap root updates,
  the exact resize boundary (7th insert into an 8-bucket table), forced hash
  collisions, and state-unchanged-after-failure checks.

Known limitation: `get_product` returns the live object, so writing
`product.price = ...` directly bypasses the price index. Use
`InventorySystem.update_price`.
