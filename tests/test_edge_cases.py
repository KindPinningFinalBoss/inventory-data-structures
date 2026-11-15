"""Phase 2 edge-case and error-handling tests.

These sit next to ``test_inventory.py`` and focus on the awkward inputs: bad
types, NaN prices, empty structures, equal prices, the heap's root, and the
exact load-factor boundary where the hash table resizes.

Run everything with ``python -m unittest discover -s tests``.
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inventory import (  # noqa: E402
    HashTable,
    InventorySystem,
    MinHeap,
    Product,
    SkipList,
)


class TestProductValidation(unittest.TestCase):
    def test_nan_and_infinite_price_rejected(self):
        for bad in (float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                Product("A", "x", bad, 1, "c")

    def test_wrong_types_rejected(self):
        with self.assertRaises(TypeError):
            Product("A", "x", "9.99", 1, "c")       # price as text
        with self.assertRaises(TypeError):
            Product("A", "x", 9.99, 2.5, "c")       # fractional quantity
        with self.assertRaises(TypeError):
            Product("A", "x", 9.99, True, "c")      # bool is not a count
        with self.assertRaises(TypeError):
            Product(42, "x", 9.99, 1, "c")          # sku must be text

    def test_blank_sku_rejected(self):
        with self.assertRaises(ValueError):
            Product("   ", "x", 1.0, 1, "c")

    def test_validation_also_runs_on_assignment(self):
        p = Product("A", "x", 1.0, 5, "c")
        with self.assertRaises(ValueError):
            p.quantity = -3
        self.assertEqual(p.quantity, 5)  # the bad write did not stick

    def test_zero_price_and_zero_quantity_are_legal(self):
        p = Product("A", "free sample", 0, 0, "c")
        self.assertEqual(p.urgency, 0)
        self.assertTrue(p.needs_reorder)


class TestHashTableEdges(unittest.TestCase):
    def test_resize_happens_exactly_past_load_factor(self):
        t = HashTable()
        for i in range(6):                       # 6 / 8 = 0.75, not over
            t.put(f"k{i}", i)
        self.assertEqual(t.capacity, 8)
        t.put("k6", 6)                           # 7 / 8 = 0.875, over
        self.assertEqual(t.capacity, 16)
        self.assertTrue(all(t.get(f"k{i}") == i for i in range(7)))

    def test_updating_existing_key_never_resizes(self):
        t = HashTable()
        for i in range(6):
            t.put(f"k{i}", i)
        for _ in range(50):
            t.put("k0", "again")
        self.assertEqual(t.capacity, 8)
        self.assertEqual(len(t), 6)

    def test_chain_removal_in_the_middle(self):
        class AlwaysCollides(HashTable):
            def _hash(self, key):  # every key lands in one bucket
                return 1

        t = AlwaysCollides()
        for k in "abc":
            t.put(k, k.upper())
        self.assertEqual(t.remove("b"), "B")
        self.assertEqual(t.get("a"), "A")
        self.assertEqual(t.get("c"), "C")
        self.assertEqual(len(t), 2)

    def test_empty_table(self):
        t = HashTable()
        self.assertEqual(len(t), 0)
        self.assertEqual(list(t), [])
        self.assertEqual(list(t.items()), [])
        with self.assertRaises(KeyError):
            t["ghost"]


class TestSkipListEdges(unittest.TestCase):
    def test_empty_list(self):
        s = SkipList(seed=1)
        self.assertEqual(len(s), 0)
        self.assertIsNone(s.search(1))
        self.assertFalse(s.delete(1))
        self.assertEqual(list(s), [])
        self.assertEqual(list(s.range_query(0, 10)), [])

    def test_insert_same_key_updates_value(self):
        s = SkipList(seed=1)
        s.insert(5, "old")
        s.insert(5, "new")
        self.assertEqual(len(s), 1)
        self.assertEqual(s.search(5), "new")

    def test_range_bounds_are_inclusive(self):
        s = SkipList(seed=2)
        for k in (10, 20, 30):
            s.insert(k, k)
        self.assertEqual([k for k, _ in s.range_query(10, 30)], [10, 20, 30])
        self.assertEqual([k for k, _ in s.range_query(20, 20)], [20])

    def test_inverted_range_is_empty(self):
        s = SkipList(seed=2)
        s.insert(10, 10)
        self.assertEqual(list(s.range_query(30, 10)), [])

    def test_delete_everything_then_reuse(self):
        s = SkipList(seed=3)
        for k in range(100):
            s.insert(k, k)
        for k in range(100):
            self.assertTrue(s.delete(k))
        self.assertEqual(len(s), 0)
        self.assertEqual(list(s), [])
        s.insert(7, "back")
        self.assertEqual(s.search(7), "back")


class TestMinHeapEdges(unittest.TestCase):
    def _filled(self):
        h = MinHeap()
        for pr, item in [(5, "e"), (1, "a"), (3, "c"), (2, "b"), (4, "d")]:
            h.push(pr, item)
        return h

    def test_decrease_key_on_root_keeps_it_on_top(self):
        h = self._filled()
        h.update("a", 0)
        self.assertEqual(h.peek(), (0, "a"))

    def test_increase_key_on_root_sinks_it(self):
        h = self._filled()
        h.update("a", 99)
        self.assertEqual(h.peek(), (2, "b"))
        order = [h.pop()[1] for _ in range(len(h))]
        self.assertEqual(order, ["b", "c", "d", "e", "a"])

    def test_remove_root_and_remove_last(self):
        h = self._filled()
        h.remove("a")                      # the root
        self.assertEqual(h.peek(), (2, "b"))
        last_item = h._heap[-1][1]         # whatever sits at the end
        h.remove(last_item)
        self.assertNotIn(last_item, h)
        popped = [h.pop()[0] for _ in range(len(h))]
        self.assertEqual(popped, sorted(popped))

    def test_remove_only_element(self):
        h = MinHeap()
        h.push(1, "solo")
        h.remove("solo")
        self.assertEqual(len(h), 0)
        self.assertIsNone(h.peek())

    def test_missing_item_errors(self):
        h = MinHeap()
        with self.assertRaises(KeyError):
            h.update("nope", 1)
        with self.assertRaises(KeyError):
            h.remove("nope")

    def test_equal_priorities_are_all_kept(self):
        h = MinHeap()
        for item in "dbca":
            h.push(1, item)
        self.assertEqual([h.pop()[1] for _ in range(4)], ["a", "b", "c", "d"])

    def test_push_existing_item_updates_instead_of_duplicating(self):
        h = MinHeap()
        h.push(5, "x")
        h.push(2, "x")
        self.assertEqual(len(h), 1)
        self.assertEqual(h.peek(), (2, "x"))

    def test_position_map_stays_in_step_under_churn(self):
        import random
        rng = random.Random(5)
        h = MinHeap()
        for i in range(200):
            h.push(rng.random(), f"i{i}")
        for _ in range(500):
            h.update(f"i{rng.randrange(200)}", rng.random())
        for item, idx in h._pos.items():
            self.assertEqual(h._heap[idx][1], item)
        out = [h.pop()[0] for _ in range(len(h))]
        self.assertEqual(out, sorted(out))


class TestSystemErrorHandling(unittest.TestCase):
    def _system(self):
        s = InventorySystem(skiplist_seed=4)
        s.add_product(Product("S1", "A", 10.0, 2, "c", 5))
        s.add_product(Product("S2", "B", 10.0, 50, "c", 5))   # same price as S1
        s.add_product(Product("S3", "C", 30.0, 1, "c", 5))
        return s

    def test_empty_system(self):
        s = InventorySystem()
        self.assertEqual(len(s), 0)
        self.assertIsNone(s.get_product("x"))
        self.assertIsNone(s.most_urgent_reorder())
        self.assertEqual(s.items_needing_reorder(), [])
        self.assertEqual(s.products_in_price_range(0, 100), [])
        self.assertEqual(list(s), [])

    def test_add_rejects_non_product(self):
        with self.assertRaises(TypeError):
            InventorySystem().add_product({"sku": "x"})

    def test_failed_add_leaves_no_trace(self):
        s = self._system()
        with self.assertRaises(KeyError):
            s.add_product(Product("S1", "dup", 1.0, 1, "c"))
        self.assertEqual(len(s), 3)
        self.assertEqual(s.get_product("S1").name, "A")
        self.assertEqual(len(s.products_in_price_range(0, 5)), 0)

    def test_equal_prices_both_returned_in_sku_order(self):
        s = self._system()
        skus = [p.sku for p in s.products_in_price_range(10.0, 10.0)]
        self.assertEqual(skus, ["S1", "S2"])

    def test_removing_one_of_two_equal_prices_keeps_the_other(self):
        s = self._system()
        s.remove_product("S1")
        skus = [p.sku for p in s.products_in_price_range(10.0, 10.0)]
        self.assertEqual(skus, ["S2"])

    def test_update_price_to_same_value_is_harmless(self):
        s = self._system()
        s.update_price("S1", 10.0)
        self.assertEqual(len(s.products_in_price_range(0, 100)), 3)

    def test_missing_sku_errors(self):
        s = self._system()
        for call in (lambda: s.remove_product("zz"),
                     lambda: s.update_quantity("zz", 1),
                     lambda: s.update_price("zz", 1.0),
                     lambda: s.adjust_quantity("zz", 1)):
            with self.assertRaises(KeyError):
                call()

    def test_bad_values_leave_state_unchanged(self):
        s = self._system()
        with self.assertRaises(ValueError):
            s.update_quantity("S1", -1)
        with self.assertRaises(TypeError):
            s.update_quantity("S1", 2.5)
        with self.assertRaises(ValueError):
            s.update_price("S1", float("nan"))
        with self.assertRaises(ValueError):
            s.update_price("S1", -5)
        self.assertEqual(s.get_product("S1").quantity, 2)
        self.assertEqual(s.get_product("S1").price, 10.0)
        self.assertEqual(s.most_urgent_reorder().sku, "S3")
        self.assertEqual(len(s.products_in_price_range(10.0, 10.0)), 2)

    def test_adjust_quantity_cannot_go_negative(self):
        s = self._system()
        s.adjust_quantity("S2", -45)
        self.assertEqual(s.get_product("S2").quantity, 5)
        with self.assertRaises(ValueError):
            s.adjust_quantity("S2", -6)
        self.assertEqual(s.get_product("S2").quantity, 5)

    def test_bad_range_arguments(self):
        s = self._system()
        with self.assertRaises(ValueError):
            s.products_in_price_range(50, 10)
        with self.assertRaises(ValueError):
            s.products_in_price_range(float("nan"), 10)
        with self.assertRaises(TypeError):
            s.products_in_price_range("a", "z")

    def test_reorder_limit_handling(self):
        s = self._system()
        self.assertEqual(s.items_needing_reorder(limit=0), [])
        self.assertEqual([p.sku for p in s.items_needing_reorder(limit=1)], ["S3"])
        with self.assertRaises(ValueError):
            s.items_needing_reorder(limit=-1)

    def test_reorder_report_leaves_heap_untouched(self):
        s = self._system()
        before = len(s._reorder)
        first = [p.sku for p in s.items_needing_reorder()]
        second = [p.sku for p in s.items_needing_reorder()]
        self.assertEqual(first, second)
        self.assertEqual(len(s._reorder), before)

    def test_traversal_is_in_price_then_sku_order(self):
        s = self._system()
        self.assertEqual([p.sku for p in s], ["S1", "S2", "S3"])
        s.update_price("S1", 99.0)
        self.assertEqual([p.sku for p in s], ["S2", "S3", "S1"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
