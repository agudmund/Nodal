#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Cozy times nodal playground - resource_monitor.py resource tracking
# Monitor memory and CPU usage during app operations

import tracemalloc
import psutil
import os
from datetime import datetime


class ResourceMonitor:
    """Monitor and track resource usage (memory, CPU)."""

    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.start_memory = None
        self.start_time = None

    def start(self):
        """Start tracking resources."""
        tracemalloc.start()
        self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.start_time = datetime.now()

    def stop(self, operation_name: str = "Operation") -> dict:
        """Stop tracking and return resource usage."""
        current_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        memory_used = current_memory - self.start_memory
        cpu_percent = self.process.cpu_percent(interval=0.1)

        # Get tracemalloc snapshot
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        elapsed = datetime.now() - self.start_time

        results = {
            "operation": operation_name,
            "elapsed_time": elapsed.total_seconds(),
            "memory_used_mb": memory_used,
            "current_memory_mb": current_memory,
            "peak_memory_mb": peak / 1024 / 1024,
            "cpu_percent": cpu_percent,
        }

        return results

    @staticmethod
    def format_results(results: dict) -> str:
        """Format results for display."""
        return (
            f"\n{'='*60}\n"
            f"📊 Resource Usage: {results['operation']}\n"
            f"{'='*60}\n"
            f"⏱️  Time:           {results['elapsed_time']:.4f}s\n"
            f"💾 Memory Used:    {results['memory_used_mb']:.2f} MB\n"
            f"📈 Current Mem:    {results['current_memory_mb']:.2f} MB\n"
            f"🔝 Peak Memory:    {results['peak_memory_mb']:.2f} MB\n"
            f"⚙️  CPU Usage:      {results['cpu_percent']:.1f}%\n"
            f"{'='*60}\n"
        )


# Global monitor instance
monitor = ResourceMonitor()
