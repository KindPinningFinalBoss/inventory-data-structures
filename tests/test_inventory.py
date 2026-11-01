"""Correctness and edge-case tests for every data structure and the system.

Run from the project root with either::

    python -m unittest discover -s tests
    python tests/test_inventory.py

The tests check normal behaviour, boundary conditions (empty structures, single
elements, duplicate keys) and that the optimised system agrees with the naive
baseline on a randomised workload. That last cross-check is the real safety net:
two independent implementations are unlikely to share the same bug.
"""

from __future__ import annotations

import os
import random
import sys
import unittest

# Allow "python tests/test_inventory.py" by putting the project root on the path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inventory import (  # noqa: E402  (import after path fix is intentional)
    HashTable,
    InventorySystem,
    MinHeap,
    NaiveInventory,
    Product,
    SkipList,
)


class TestProduct(unittest.TestCase):
    def test_valid_product(self):
        p = Product("A1", "Widget", 9.99, 5, "misc", 10)
        self.assertEqual(p.sku, "A1")
        self.assertAlmostEqual(p.urgency, 0.5)
        self.assertTrue(p.needs_reorder)

    def test_rejects_bad_values(self):
        with self.assertRaises(ValueError):
            Product("", "No SKU", 1.0, 1, "misc")
        with self.assertRaises(ValueError):
            Product("A1", "Negative price", -1.0, 1, "misc")
        with self.assertRaises(ValueError):
            Product("A1", "Negative qty", 1.0, -1, "misc")
        with self.assertRaises(ValueError):
            Product("A1", "Bad threshold", 1.0, 1, "misc", 0)


class TestHashTable(unittest.TestCase):
    def test_put_get_update(self):
        t = HashTable()
        t.put("x", 1)
        t.put("y", 2)
        self.assertEqual(t.get("x"), 1)
        t.put("x", 99)  # update, not insert
        self.assertEqual(t.get("x"), 99)
        self.assertEqual(len(t), 2)

    def test_missing_key(self):
        t = HashTable()
        self.assertIsNone(t.get("nope"))
        self.assertEqual(t.get("nope", "default"), "default")
        with self.assertRaises(KeyError):
            t.remove("nope")

    def test_remove(self):
        t = HashTable()
        t.put("a", 1)
        self.assertEqual(t.remove("a"), 1)
        self.assertNotIn("a", t)
        self.assertEqual(len(t), 0)

    def test_resizes_and_keeps_everything(self):
        t = HashTable()
        start_capacity = t.capacity
        for i in range(1000):
            t.put(f"key-{i}", i)
        self.assertEqual(len(t), 1000)
        self.assertGreater(t.capacity, start_capacity)  # it grew
        self.assertLessEqual(t.load_factor, 0.75)
        for i in range(1000):
            self.assertEqual(t.get(f"key-{i}"), i)


class TestSkipList(unittest.TestCase):
    def test_insert_search_delete(self):
        s = SkipList(seed=1)
        for key in [5, 1, 9, 3, 7]:
            s.insert(key, f"v{key}")
        self.assertEqual(s.search(3), "v3")
        self.assertIsNone(s.search(100))
        self.assertTrue(s.delete(9))
        self.assertFalse(s.delete(9))  # already gone
        self.assertEqual(len(s), 4)

    def test_sorted_iteration(self):
        s = SkipList(seed=2)
        keys = list(range(50))
        random.Random(0).shuffle(keys)
        for k in keys:
            s.insert(k, k)
        self.assertEqual([k for k, _ in s], sorted(range(50)))

    def test_range_query(self):
        s = SkipList(seed=3)
        for k in range(0, 100, 5):  # 0, 5, 10, ... 95
            s.insert(k, k)
        got = [k for k, _ in s.range_query(23, 47)]
        self.assertEqual(got, [25, 30, 35, 40, 45])

    def test_empty_range(self):
        s = SkipList(seed=4)
        s.insert(10, "ten")
        self.assertEqual(list(s.range_query(20, 30)), [])


class TestMinHeap(unittest.TestCase):
    def test_push_pop_order(self):
        h = MinHeap()
        for pr, item in [(5, "e"), (1, "a"), (3, "c"), (2, "b"), (4, "d")]:
            h.push(pr, item)
        popped = [h.pop()[1] for _ in range(len(h))]
        self.assertEqual(popped, ["a", "b", "c", "d", "e"])

    def test_peek_and_empty(self):
        h = MinHeap()
        self.assertIsNone(h.peek())
        with self.assertRaises(IndexError):
            h.pop()
        h.push(7, "x")
        self.assertEqual(h.peek(), (7, "x"))

    def test_decrease_key(self):
        h = MinHeap()
        h.push(10, "a")
        h.push(20, "b")
        h.push(30, "c")
        h.update("c", 1)  # c becomes the most urgent
        self.assertEqual(h.peek(), (1, "c"))

    def test_remove_arbitrary(self):
        h = MinHeap()
        for pr, item in [(5, "e"), (1, "a"), (3, "c")]:
            h.push(pr, item)
        h.remove("a")
        self.assertNotIn("a", h)
        self.assertEqual(h.peek(), (3, "c"))


class TestInventorySystem(unittest.TestCase):
    def _sample(self) -> InventorySystem:
        system = InventorySystem(skiplist_seed=11)
        system.add_product(Product("S1", "A", 10.0, 2, "cat", 5))
        system.add_product(Product("S2", "B", 20.0, 50, "cat", 5))
        system.add_product(Product("S3", "C", 30.0, 1, "cat", 5))
        return system

    def test_lookup_and_duplicate(self):
        s = self._sample()
        self.assertEqual(s.get_product("S2").name, "B")
        with self.assertRaises(KeyError):
            s.add_product(Product("S1", "dup", 1.0, 1, "cat"))

    def test_price_range_sorted(self):
        s = self._sample()
        names = [p.name for p in s.products_in_price_range(10.0, 25.0)]
        self.assertEqual(names, ["A", "B"])

    def test_reorder_priority(self):
        s = self._sample()
        # S3 (1/5) is more urgent than S1 (2/5); S2 (50/5) is fine.
        self.assertEqual(s.most_urgent_reorder().sku, "S3")
        urgent = [p.sku for p in s.items_needing_reorder()]
        self.assertEqual(urgent, ["S3", "S1"])

    def test_quantity_update_moves_priority(self):
        s = self._sample()
        s.update_quantity("S3", 100)  # no longer urgent
        self.assertEqual(s.most_urgent_reorder().sku, "S1")

    def test_price_update_rekeys(self):
        s = self._sample()
        s.update_price("S1", 99.0)  # was cheapest, now dearest
        names = [p.name for p in s.products_in_price_range(0.0, 1000.0)]
        self.assertEqual(names, ["B", "C", "A"])

    def test_remove(self):
        s = self._sample()
        s.remove_product("S2")
        self.assertNotIn("S2", s)
        self.assertEqual(len(s), 2)
        with self.assertRaises(KeyError):
            s.remove_product("S2")


class TestSystemMatchesBaseline(unittest.TestCase):
    """Fuzz test: the optimised system must agree with the naive baseline."""

    def test_random_workload_agrees(self):
        rng = random.Random(2024)
        fast = InventorySystem(skiplist_seed=99)
        slow = NaiveInventory()
        categories = ["a", "b", "c"]

        for i in range(400):
            sku = f"SKU-{i}"
            product_fast = Product(
                sku, f"name-{i}",
                round(rng.uniform(1, 500), 2),
                rng.randint(0, 100),
                rng.choice(categories),
                rng.randint(5, 30),
            )
            # The baseline needs its own object (quantities mutate independently).
            product_slow = Product(
                sku, product_fast.name, product_fast.price,
                product_fast.quantity, product_fast.category,
                product_fast.reorder_threshold,
            )
            fast.add_product(product_fast)
            slow.add_product(product_slow)

        # Random quantity updates on both.
        for _ in range(200):
            sku = f"SKU-{rng.randint(0, 399)}"
            new_qty = rng.randint(0, 100)
            fast.update_quantity(sku, new_qty)
            slow.update_quantity(sku, new_qty)

        # Point lookups agree.
        for _ in range(100):
            sku = f"SKU-{rng.randint(0, 399)}"
            self.assertEqual(
                fast.get_product(sku).quantity,
                slow.get_product(sku).quantity,
            )

        # Price-range queries agree (compare as sorted SKU sets per price order).
        for _ in range(20):
            lo = rng.uniform(1, 400)
            hi = lo + rng.uniform(10, 100)
            fast_skus = [p.sku for p in fast.products_in_price_range(lo, hi)]
            slow_skus = [p.sku for p in slow.products_in_price_range(lo, hi)]
            self.assertEqual(sorted(fast_skus), sorted(slow_skus))
            # Prices come back non-decreasing.
            prices = [fast.get_product(s).price for s in fast_skus]
            self.assertEqual(prices, sorted(prices))

        # The set of items needing reorder agrees.
        fast_reorder = sorted(p.sku for p in fast.items_needing_reorder())
        slow_reorder = sorted(p.sku for p in slow.items_needing_reorder())
        self.assertEqual(fast_reorder, slow_reorder)


if __name__ == "__main__":
    unittest.main(verbosity=2)
