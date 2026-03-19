#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - resource_monitor.py resource tracking
-Monitor memory and CPU usage during app operations for enjoying
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

import tracemalloc
import psutil
import os
import time
from datetime import datetime
from utils.logger import setup_logger

logger = setup_logger()

class ResourceMonitor:
    """Monitor and track resource usage (memory, CPU)."""

    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.start_memory = None
        self.start_time = None

    def start(self):
        """Start tracking resources for a specific operation."""
        tracemalloc.start()
        # RSS is the 'Resident Set Size' - the actual RAM occupied
        self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.start_time = time.perf_counter()
        logger.debug("Resource tracking started.")

    def stop(self, operation_name: str = "Operation") -> dict:
        """Stop tracking and return the delta in resources."""
        if self.start_time is None:
            return {"error": "Monitor was never started"}

        current_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        memory_used = current_memory - self.start_memory
        
        # CPU percent since the last call (or start)
        cpu_percent = self.process.cpu_percent(interval=None)

        # Get peak memory via tracemalloc
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        elapsed = time.perf_counter() - self.start_time

        results = {
            "operation": operation_name,
            "elapsed_time": elapsed,
            "memory_used_mb": memory_used,
            "current_memory_mb": current_memory,
            "peak_memory_mb": peak / 1024 / 1024,
            "cpu_percent": cpu_percent,
        }
        
        logger.info(self.format_results(results))
        return results

    @staticmethod
    def format_results(results: dict) -> str:
        """Format results for a pretty console/log output."""
        return (
            f"\n{'═'*60}\n"
            f" 📊 RESOURCE REPORT: {results['operation']}\n"
            f"{'═'*60}\n"
            f" ⏱️  Time:           {results['elapsed_time']:.4f}s\n"
            f" 💾 Memory Delta:    {results['memory_used_mb']:.2f} MB\n"
            f" 📈 Peak Memory:    {results['peak_memory_mb']:.2f} MB\n"
            f" 🎛️  CPU Usage:      {results['cpu_percent']:.1f}%\n"
            f"{'═'*60}"
        )

# Global monitor instance
monitor = ResourceMonitor()
