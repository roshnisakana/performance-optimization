"""
benchmark_functions.py
------------------------
Isolated, function-level before/after benchmarks using timeit, run against
identical input data so each optimization's individual contribution can be
measured on its own (separately from the full-pipeline benchmark).
"""

import timeit
import random

import sales_analytics_baseline as base
import sales_analytics_optimized as opt


def make_shared_dataset():
    records = base.generate_sales_data(n=6000, seed=42)
    rng = random.Random(43)
    blocklist = rng.sample(base.CUSTOMER_POOL, 80)
    filtered_records_baseline = base.filter_blocked_records(records, blocklist)
    revenue = base.compute_revenue_by_customer(filtered_records_baseline)
    return records, blocklist, filtered_records_baseline, revenue


records, blocklist, filtered_records, revenue = make_shared_dataset()
blocklist_set = set(blocklist)

RESULTS = []


def bench(label, baseline_stmt, optimized_stmt, globals_dict, number=5):
    t_base = timeit.timeit(baseline_stmt, globals=globals_dict, number=number) / number
    t_opt = timeit.timeit(optimized_stmt, globals=globals_dict, number=number) / number
    speedup = t_base / t_opt if t_opt > 0 else float("inf")
    RESULTS.append((label, t_base, t_opt, speedup))
    print(f"{label:38s}  baseline={t_base*1000:9.3f} ms   optimized={t_opt*1000:9.3f} ms   speedup={speedup:6.1f}x")


if __name__ == "__main__":
    print(f"{'Function':38s}  {'Baseline':>13s}   {'Optimized':>13s}   Speedup")
    print("-" * 90)

    bench(
        "find_duplicate_order_ids",
        "base.find_duplicate_order_ids(records)",
        "opt.find_duplicate_order_ids(records)",
        {"base": base, "opt": opt, "records": records},
        number=3,
    )

    bench(
        "compute_revenue_by_customer",
        "base.compute_revenue_by_customer(filtered_records)",
        "opt.compute_revenue_by_customer(filtered_records)",
        {"base": base, "opt": opt, "filtered_records": filtered_records},
        number=20,
    )

    bench(
        "filter_blocked_records",
        "base.filter_blocked_records(records, blocklist)",
        "opt.filter_blocked_records(records, blocklist)",
        {"base": base, "opt": opt, "records": records, "blocklist": blocklist},
        number=50,
    )

    bench(
        "rank_customers_by_revenue",
        "base.rank_customers_by_revenue(revenue)",
        "opt.rank_customers_by_revenue(revenue)",
        {"base": base, "opt": opt, "revenue": revenue},
        number=200,
    )

    bench(
        "validate_date_format (x4923 calls)",
        "[base.validate_date_format(r['date']) for r in filtered_records]",
        "[opt.validate_date_format(r['date']) for r in filtered_records]",
        {"base": base, "opt": opt, "filtered_records": filtered_records},
        number=20,
    )

    ranked = opt.rank_customers_by_revenue(revenue)
    duplicate_ids = opt.find_duplicate_order_ids(records)
    bench(
        "build_summary_report",
        "base.build_summary_report(filtered_records, ranked, duplicate_ids)",
        "opt.build_summary_report(filtered_records, ranked, duplicate_ids)",
        {"base": base, "opt": opt, "filtered_records": filtered_records,
         "ranked": ranked, "duplicate_ids": duplicate_ids},
        number=10,
    )

    print()
    print("Full pipeline (process_sales_data):")
    bench(
        "process_sales_data (end-to-end)",
        "base.process_sales_data()",
        "opt.process_sales_data()",
        {"base": base, "opt": opt},
        number=3,
    )
