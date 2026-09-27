"""
test_equivalence.py
---------------------
Verifies that sales_analytics_optimized.py produces exactly the same
results as sales_analytics_baseline.py (same stats, same report text,
same individual function outputs on shared inputs) — i.e. that every
optimization changed *how* the answer is computed, not *what* the
answer is. Also includes a handful of standalone correctness checks
against small, hand-verified inputs, independent of either module.

Run with:  python3 -m pytest test_equivalence.py -v
"""

import random

import pytest

import sales_analytics_baseline as base
import sales_analytics_optimized as opt


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def shared_records():
    return base.generate_sales_data(n=2000, seed=7)


@pytest.fixture(scope="module")
def shared_blocklist():
    rng = random.Random(8)
    return rng.sample(base.CUSTOMER_POOL, 50)


# ---------------------------------------------------------------------------
# End-to-end equivalence
# ---------------------------------------------------------------------------

class TestFullPipelineEquivalence:
    def test_stats_are_identical(self):
        _, stats_b = base.process_sales_data(n=2000, blocklist_size=50, seed=7)
        _, stats_o = opt.process_sales_data(n=2000, blocklist_size=50, seed=7)
        assert stats_b == stats_o

    def test_report_text_is_byte_identical(self):
        report_b, _ = base.process_sales_data(n=2000, blocklist_size=50, seed=7)
        report_o, _ = opt.process_sales_data(n=2000, blocklist_size=50, seed=7)
        assert report_b == report_o

    def test_identical_across_a_different_seed_and_size(self):
        """Re-check equivalence with different parameters, not just the
        defaults, to avoid the two modules simply agreeing by coincidence
        on one specific input."""
        report_b, stats_b = base.process_sales_data(n=800, blocklist_size=30, seed=99)
        report_o, stats_o = opt.process_sales_data(n=800, blocklist_size=30, seed=99)
        assert stats_b == stats_o
        assert report_b == report_o


# ---------------------------------------------------------------------------
# Per-function equivalence on shared input
# ---------------------------------------------------------------------------

class TestPerFunctionEquivalence:
    def test_find_duplicate_order_ids(self, shared_records):
        assert base.find_duplicate_order_ids(shared_records) == \
            opt.find_duplicate_order_ids(shared_records)

    def test_compute_revenue_by_customer(self, shared_records):
        rev_b = base.compute_revenue_by_customer(shared_records)
        rev_o = opt.compute_revenue_by_customer(shared_records)
        assert rev_b.keys() == rev_o.keys()  # same set AND same insertion order
        assert list(rev_b.keys()) == list(rev_o.keys())
        for customer in rev_b:
            assert rev_b[customer] == pytest.approx(rev_o[customer])

    def test_filter_blocked_records(self, shared_records, shared_blocklist):
        filtered_b = base.filter_blocked_records(shared_records, shared_blocklist)
        filtered_o = opt.filter_blocked_records(shared_records, shared_blocklist)
        assert filtered_b == filtered_o

    def test_rank_customers_by_revenue(self, shared_records):
        revenue = base.compute_revenue_by_customer(shared_records)
        ranked_b = base.rank_customers_by_revenue(revenue)
        ranked_o = opt.rank_customers_by_revenue(revenue)
        assert ranked_b == ranked_o

    def test_validate_date_format(self):
        for date_str in ["2026-01-15", "2026-13-40", "not-a-date", "", "2026-1-15"]:
            assert base.validate_date_format(date_str) == opt.validate_date_format(date_str)

    def test_build_summary_report(self, shared_records):
        duplicate_ids = opt.find_duplicate_order_ids(shared_records)
        revenue = opt.compute_revenue_by_customer(shared_records)
        ranked = opt.rank_customers_by_revenue(revenue)
        report_b = base.build_summary_report(shared_records, ranked, duplicate_ids)
        report_o = opt.build_summary_report(shared_records, ranked, duplicate_ids)
        assert report_b == report_o


# ---------------------------------------------------------------------------
# Standalone correctness checks (independent of either module agreeing
# with the other — hand-verified expected answers on small inputs)
# ---------------------------------------------------------------------------

class TestStandaloneCorrectness:
    def test_duplicate_detection_on_a_tiny_known_case(self):
        tiny = [
            {"order_id": "A"}, {"order_id": "B"},
            {"order_id": "A"}, {"order_id": "C"}, {"order_id": "A"},
        ]
        assert opt.find_duplicate_order_ids(tiny) == {"A"}

    def test_revenue_aggregation_on_a_tiny_known_case(self):
        tiny = [
            {"customer": "X", "amount": 10.0},
            {"customer": "Y", "amount": 5.0},
            {"customer": "X", "amount": 2.5},
        ]
        assert opt.compute_revenue_by_customer(tiny) == {"X": 12.5, "Y": 5.0}

    def test_ranking_orders_descending_by_revenue(self):
        result = opt.rank_customers_by_revenue({"A": 10, "B": 30, "C": 20})
        assert result == [("B", 30), ("C", 20), ("A", 10)]

    def test_ranking_ties_preserve_original_relative_order(self):
        result = opt.rank_customers_by_revenue({"A": 10, "B": 10, "C": 5})
        assert result == [("A", 10), ("B", 10), ("C", 5)]

    def test_blocklist_filtering_removes_only_blocked_customers(self):
        records = [{"customer": "X"}, {"customer": "Y"}, {"customer": "Z"}]
        result = opt.filter_blocked_records(records, blocklist=["Y"])
        assert result == [{"customer": "X"}, {"customer": "Z"}]

    def test_date_format_validation(self):
        assert opt.validate_date_format("2026-09-27") is True
        assert opt.validate_date_format("2026/09/27") is False
        assert opt.validate_date_format("27-09-2026") is False
