#!/usr/bin/env python3
"""Analyze mimalloc v3 vs jemalloc benchmark results and generate graphs."""

import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from collections import defaultdict
import os

def parse_benchres(path):
    """Parse benchres.csv into structured data."""
    data = defaultdict(lambda: defaultdict(lambda: {"time": [], "rss": []}))
    with open(path) as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 4:
                bench = parts[0]
                alloc = parts[1]
                time_str = parts[2]
                rss = int(parts[3])
                # Parse time (may have leading zeros like 04.50 or be like .206)
                time_val = float(time_str)
                data[bench][alloc]["time"].append(time_val)
                data[bench][alloc]["rss"].append(rss)
    return data

def main():
    csv_path = "out/bench/benchres.csv"
    data = parse_benchres(csv_path)

    benchmarks = sorted(data.keys())

    # Compute averages
    results = {}
    for bench in benchmarks:
        results[bench] = {}
        for alloc in ["mi3", "je"]:
            if alloc in data[bench]:
                times = data[bench][alloc]["time"]
                rsses = data[bench][alloc]["rss"]
                results[bench][alloc] = {
                    "time_mean": np.mean(times),
                    "time_std": np.std(times),
                    "rss_mean": np.mean(rsses),
                    "rss_std": np.std(rsses),
                    "time_all": times,
                    "rss_all": rsses,
                }

    # Print summary table
    print("=" * 90)
    print(f"{'Benchmark':<18} {'mi3 time(s)':>12} {'je time(s)':>12} {'Speedup':>9} {'mi3 RSS(KB)':>12} {'je RSS(KB)':>12} {'RSS ratio':>10}")
    print("=" * 90)

    for bench in benchmarks:
        if "mi3" in results[bench] and "je" in results[bench]:
            mi = results[bench]["mi3"]
            je = results[bench]["je"]
            speedup = je["time_mean"] / mi["time_mean"] if mi["time_mean"] > 0 else float('inf')
            rss_ratio = mi["rss_mean"] / je["rss_mean"] if je["rss_mean"] > 0 else float('inf')
            print(f"{bench:<18} {mi['time_mean']:>10.3f}s {je['time_mean']:>10.3f}s {speedup:>8.2f}x {mi['rss_mean']:>11.0f} {je['rss_mean']:>11.0f} {rss_ratio:>9.2f}x")
    print("=" * 90)

    # ---- GRAPH 1: Elapsed Time Comparison ----
    fig, ax = plt.subplots(figsize=(14, 7))

    benches_for_plot = [b for b in benchmarks if "mi3" in results[b] and "je" in results[b]]
    x = np.arange(len(benches_for_plot))
    width = 0.35

    mi3_times = [results[b]["mi3"]["time_mean"] for b in benches_for_plot]
    je_times = [results[b]["je"]["time_mean"] for b in benches_for_plot]
    mi3_errs = [results[b]["mi3"]["time_std"] for b in benches_for_plot]
    je_errs = [results[b]["je"]["time_std"] for b in benches_for_plot]

    bars1 = ax.bar(x - width/2, mi3_times, width, yerr=mi3_errs, label='mimalloc v3.2.8', color='#2196F3', capsize=3)
    bars2 = ax.bar(x + width/2, je_times, width, yerr=je_errs, label='jemalloc 5.3.0', color='#FF9800', capsize=3)

    ax.set_ylabel('Elapsed Time (seconds)', fontsize=12)
    ax.set_title('mimalloc v3.2.8 vs jemalloc 5.3.0 — Elapsed Time (lower is better)', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(benches_for_plot, rotation=45, ha='right', fontsize=10)
    ax.legend(fontsize=11)
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig('out/bench/time_comparison.png', dpi=150)
    plt.close()
    print("\nSaved: out/bench/time_comparison.png")

    # ---- GRAPH 2: RSS Memory Comparison ----
    fig, ax = plt.subplots(figsize=(14, 7))

    mi3_rss = [results[b]["mi3"]["rss_mean"] / 1024 for b in benches_for_plot]  # Convert to MB
    je_rss = [results[b]["je"]["rss_mean"] / 1024 for b in benches_for_plot]
    mi3_rss_errs = [results[b]["mi3"]["rss_std"] / 1024 for b in benches_for_plot]
    je_rss_errs = [results[b]["je"]["rss_std"] / 1024 for b in benches_for_plot]

    bars1 = ax.bar(x - width/2, mi3_rss, width, yerr=mi3_rss_errs, label='mimalloc v3.2.8', color='#2196F3', capsize=3)
    bars2 = ax.bar(x + width/2, je_rss, width, yerr=je_rss_errs, label='jemalloc 5.3.0', color='#FF9800', capsize=3)

    ax.set_ylabel('Peak RSS (MB)', fontsize=12)
    ax.set_title('mimalloc v3.2.8 vs jemalloc 5.3.0 — Peak RSS Memory (lower is better)', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(benches_for_plot, rotation=45, ha='right', fontsize=10)
    ax.legend(fontsize=11)
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig('out/bench/rss_comparison.png', dpi=150)
    plt.close()
    print("Saved: out/bench/rss_comparison.png")

    # ---- GRAPH 3: Normalized Speedup (mi3 relative to je) ----
    fig, ax = plt.subplots(figsize=(14, 6))

    speedups = [results[b]["je"]["time_mean"] / results[b]["mi3"]["time_mean"] for b in benches_for_plot]
    colors = ['#4CAF50' if s > 1.0 else '#F44336' for s in speedups]

    bars = ax.barh(benches_for_plot, speedups, color=colors, edgecolor='black', linewidth=0.5)
    ax.axvline(x=1.0, color='black', linestyle='--', linewidth=1.5, label='Equal performance')
    ax.set_xlabel('Speedup factor (>1 = mimalloc faster)', fontsize=12)
    ax.set_title('mimalloc v3.2.8 Speedup vs jemalloc 5.3.0 (higher is better for mimalloc)', fontsize=14, fontweight='bold')

    # Add value labels on bars
    for bar, val in zip(bars, speedups):
        ax.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height()/2, f'{val:.2f}x',
                va='center', fontsize=10)

    ax.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    plt.savefig('out/bench/speedup.png', dpi=150)
    plt.close()
    print("Saved: out/bench/speedup.png")

    # ---- GRAPH 4: RSS ratio (mi3 / je) ----
    fig, ax = plt.subplots(figsize=(14, 6))

    rss_ratios = [results[b]["mi3"]["rss_mean"] / results[b]["je"]["rss_mean"] for b in benches_for_plot]
    colors = ['#4CAF50' if r < 1.0 else '#FF9800' for r in rss_ratios]

    bars = ax.barh(benches_for_plot, rss_ratios, color=colors, edgecolor='black', linewidth=0.5)
    ax.axvline(x=1.0, color='black', linestyle='--', linewidth=1.5, label='Equal memory')
    ax.set_xlabel('RSS Ratio mi3/je (<1 = mimalloc uses less memory)', fontsize=12)
    ax.set_title('Memory Usage Ratio: mimalloc v3.2.8 / jemalloc 5.3.0 (lower is better for mimalloc)', fontsize=14, fontweight='bold')

    for bar, val in zip(bars, rss_ratios):
        ax.text(bar.get_width() + 0.02, bar.get_y() + bar.get_height()/2, f'{val:.2f}x',
                va='center', fontsize=10)

    ax.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    plt.savefig('out/bench/rss_ratio.png', dpi=150)
    plt.close()
    print("Saved: out/bench/rss_ratio.png")

if __name__ == "__main__":
    main()
