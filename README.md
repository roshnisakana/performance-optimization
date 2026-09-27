# performance-optimization
Profiled a Python data pipeline with cProfile, fixed 6 real bottlenecks (O(n²)→O(n), list→set, string concat→join), and verified byte-identical output with a 15-test equivalence suite — 108.9x speedup
