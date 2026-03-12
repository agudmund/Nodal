#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Cozy times nodal playground - profiler.py profiling utilities
# Simple wrappers around cProfile for easy benchmark tracking

import cProfile
import pstats
import io
import time
import functools
from datetime import datetime
from pathlib import Path


class BenchmarkResult:
    """Stores and displays benchmark results."""

    def __init__(self, name: str, elapsed_time: float):
        self.name = name
        self.elapsed_time = elapsed_time
        self.timestamp = datetime.now()

    def __repr__(self) -> str:
        return f"{self.name}: {self.elapsed_time:.4f}s"


def time_function(func):
    """Decorator to time a function's execution."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"⏱️  {func.__name__} took {elapsed:.4f}s")
        return result
    return wrapper


def profile_function(func):
    """Decorator to profile a function using cProfile."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()

        result = func(*args, **kwargs)

        profiler.disable()

        # Print results
        print(f"\n{'='*60}")
        print(f"Profile: {func.__name__}")
        print(f"{'='*60}")

        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
        ps.print_stats(10)  # Top 10 functions
        print(s.getvalue())

        return result
    return wrapper


def benchmark_suite(name: str, iterations: int = 1):
    """Context manager for benchmarking a code block."""
    class BenchmarkContext:
        def __enter__(self):
            self.start_time = time.perf_counter()
            return self

        def __exit__(self, *args):
            elapsed = time.perf_counter() - self.start_time
            avg_time = elapsed / iterations
            print(f"📊 {name}")
            print(f"   Total: {elapsed:.4f}s | Average: {avg_time:.6f}s ({iterations} iterations)")

    return BenchmarkContext()


def save_benchmark_result(result: BenchmarkResult, results_file: str = "benchmark_results.txt"):
    """Save benchmark result to file for tracking over time."""
    results_path = Path(__file__).parent.parent / results_file

    with open(results_path, "a", encoding="utf-8") as f:
        f.write(f"{result.timestamp.isoformat()} | {result}\n")

    print(f"✅ Result saved to {results_file}")
