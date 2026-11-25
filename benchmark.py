"""
Benchmark system for AI Maze Solver algorithms.

Runs empirical performance evaluations of BFS, DFS, and A* on identical
procedurally generated mazes of increasing dimensions (15x15, 25x25, 50x50, 75x75).

Measures and compares:
- Average Execution Time (ms)
- Average Nodes Expanded
- Average Solution Path Length
"""

import sys
import os
import statistics

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from maze import Maze
from algorithms.bfs import bfs_solve
from algorithms.dfs import dfs_solve
from algorithms.astar import astar_solve


def run_benchmarks(sizes=None, trials_per_size=10):
    """
    Run empirical benchmarks across multiple maze dimensions.
    Uses identical maze instances for all three algorithms per trial.
    Calculates both Mean and Median metrics to provide robust statistical evaluation.
    """
    if sizes is None:
        sizes = [(15, 15), (25, 25), (50, 50), (75, 75)]
    
    algorithms = [
        ("BFS", bfs_solve),
        ("DFS", dfs_solve),
        ("A*", astar_solve),
    ]
    
    print("=" * 104)
    print("                      AI MAZE SOLVER: ALGORITHM BENCHMARK SUITE")
    print("=" * 104)
    print(f"Configurations: {len(sizes)} Grid Sizes | {trials_per_size} Solvable Trials Per Size")
    print("Testing Algorithms: Breadth-First Search (BFS), Depth-First Search (DFS), A* Search")
    print("Measurement Scope: Pure search compute time (time.perf_counter()) excluding UI/animation overhead.")
    print("=" * 104)
    print()

    summary_records = []

    for rows, cols in sizes:
        print(f"--> Running Benchmark for Grid Size: {rows}x{cols} ({trials_per_size} trials)...")
        
        # Store trial metrics: algo_name -> dict of lists
        metrics = {
            "BFS": {"time": [], "nodes": [], "path": []},
            "DFS": {"time": [], "nodes": [], "path": []},
            "A*":  {"time": [], "nodes": [], "path": []},
        }
        
        trial = 0
        seed = 1000
        while trial < trials_per_size:
            seed += 1
            test_maze = Maze(rows, cols)
            test_maze.generate_random_maze(seed=seed)
            if not test_maze.has_solution():
                continue
            
            # Run each algorithm on an identical clone of the maze
            for algo_name, solver in algorithms:
                clone = test_maze.clone()
                res = solver(clone)
                assert res['found'], f"Algorithm {algo_name} failed on solvable maze seed {seed}"
                
                path_len = len(res['path']) - 1 if len(res['path']) > 1 else 0
                metrics[algo_name]["time"].append(res["time_ms"])
                metrics[algo_name]["nodes"].append(res["nodes_expanded"])
                metrics[algo_name]["path"].append(path_len)
            
            trial += 1

        # Calculate mean and median for current size
        for algo_name in ["BFS", "DFS", "A*"]:
            summary_records.append({
                "size": f"{rows}x{cols}",
                "algo": algo_name,
                "mean_time": statistics.mean(metrics[algo_name]["time"]),
                "median_time": statistics.median(metrics[algo_name]["time"]),
                "mean_nodes": statistics.mean(metrics[algo_name]["nodes"]),
                "median_nodes": statistics.median(metrics[algo_name]["nodes"]),
                "mean_path": statistics.mean(metrics[algo_name]["path"]),
                "median_path": statistics.median(metrics[algo_name]["path"])
            })
        print(f"    Completed {trials_per_size} trials for {rows}x{cols}.\n")

    # Print Formatted Results Table with Mean and Median
    header = (f"{'Grid Size':<10} | {'Algorithm':<9} | "
              f"{'Mean Nodes':<11} | {'Med Nodes':<10} | "
              f"{'Mean Path':<10} | {'Med Path':<9} | "
              f"{'Mean Time (ms)':<15} | {'Med Time (ms)':<14}")
    divider = "-" * len(header)
    
    print("\n" + "=" * len(header))
    print("                                   EMPIRICAL RESULTS TABLE")
    print("=" * len(header))
    print(header)
    print(divider)
    
    prev_size = ""
    for rec in summary_records:
        if prev_size and prev_size != rec["size"]:
            print(divider)
        prev_size = rec["size"]
        print(f"{rec['size']:<10} | {rec['algo']:<9} | "
              f"{rec['mean_nodes']:<11.1f} | {rec['median_nodes']:<10.1f} | "
              f"{rec['mean_path']:<10.1f} | {rec['median_path']:<9.1f} | "
              f"{rec['mean_time']:<15.3f} | {rec['median_time']:<14.3f}")
    
    print("=" * len(header))
    print()
    print("KEY ACADEMIC OBSERVATIONS & EMPIRICAL ANALYSIS:")
    
    # 1. Optimality Equivalence Check
    by_size = {}
    for r in summary_records:
        by_size.setdefault(r["size"], {})[r["algo"]] = r

    all_optimal_match = True
    for sz, algos in by_size.items():
        if "BFS" in algos and "A*" in algos:
            if abs(algos["BFS"]["mean_path"] - algos["A*"]["mean_path"]) > 1e-6:
                all_optimal_match = False
                break

    print("1. Optimality Equivalence:")
    if all_optimal_match:
        print(f"   - Verified: BFS and A* produced identical optimal path lengths across all {len(by_size)} grid sizes.")
    else:
        print("   - Notice: Path length difference detected between BFS and A*.")

    # 2. Search Efficiency Comparison
    print("2. Search Efficiency & Node Expansions:")
    for sz, algos in by_size.items():
        if "BFS" in algos and "A*" in algos:
            bfs_n = algos["BFS"]["mean_nodes"]
            ast_n = algos["A*"]["mean_nodes"]
            diff = ((bfs_n - ast_n) / bfs_n) * 100 if bfs_n > 0 else 0
            print(f"   - Size {sz:<7}: A* expanded {ast_n:.1f} nodes vs BFS {bfs_n:.1f} nodes ({diff:+.1f}% change)")

    # 3. Execution Time & Overhead Analysis
    print("3. Search Execution Time vs Data Structure Overhead:")
    for sz, algos in by_size.items():
        if "BFS" in algos and "A*" in algos:
            bfs_t = algos["BFS"]["mean_time"]
            ast_t = algos["A*"]["mean_time"]
            print(f"   - Size {sz:<7}: BFS search time {bfs_t:.3f} ms | A* search time {ast_t:.3f} ms")
    print("   - Note: Fewer expanded nodes do not guarantee lower runtime because A* incurs O(log N)")
    print("     priority-queue heap operations and heuristic calculations per node.")
    print("=" * len(header))

    return summary_records


if __name__ == "__main__":
    run_benchmarks()
