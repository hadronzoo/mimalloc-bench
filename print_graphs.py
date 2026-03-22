#!/usr/bin/env python3
"""Print text-based bar charts for mimalloc v3 vs jemalloc benchmark results."""

from collections import defaultdict
import numpy as np

def parse_benchres(path):
    data = defaultdict(lambda: defaultdict(lambda: {"time": [], "rss": []}))
    with open(path) as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 4:
                bench, alloc, time_str, rss = parts[0], parts[1], parts[2], int(parts[3])
                data[bench][alloc]["time"].append(float(time_str))
                data[bench][alloc]["rss"].append(rss)
    return data

def bar(value, max_val, width=40, char="█"):
    n = int(round(value / max_val * width)) if max_val > 0 else 0
    return char * n

def main():
    data = parse_benchres("out/bench/benchres.csv")
    benchmarks = sorted(data.keys())

    results = {}
    for bench in benchmarks:
        results[bench] = {}
        for alloc in ["mi3", "je"]:
            if alloc in data[bench]:
                results[bench][alloc] = {
                    "time": np.mean(data[bench][alloc]["time"]),
                    "rss": np.mean(data[bench][alloc]["rss"]),
                }

    benches = [b for b in benchmarks if "mi3" in results[b] and "je" in results[b]]

    # ===== GRAPH 1: SPEEDUP =====
    print()
    print("╔══════════════════════════════════════════════════════════════════════════╗")
    print("║     SPEEDUP: mimalloc v3.2.8 vs jemalloc 5.3.0 (higher = mi3 faster)   ║")
    print("╚══════════════════════════════════════════════════════════════════════════╝")
    print()

    speedups = [(b, results[b]["je"]["time"] / results[b]["mi3"]["time"]) for b in benches]
    speedups.sort(key=lambda x: x[1], reverse=True)
    max_speedup = max(s for _, s in speedups)

    for bench, spd in speedups:
        label = f"{bench:<16}"
        if spd >= 1.0:
            b = bar(spd, max_speedup, width=45, char="▓")
            marker = f" {spd:.2f}x ◀ mi3 faster"
        else:
            b = bar(spd, max_speedup, width=45, char="░")
            marker = f" {spd:.2f}x ◀ je faster"
        print(f"  {label} {b}{marker}")

    print(f"\n  {'1.0x line':>16}  {'|':>5}")
    print()

    # ===== GRAPH 2: ELAPSED TIME =====
    print("╔══════════════════════════════════════════════════════════════════════════╗")
    print("║     ELAPSED TIME (seconds) — lower is better                            ║")
    print("╚══════════════════════════════════════════════════════════════════════════╝")
    print()

    max_time = max(max(results[b]["mi3"]["time"], results[b]["je"]["time"]) for b in benches)

    for bench in benches:
        mi_t = results[bench]["mi3"]["time"]
        je_t = results[bench]["je"]["time"]
        mi_bar = bar(mi_t, max_time, width=40, char="█")
        je_bar = bar(je_t, max_time, width=40, char="▒")
        print(f"  {bench:<16} mi3 {mi_bar} {mi_t:.3f}s")
        print(f"  {'':16} je  {je_bar} {je_t:.3f}s")
        print()

    print("  Legend: █ = mimalloc v3   ▒ = jemalloc")
    print()

    # ===== GRAPH 3: PEAK RSS MEMORY =====
    print("╔══════════════════════════════════════════════════════════════════════════╗")
    print("║     PEAK RSS MEMORY (MB) — lower is better                              ║")
    print("╚══════════════════════════════════════════════════════════════════════════╝")
    print()

    max_rss = max(max(results[b]["mi3"]["rss"], results[b]["je"]["rss"]) for b in benches) / 1024

    for bench in benches:
        mi_r = results[bench]["mi3"]["rss"] / 1024
        je_r = results[bench]["je"]["rss"] / 1024
        mi_bar = bar(mi_r, max_rss, width=40, char="█")
        je_bar = bar(je_r, max_rss, width=40, char="▒")
        print(f"  {bench:<16} mi3 {mi_bar} {mi_r:.1f} MB")
        print(f"  {'':16} je  {je_bar} {je_r:.1f} MB")
        print()

    print("  Legend: █ = mimalloc v3   ▒ = jemalloc")
    print()

    # ===== GRAPH 4: RSS RATIO =====
    print("╔══════════════════════════════════════════════════════════════════════════╗")
    print("║     MEMORY RATIO mi3/je (<1 = mi3 uses less, >1 = mi3 uses more)        ║")
    print("╚══════════════════════════════════════════════════════════════════════════╝")
    print()

    ratios = [(b, results[b]["mi3"]["rss"] / results[b]["je"]["rss"]) for b in benches]
    ratios.sort(key=lambda x: x[1])
    max_ratio = max(r for _, r in ratios)

    for bench, ratio in ratios:
        label = f"{bench:<16}"
        if ratio <= 1.0:
            b = bar(ratio, max_ratio, width=40, char="▓")
            note = "◀ mi3 uses LESS"
        else:
            b = bar(ratio, max_ratio, width=40, char="░")
            note = "◀ mi3 uses MORE"
        print(f"  {label} {b} {ratio:.2f}x {note}")

    print()
    print("  1.0x = equal memory usage")
    print()

if __name__ == "__main__":
    main()
