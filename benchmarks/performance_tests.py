#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - performance_tests.py performance testing utilities
-Performance stress tests for node creation and connection operations
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

from utils.resource_monitor import ResourceMonitor


def test_performance_burst(scene, view):
    """
    Creates 50 nodes and 49 wires with guaranteed connections.
    Useful for performance profiling and stress testing.

    Args:
        scene: The NodeScene instance to add nodes to
        view: The NodeGraphicsView instance for centering
    """
    created_nodes = []

    monitor = ResourceMonitor()
    monitor.start()

    # Spawn nodes in a nice diagonal cascade
    for i in range(50):
        x_pos = 100 + (i * 40)
        y_pos = 100 + (i * 20)

        new_node = scene.add_node(x_pos, y_pos, f"Stress Node {i}")

        # If we have a previous node, connect them
        if created_nodes:
            prev_node = created_nodes[-1]
            scene.add_connection(prev_node, new_node)

        created_nodes.append(new_node)

    monitor.stop("50 Node Burst with Wires")

    # Center view on the middle of the cluster
    if created_nodes:
        view.centerOn(created_nodes[25])
