"""
sales_analytics_baseline.py
----------------------------
A self-contained sales data analytics processor: generates a synthetic
dataset, then finds duplicate orders, computes per-customer revenue,
flags blocked customers, ranks customers by revenue, and builds a text
summary report.

This is the BASELINE version. It is functionally correct but written the
way a first draft often is: nested loops where a lookup structure would
do, a hand-rolled sort where a built-in would do, and a growing-string
report. Its performance is analyzed and improved in
sales_analytics_optimized.py.
"""

import random
import re


# ---------------------------------------------------------------------------
# Synthetic data generation (deterministic, seeded — no external files needed)
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
        # Occasionally duplicate a previous order (simulating a double
        # submission) so duplicate-detection has real work to do.
        if i > 0 and rng.random() < duplicate_rate:
            records.append(dict(records[rng.randint(0, i)]))
    return records


# ---------------------------------------------------------------------------
# Duplicate detection — BASELINE: O(n^2) nested-loop comparison
# ---------------------------------------------------------------------------

def find_duplicate_order_ids(records):
    """Return the set of order_ids that appear more than once."""
    duplicates = set()
    for i in range(len(records)):
        for j in range(len(records)):
            if i != j and records[i]["order_id"] == records[j]["order_id"]:
                duplicates.add(records[i]["order_id"])
    return duplicates


# ---------------------------------------------------------------------------
# Revenue aggregation — BASELINE: re-scans the whole dataset per customer
# ---------------------------------------------------------------------------

def compute_revenue_by_customer(records):
    """Return {customer: total_revenue} for every customer in records."""
    unique_customers = []
    for record in records:
        if record["customer"] not in unique_customers:
            unique_customers.append(record["customer"])

    revenue_by_customer = {}
    for customer in unique_customers:
        total = 0.0
        for record in records:
            if record["customer"] == customer:
                total += record["amount"]
        revenue_by_customer[customer] = total
    return revenue_by_customer


# ---------------------------------------------------------------------------
# Date validation — BASELINE: recompiles the regex on every single call
# ---------------------------------------------------------------------------

def validate_date_format(date_str):
    """Return True if date_str looks like YYYY-MM-DD."""
    pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    return bool(pattern.match(date_str))


# ---------------------------------------------------------------------------
# Blocklist check — BASELINE: list membership test (O(size of blocklist))
# ---------------------------------------------------------------------------

def is_blocked(customer, blocklist):
    """Return True if customer is on the (list-based) blocklist."""
    return customer in blocklist


def filter_blocked_records(records, blocklist):
    """Return only the records whose customer is NOT on the blocklist."""
    return [r for r in records if not is_blocked(r["customer"], blocklist)]


# ---------------------------------------------------------------------------
# Ranking — BASELINE: hand-rolled bubble sort instead of the built-in sorted()
# ---------------------------------------------------------------------------

def rank_customers_by_revenue(revenue_by_customer):
    """Return a list of (customer, revenue) tuples, highest revenue first."""
    items = list(revenue_by_customer.items())
    n = len(items)
    for i in range(n):
        for j in range(0, n - i - 1):
            if items[j][1] < items[j + 1][1]:
                items[j], items[j + 1] = items[j + 1], items[j]
    return items


# ---------------------------------------------------------------------------
# Report building — BASELINE: grows a string with += in a loop
# ---------------------------------------------------------------------------

def build_summary_report(records, ranked_customers, duplicate_ids):
    """Build a multi-section plain-text report string."""
    report = ""
    report += "=" * 60 + "\n"
    report += "SALES ANALYTICS REPORT\n"
    report += "=" * 60 + "\n\n"

    report += f"Total records processed: {len(records)}\n"
    report += f"Duplicate order IDs found: {len(duplicate_ids)}\n\n"

    report += "-" * 60 + "\n"
    report += "Revenue by customer (highest first)\n"
    report += "-" * 60 + "\n"
    for customer, revenue in ranked_customers:
        report += f"{customer:<20} ${revenue:>10.2f}\n"

    report += "\n" + "-" * 60 + "\n"
    report += "Per-order detail\n"
    report += "-" * 60 + "\n"
    for record in records:
        valid = validate_date_format(record["date"])
        report += (
            f"{record['order_id']}  {record['customer']:<14}  "
            f"{record['product']:<12}  ${record['amount']:>8.2f}  "
            f"{record['date']}  (valid_date={valid})\n"
        )

    return report


# ---------------------------------------------------------------------------
# Orchestration — this is the function profiled end-to-end
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
