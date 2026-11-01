"""Performance comparison between the naive baseline and the optimised system.

Run with ``python benchmark.py`` from the project root. For a range of catalogue
sizes it times three operations on both implementations:

    1. point lookup by SKU
    2. price-range query
    3. reorder report (the ten most urgent low-stock items)

It prints a results table, writes the raw numbers to ``figures/benchmark.csv``,
and saves log-log plots as PNGs under ``figures/``. The plots and the CSV are
what the written report's performance section is built on, so the numbers there
are measured, not guessed.
"""

from __future__ import annotations

import csv
import os
import random
from time import perf_counter

import matplotlib

matplotlib.use("Agg")  # render to files, no display needed
import matplotlib.pyplot as plt  # noqa: E402

from inventory import InventorySystem, NaiveInventory, Product  # noqa: E402

SIZES = [1_000, 2_000, 5_000, 10_000, 20_000, 50_000]
LOOKUPS = 300
RANGE_QUERIES = 50
REORDER_CALLS = 50
BATCH_REPEATS = 3  # repeat each timed batch to smooth out scheduler noise
NARROW_WIDTH = 8.0  # selective query: returns roughly 0.8% of the catalogue
WIDE_WIDTH = 200.0  # broad query: returns roughly a fifth of the catalogue
FIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures")


def make_products(n: int, rng: random.Random) -> list[Product]:
    """Generate ``n`` products with random prices, quantities and thresholds."""
    products = []
    for i in range(n):
        products.append(
            Product(
                sku=f"SKU-{i:07d}",
                name=f"Item {i}",
                price=round(rng.uniform(1.0, 1000.0), 2),
                quantity=rng.randint(0, 200),
                category=rng.choice(["a", "b", "c", "d"]),
                reorder_threshold=rng.randint(5, 40),
            )
        )
    return products


def time_op(fn, repeats: int) -> float:
    """Return average seconds per call of ``fn`` over ``repeats`` runs."""
    start = perf_counter()
    for _ in range(repeats):
        fn()
    return (perf_counter() - start) / repeats


def run() -> list[dict]:
    """Benchmark every size and return a list of per-size result rows."""
    rng = random.Random(42)
    rows: list[dict] = []

    for n in SIZES:
        products = make_products(n, rng)
        skus = [p.sku for p in products]

        system = InventorySystem(skiplist_seed=1)
        for p in products:
            system.add_product(p)

        naive = NaiveInventory()
        # Each implementation needs its own Product objects.
        naive.bulk_add([
            Product(p.sku, p.name, p.price, p.quantity, p.category,
                    p.reorder_threshold)
            for p in products
        ])

        lookup_targets = [rng.choice(skus) for _ in range(LOOKUPS)]
        narrow_lows = [rng.uniform(1.0, 990.0) for _ in range(RANGE_QUERIES)]
        wide_lows = [rng.uniform(1.0, 800.0) for _ in range(RANGE_QUERIES)]

        def sys_lookup(targets=lookup_targets, s=system):
            for sku in targets:
                s.get_product(sku)

        def naive_lookup(targets=lookup_targets, s=naive):
            for sku in targets:
                s.get_product(sku)

        def sys_narrow(lows=narrow_lows, s=system):
            for lo in lows:
                s.products_in_price_range(lo, lo + NARROW_WIDTH)

        def naive_narrow(lows=narrow_lows, s=naive):
            for lo in lows:
                s.products_in_price_range(lo, lo + NARROW_WIDTH)

        def sys_wide(lows=wide_lows, s=system):
            for lo in lows:
                s.products_in_price_range(lo, lo + WIDE_WIDTH)

        def naive_wide(lows=wide_lows, s=naive):
            for lo in lows:
                s.products_in_price_range(lo, lo + WIDE_WIDTH)

        def sys_reorder(s=system):
            s.items_needing_reorder(limit=10)

        def naive_reorder(s=naive):
            s.items_needing_reorder(limit=10)

        row = {
            "n": n,
            "sys_lookup": time_op(sys_lookup, BATCH_REPEATS) / LOOKUPS,
            "naive_lookup": time_op(naive_lookup, BATCH_REPEATS) / LOOKUPS,
            "sys_narrow": time_op(sys_narrow, BATCH_REPEATS) / RANGE_QUERIES,
            "naive_narrow": time_op(naive_narrow, BATCH_REPEATS) / RANGE_QUERIES,
            "sys_wide": time_op(sys_wide, BATCH_REPEATS) / RANGE_QUERIES,
            "naive_wide": time_op(naive_wide, BATCH_REPEATS) / RANGE_QUERIES,
            "sys_reorder": time_op(sys_reorder, REORDER_CALLS),
            "naive_reorder": time_op(naive_reorder, REORDER_CALLS),
        }
        rows.append(row)
        print(
            f"n={n:>6}  "
            f"lookup: naive {row['naive_lookup']*1e6:8.2f}us  "
            f"sys {row['sys_lookup']*1e6:7.3f}us  "
            f"| narrow range: naive {row['naive_narrow']*1e3:7.3f}ms  "
            f"sys {row['sys_narrow']*1e3:6.3f}ms  "
            f"| reorder: naive {row['naive_reorder']*1e3:7.3f}ms  "
            f"sys {row['sys_reorder']*1e3:6.3f}ms"
        )
    return rows


def write_csv(rows: list[dict]) -> str:
    """Save the raw results to a CSV and return its path."""
    os.makedirs(FIG_DIR, exist_ok=True)
    path = os.path.join(FIG_DIR, "benchmark.csv")
    with open(path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return path


def _plot(rows, naive_key, sys_key, title, ylabel, scale, filename) -> str:
    """Draw one naive-vs-optimised log-log chart and save it."""
    ns = [r["n"] for r in rows]
    naive_y = [r[naive_key] * scale for r in rows]
    sys_y = [r[sys_key] * scale for r in rows]

    fig, ax = plt.subplots(figsize=(6.2, 4.0))
    ax.plot(ns, naive_y, "o-", color="#c0392b", label="Naive baseline")
    ax.plot(ns, sys_y, "s-", color="#1f6feb", label="Optimised system")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Number of products (log scale)")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, which="both", linestyle=":", linewidth=0.6, alpha=0.6)
    ax.legend()
    fig.tight_layout()
    path = os.path.join(FIG_DIR, filename)
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def make_plots(rows: list[dict]) -> list[str]:
    """Produce all four comparison figures and return their paths."""
    os.makedirs(FIG_DIR, exist_ok=True)
    return [
        _plot(rows, "naive_lookup", "sys_lookup",
              "Point lookup by SKU", "Avg time per lookup (microseconds)",
              1e6, "fig_lookup.png"),
        _plot(rows, "naive_narrow", "sys_narrow",
              "Selective price-range query (narrow band)",
              "Avg time per query (milliseconds)", 1e3, "fig_range_narrow.png"),
        _plot(rows, "naive_wide", "sys_wide",
              "Broad price-range query (wide band)",
              "Avg time per query (milliseconds)", 1e3, "fig_range_wide.png"),
        _plot(rows, "naive_reorder", "sys_reorder",
              "Reorder report (10 most urgent)", "Avg time per call (milliseconds)",
              1e3, "fig_reorder.png"),
    ]


def main() -> None:
    print("Benchmarking naive baseline vs optimised system...\n")
    rows = run()
    csv_path = write_csv(rows)
    fig_paths = make_plots(rows)

    biggest = rows[-1]
    print("\nAt the largest size tested "
          f"({biggest['n']:,} products) the optimised system is:")
    print(f"  lookup:        {biggest['naive_lookup']/biggest['sys_lookup']:7.0f}x faster")
    print(f"  narrow range:  {biggest['naive_narrow']/biggest['sys_narrow']:7.1f}x faster")
    print(f"  wide range:    {biggest['naive_wide']/biggest['sys_wide']:7.1f}x faster")
    print(f"  reorder:       {biggest['naive_reorder']/biggest['sys_reorder']:7.0f}x faster")
    print(f"\nWrote {csv_path}")
    for p in fig_paths:
        print(f"Wrote {p}")


if __name__ == "__main__":
    main()
