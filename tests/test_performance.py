#!/usr/bin/env python3
"""Test performance with and without parallelization."""

import subprocess
import time

def run_test_suite(workers=None):
    """Run pytest and measure time."""
    if workers:
        cmd = f"python -m pytest tests/test_validation_integration.py tests/test_stress_scenarios.py -n {workers} -v --tb=short"
    else:
        cmd = "python -m pytest tests/test_validation_integration.py tests/test_stress_scenarios.py -v --tb=short"
    
    print(f"\nRunning: {cmd}")
    start = time.time()
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    elapsed = time.time() - start
    
    # Extract test count from output
    output = result.stdout + result.stderr
    print(f"Time: {elapsed:.1f}s")
    print(f"Output (last 500 chars):\n{output[-500:]}")
    
    return elapsed

if __name__ == "__main__":
    print("=" * 70)
    print("TEST PERFORMANCE COMPARISON")
    print("=" * 70)
    
    # Sequential run
    print("\n1. SEQUENTIAL (no parallelization)")
    sequential_time = run_test_suite(workers=None)
    
    # Parallel run with 4 workers
    print("\n2. PARALLEL (4 workers)")
    parallel_time = run_test_suite(workers=4)
    
    # Calculate speedup
    speedup = sequential_time / parallel_time if parallel_time > 0 else 0
    improvement = ((sequential_time - parallel_time) / sequential_time) * 100 if sequential_time > 0 else 0
    
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Sequential time: {sequential_time:.1f}s")
    print(f"Parallel time:   {parallel_time:.1f}s")
    print(f"Speedup:         {speedup:.1f}x")
    print(f"Improvement:     {improvement:.0f}%")
