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
benchmark.py      Performance comparison + matplotlib graphs -> figures/
tests/
  test_inventory.py  21 unit tests + a differential fuzz test
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
python -m unittest discover -s tests  # run the test suite (21 tests)
python benchmark.py                 # regenerate the timing graphs in figures/
```

## Notes

- The skip list accepts an optional `seed` so benchmarks and tests are reproducible.
- The differential test in `tests/test_inventory.py` checks the optimized system
  against the naive baseline on a random workload. It is what caught the original
  heap sift-down bug described in the report.
