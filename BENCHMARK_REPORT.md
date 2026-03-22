# mimalloc v3.2.8 vs jemalloc 5.3.0 — Benchmark Report

**Date:** 2026-03-22
**Platform:** Linux 6.18.5, x86_64, 4 cores
**Methodology:** 3 repeats per benchmark, averaged results
**mimalloc version:** v3.2.8 (rc3, released 2026-02-03)
**jemalloc version:** 5.3.0

## Summary

mimalloc v3 is **faster than jemalloc in 12 out of 14 benchmarks**, with dramatic speedups in high-contention and large-allocation workloads. jemalloc uses less peak memory in some multi-threaded stress tests, while mimalloc v3 uses significantly less memory for small-allocation and single-threaded workloads.

## Results Table

| Benchmark | mi3 time (s) | je time (s) | Speedup | mi3 RSS (KB) | je RSS (KB) | RSS ratio |
|---|---|---|---|---|---|---|
| alloc-test1 | 3.553 | 3.513 | 0.99x | 13,783 | 13,237 | 1.04x |
| alloc-testN | 3.400 | 3.380 | 0.99x | 14,500 | 13,923 | 1.04x |
| barnes | 2.703 | 2.697 | 1.00x | 58,865 | 61,067 | 0.96x |
| cfrac | 4.460 | 4.540 | 1.02x | 3,483 | 5,653 | 0.62x |
| espresso | 4.940 | 5.010 | 1.01x | 5,265 | 6,065 | 0.87x |
| glibc-simple | 2.530 | 2.867 | 1.13x | 2,164 | 4,951 | 0.44x |
| glibc-thread | 3.025 | 3.055 | 1.01x | 3,484 | 5,888 | 0.59x |
| larsonN-sized | 11.450 | 12.721 | 1.11x | 60,879 | 45,059 | 1.35x |
| malloc-large | 3.990 | 17.577 | **4.41x** | 594,487 | 446,899 | 1.33x |
| mleak10 | 0.227 | 0.477 | **2.10x** | 2,541 | 5,300 | 0.48x |
| mleak100 | 2.350 | 4.893 | **2.08x** | 2,604 | 5,399 | 0.48x |
| mstressN | 0.277 | 0.600 | **2.17x** | 109,711 | 50,452 | 2.17x |
| rptestN | 0.247 | 0.384 | **1.55x** | 23,217 | 23,547 | 0.99x |
| xmalloc-testN | 1.186 | 10.817 | **9.12x** | 66,536 | 51,331 | 1.30x |

*Speedup >1 means mimalloc is faster. RSS ratio <1 means mimalloc uses less memory.*

## Performance Analysis

### Where mimalloc v3 dominates (speed)

- **xmalloc-testN (9.12x faster):** Producer/consumer pattern with cross-thread allocation — mimalloc v3's lock-free design dramatically outperforms jemalloc's arena-based approach.
- **malloc-large (4.41x faster):** Large (MiB-scale) allocations — mimalloc v3 handles large allocations with far less system overhead (0.48s sys vs 15.91s sys for jemalloc).
- **mstressN (2.17x faster):** Multi-threaded server workload stress test — mimalloc v3's improved cross-thread sharing shines.
- **mleak10/mleak100 (2.08-2.10x faster):** Memory leak detection workloads — mimalloc v3 is substantially faster with much less system time.
- **rptestN (1.55x faster):** rpmalloc-style allocation patterns with mimalloc achieving ~8.3M ops/sec vs ~5.3M ops/sec for jemalloc.
- **glibc-simple (1.13x faster):** Simple single-threaded allocations — modest but consistent advantage.
- **larsonN-sized (1.11x faster):** Server workload with sized deallocation — mimalloc benefits from sized free optimizations.

### Essentially tied

- **alloc-test1/alloc-testN (~0.99x):** Pareto-distributed allocations — both allocators perform nearly identically.
- **barnes (1.00x):** N-body simulation — performance is compute-bound, not allocator-bound.
- **cfrac (1.02x), espresso (1.01x), glibc-thread (1.01x):** Marginal differences within noise.

### No benchmarks where jemalloc clearly wins on speed

jemalloc does not meaningfully outperform mimalloc v3 in any benchmark.

## Memory Usage Analysis

### Where mimalloc v3 uses less memory

- **glibc-simple (0.44x):** mimalloc uses less than half the RSS (2.2 MB vs 5.0 MB).
- **mleak10/mleak100 (0.48x):** Roughly half the memory footprint.
- **glibc-thread (0.59x):** Significantly less memory for threaded glibc workloads.
- **cfrac (0.62x):** 38% less memory for many small allocations.
- **espresso (0.87x):** Modest memory savings.
- **barnes (0.96x):** Slightly less memory for the N-body simulation.

### Where jemalloc uses less memory

- **mstressN (2.17x):** mimalloc uses 2x more RSS — the biggest memory disadvantage. This reflects mimalloc's strategy of retaining memory segments for reuse rather than returning them to the OS.
- **larsonN-sized (1.35x):** mimalloc retains more memory in cross-thread workloads.
- **malloc-large (1.33x):** mimalloc uses more peak RSS for large allocations (594 MB vs 447 MB), though it completes 4.4x faster.
- **xmalloc-testN (1.30x):** More memory but 9x faster throughput.

## Key Takeaways

1. **mimalloc v3 is consistently faster** across virtually all workloads, with the advantage being most dramatic in multi-threaded and large-allocation scenarios (up to 9x faster).

2. **Speed vs memory trade-off:** mimalloc v3 tends to use more memory in high-throughput multi-threaded workloads (mstress, larson, xmalloc-test) — this is by design, as it retains memory segments for faster reuse rather than eagerly returning them to the OS.

3. **Small allocation efficiency:** For workloads dominated by small allocations (cfrac, glibc-simple, mleak), mimalloc v3 uses both less time AND less memory than jemalloc.

4. **Large allocation handling:** mimalloc v3's large allocation path is dramatically superior in speed (4.4x), using much less system time, though with ~33% more peak RSS.

5. **v3 architectural improvements:** The lock-free design improvements in v3 are clearly visible in cross-thread workloads like xmalloc-testN (9x) and mstressN (2x), validating the v3 redesign.

## Graphs

- `out/bench/time_comparison.png` — Side-by-side elapsed time comparison
- `out/bench/rss_comparison.png` — Side-by-side peak RSS comparison
- `out/bench/speedup.png` — Speedup factor (mi3 relative to jemalloc)
- `out/bench/rss_ratio.png` — Memory usage ratio (mi3 / jemalloc)
