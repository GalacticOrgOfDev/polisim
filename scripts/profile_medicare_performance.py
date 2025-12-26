#!/usr/bin/env python3
"""
Performance Profiling Script for Medicare Monte Carlo

Profiles the Medicare model to identify bottlenecks and optimization opportunities.
"""

import sys
import time
import cProfile
import pstats
import io
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.medicare_medicaid import MedicareModel


def profile_medicare_projection():
    """Profile Medicare projection performance."""
    
    print("=" * 80)
    print("  Medicare Monte Carlo Performance Profiling")
    print("=" * 80)
    print()
    
    # Test configurations
    test_cases = [
        (10, 1000, "Quick test"),
        (10, 5000, "Medium test"),
        (10, 10000, "Full test"),
    ]
    
    for years, iterations, description in test_cases:
        print(f"Test: {description} ({years} years, {iterations:,} iterations)")
        print("-" * 60)
        
        model = MedicareModel(seed=42)
        
        # Time the projection
        start_time = time.time()
        df = model.project_all_parts(years=years, iterations=iterations)
        elapsed = time.time() - start_time
        
        # Calculate statistics
        records = len(df)
        iterations_per_sec = iterations / elapsed
        records_per_sec = records / elapsed
        
        print(f"  Time:       {elapsed:.2f} seconds")
        print(f"  Records:    {records:,}")
        print(f"  Iter/sec:   {iterations_per_sec:.0f}")
        print(f"  Rec/sec:    {records_per_sec:.0f}")
        print()
    
    # Detailed profiling with cProfile
    print("=" * 80)
    print("  Detailed Profiling (10 years, 10,000 iterations)")
    print("=" * 80)
    print()
    
    profiler = cProfile.Profile()
    model = MedicareModel(seed=42)
    
    profiler.enable()
    df = model.project_all_parts(years=10, iterations=10000)
    profiler.disable()
    
    # Print top functions by cumulative time
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats(20)  # Top 20 functions
    
    print(s.getvalue())
    
    print("=" * 80)
    print("  Bottleneck Analysis")
    print("=" * 80)
    print()
    
    # Analyze the profiling data
    ps = pstats.Stats(profiler)
    stats = ps.stats
    
    # Find the most time-consuming functions
    sorted_stats = sorted(stats.items(), key=lambda x: x[1][3], reverse=True)
    
    print("Top 10 Time-Consuming Operations:")
    print()
    for i, (func, (cc, nc, tt, ct, callers)) in enumerate(sorted_stats[:10], 1):
        filename, line, funcname = func
        if 'medicare' in filename or 'numpy' in filename:
            print(f"{i}. {funcname}")
            print(f"   File: {Path(filename).name}:{line}")
            print(f"   Cumulative Time: {ct:.3f}s")
            print(f"   Calls: {nc}")
            print()


if __name__ == "__main__":
    profile_medicare_projection()
