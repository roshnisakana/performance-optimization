"""
sales_analytics_optimized.py
------------------------------
Same functionality as sales_analytics_baseline.py, with every bottleneck
identified by profiling fixed:

  1. find_duplicate_order_ids   : O(n^2) nested loop -> O(n) with Counter
  2. compute_revenue_by_customer: O(n*m) re-scan      -> O(n) single pass
  3. is_blocked / filter        : list membership     -> set membership
  4. validate_date_format       : regex recompiled     -> compiled once at
                                   every call            module import time
  5. rank_customers_by_revenue  : hand-rolled bubble   -> built-in sorted()
                                   sort O(n^2)

Data generation is unchanged (it was never a bottleneck) so the two
modules can be run against identical input for a fair, apples-to-apples
comparison, and build_summary_report produces byte-for-byte identical
output to the baseline (same formatting, built more efficiently).
"""

import random
import re
from collections import Counter


# ---------------------------------------------------------------------------
# Synthetic data generation — unchanged from baseline (not a bottleneck)
# ---------------------------------------------------------------------------

CUSTOMER_POOL = [f"Customer_{i:04d}" for i in range(400)]
PRODUCT_POOL = ["Widget", "Gadget", "Gizmo", "Doohickey", "Thingamajig", "Contraption"]


def generate_sales_data(n=6000, seed=42, duplicate_rate=0.03):
    """Generate n synthetic sales records, with some duplicate order_ids
    injected on purpose (simulating double-submitted orders)."""
    rng = random.Random(seed)
    records = []
    for i in range(n):
        order_id = f"ORD{i:06d}"
        record = {
            "order_id": order_id,
            "customer": rng.choice(CUSTOMER_POOL),
            "product": rng.choice(PRODUCT_POOL),
            "amount": round(rng.uniform(5.0, 500.0), 2),
            "date": f"2026-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}",
        }
        records.append(record)
        if i > 0 and rng.random() < duplicate_rate:
            records.append(dict(records[rng.randint(0, i)]))
    return records


# ---------------------------------------------------------------------------
# Fix 1: duplicate detection — O(n) with a Counter instead of O(n^2) pairwise
# ---------------------------------------------------------------------------

def find_duplicate_order_ids(records):
    """Return the set of order_ids that appear more than once."""
    counts = Counter(r["order_id"] for r in records)
    return {order_id for order_id, count in counts.items() if count > 1}


# ---------------------------------------------------------------------------
# Fix 2: revenue aggregation — single pass instead of re-scanning per customer
# ---------------------------------------------------------------------------

def compute_revenue_by_customer(records):
    """Return {customer: total_revenue} for every customer in records.

    A plain dict is used (not defaultdict) so that key insertion order
    matches the baseline's first-seen order exactly, keeping the two
    modules' output byte-for-byte comparable.
    """
    revenue_by_customer = {}
    for record in records:
        customer = record["customer"]
        if customer not in revenue_by_customer:
            revenue_by_customer[customer] = 0.0
        revenue_by_customer[customer] += record["amount"]
    return revenue_by_customer


# ---------------------------------------------------------------------------
# Fix 3: date validation — regex compiled once at import time, not per call
# ---------------------------------------------------------------------------

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validate_date_format(date_str):
    """Return True if date_str looks like YYYY-MM-DD."""
    return bool(_DATE_RE.match(date_str))


# ---------------------------------------------------------------------------
# Fix 4: blocklist check — set membership (O(1)) instead of list (O(k))
# ---------------------------------------------------------------------------

def is_blocked(customer, blocklist_set):
    """Return True if customer is on the (set-based) blocklist."""
    return customer in blocklist_set


def filter_blocked_records(records, blocklist):
    """Return only the records whose customer is NOT on the blocklist.

    Accepts the same list `blocklist` the baseline uses; converts it to a
    set exactly once, rather than re-scanning a list on every record.
    """
    blocklist_set = set(blocklist)
    return [r for r in records if not is_blocked(r["customer"], blocklist_set)]


# ---------------------------------------------------------------------------
# Fix 5: ranking — built-in sorted() (Timsort, O(n log n)) instead of bubble
# sort. sorted() is stable, matching the baseline's stable bubble sort, so
# tie ordering is identical between the two modules.
# ---------------------------------------------------------------------------

def rank_customers_by_revenue(revenue_by_customer):
    """Return a list of (customer, revenue) tuples, highest revenue first."""
    return sorted(revenue_by_customer.items(), key=lambda item: item[1], reverse=True)


# ---------------------------------------------------------------------------
# Report building — same content as baseline, built with list + join instead
# of repeated string concatenation
# ---------------------------------------------------------------------------

def build_summary_report(records, ranked_customers, duplicate_ids):
    """Build the same multi-section plain-text report as the baseline."""
    parts = []
    parts.append("=" * 60 + "\n")
    parts.append("SALES ANALYTICS REPORT\n")
    parts.append("=" * 60 + "\n\n")

    parts.append(f"Total records processed: {len(records)}\n")
    parts.append(f"Duplicate order IDs found: {len(duplicate_ids)}\n\n")

    parts.append("-" * 60 + "\n")
    parts.append("Revenue by customer (highest first)\n")
    parts.append("-" * 60 + "\n")
    for customer, revenue in ranked_customers:
        parts.append(f"{customer:<20} ${revenue:>10.2f}\n")

    parts.append("\n" + "-" * 60 + "\n")
    parts.append("Per-order detail\n")
    parts.append("-" * 60 + "\n")
    for record in records:
        valid = validate_date_format(record["date"])
        parts.append(
            f"{record['order_id']}  {record['customer']:<14}  "
            f"{record['product']:<12}  ${record['amount']:>8.2f}  "
            f"{record['date']}  (valid_date={valid})\n"
        )

    return "".join(parts)


# ---------------------------------------------------------------------------
# Orchestration — same signature and return shape as the baseline
# ---------------------------------------------------------------------------

def process_sales_data(n=6000, blocklist_size=80, seed=42):
    """Run the full pipeline and return (report_string, stats_dict)."""
    records = generate_sales_data(n=n, seed=seed)

    rng = random.Random(seed + 1)
    blocklist = rng.sample(CUSTOMER_POOL, min(blocklist_size, len(CUSTOMER_POOL)))

    duplicate_ids = find_duplicate_order_ids(records)
    filtered_records = filter_blocked_records(records, blocklist)
    revenue_by_customer = compute_revenue_by_customer(filtered_records)
    ranked_customers = rank_customers_by_revenue(revenue_by_customer)
    report = build_summary_report(filtered_records, ranked_customers, duplicate_ids)

    stats = {
        "total_records": len(records),
        "filtered_records": len(filtered_records),
        "duplicate_count": len(duplicate_ids),
        "unique_customers": len(revenue_by_customer),
        "total_revenue": round(sum(revenue_by_customer.values()), 2),
    }
    return report, stats


if __name__ == "__main__":
    report, stats = process_sales_data()
    print(stats)
    print(report[:500], "...")
