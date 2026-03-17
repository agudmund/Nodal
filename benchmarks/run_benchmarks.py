# In benchmarks/run_benchmarks.py

import sys
import time
from pathlib import Path

# Fix the path so we can see the root modules
root_dir = Path(__file__).parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from benchmarks.profiler import time_function, benchmark_suite
from graphics.Scene import NodeScene
from utils.logger import setup_logger

from PySide6.QtWidgets import QApplication

# Initialize a silent logger for benchmarks to keep the console clean
logger = setup_logger()

@time_function
def benchmark_zoom_performance(scene, view, zoom_level):
    """
    PURPOSE: Measure render time at extreme zoom levels.
    ACCOUNTABILITY: Higher time = GPU bottleneck.
    """
    view.current_zoom = zoom_level
    view.resetTransform()
    view.scale(zoom_level, zoom_level)
    
    start = time.perf_counter()
    view.viewport().repaint() # Force an immediate hardware frame
    return time.perf_counter() - start

@time_function
def benchmark_complex_graph(count: int = 50):
    """Stress test: Creating nodes AND rubbery connections."""
    scene = NodeScene()
    nodes = []
    
    # 1. Node Creation
    for i in range(count):
        node = scene.add_node(i * 10, i * 10, f"Node {i}")
        nodes.append(node)
    
    # 2. Nerve Connection (The real heavy lifting)
    for i in range(len(nodes) - 1):
        scene.add_connection(nodes[i], nodes[i+1])
    
    return scene

def run_all_benchmarks():
    # START HERE: Create a dummy app so Qt doesn't panic
    app = QApplication.instance() or QApplication(sys.argv)
    
    print("\n" + "═"*60)
    print(" 🔍 NODAL ENGINE: STRESS TEST ")
    print("═"*60)

    try:
        print(f"🚀 Initializing Scene...")
        start = time.perf_counter()
        scene = NodeScene()
        print(f" ✅ Scene Ready ({time.perf_counter() - start:.4f}s)")

        print(f"\n🚀 Running Complex Graph Test (100 Nodes + 99 Rubbery Wires)...")
        with benchmark_suite("Heavy Nerve Stress Test", iterations=1):
            benchmark_complex_graph(100)

        # print(f"🚀 Testing 0.1x Zoom Performance...")
        # time_taken = benchmark_zoom_performance(scene, window.view, 0.1)
        # print(f" ✅ 0.1x Render: {time_taken:.4f}s")
            
    except Exception as e:
        print(f"\n❌ BENCHMARK CRASHED: {str(e)}")
        import traceback
        traceback.print_exc()

    print("\n" + "═"*60)
    print(" ✨ STRESS TEST COMPLETE ")
    print("═"*60 + "\n")

if __name__ == "__main__":
    run_all_benchmarks()