#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Cozy times nodal playground - run_benchmarks.py benchmark suite runner
# Run this script to profile app performance

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmarks.profiler import time_function, benchmark_suite, profile_function
from graphics.scene import NodeScene
from graphics.node import Node
from utils.logger import setup_logger

logger = setup_logger()


@time_function
def benchmark_scene_creation():
    """Benchmark creating a new scene."""
    scene = NodeScene()
    return scene


@time_function
def benchmark_node_creation(count: int = 100):
    """Benchmark creating N nodes."""
    scene = NodeScene()
    for i in range(count):
        scene.add_node(i * 150, i * 100, f"Node {i}")
    return scene


@time_function
def benchmark_node_selection(count: int = 50):
    """Benchmark selecting/deselecting nodes."""
    scene = NodeScene()
    nodes = [scene.add_node(i * 150, i * 100, f"Node {i}") for i in range(count)]

    # Toggle selection
    for node in nodes:
        node.setSelected(True)
        node.setSelected(False)

    return nodes


def run_all_benchmarks():
    """Run the complete benchmark suite."""
    print("\n" + "="*60)
    print("🔍 NODAL APP BENCHMARKS")
    print("="*60 + "\n")

    logger.info("Starting benchmark suite")

    # Scene creation
    print("📈 Scene Creation:")
    benchmark_scene_creation()

    # Node creation (varying counts)
    print("\n📈 Node Creation:")
    with benchmark_suite("Creating 50 nodes", iterations=1):
        benchmark_node_creation(50)

    with benchmark_suite("Creating 100 nodes", iterations=1):
        benchmark_node_creation(100)

    with benchmark_suite("Creating 500 nodes", iterations=1):
        benchmark_node_creation(500)

    # Node selection
    print("\n📈 Node Selection (50 nodes):")
    benchmark_node_selection(50)

    print("\n" + "="*60)
    print("✅ Benchmark suite complete!")
    print("="*60 + "\n")

    logger.info("Benchmark suite completed")


if __name__ == "__main__":
    run_all_benchmarks()
