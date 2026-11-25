"""
Main entry point for the AI Maze Solver application.

Usage:
    python main.py                  # Run the interactive Pygame UI (default 25x25)
    python main.py --rows 31 --cols 31
    python main.py --maze mazes/sample1.txt
    python main.py --benchmark      # Run the benchmark suite directly
"""

import sys
import os
import argparse

from maze import Maze


def main():
    parser = argparse.ArgumentParser(description="AI Maze Solver - BFS | DFS | A* Visualization")
    parser.add_argument("--rows", type=int, default=25, help="Number of grid rows (default: 25)")
    parser.add_argument("--cols", type=int, default=25, help="Number of grid columns (default: 25)")
    parser.add_argument("--maze", type=str, default=None, help="Path to initial maze text file")
    parser.add_argument("--benchmark", action="store_true", help="Run algorithm benchmarks without launching UI")
    
    args = parser.parse_args()

    # If benchmark flag is provided, run benchmark and exit
    if args.benchmark:
        from benchmark import run_benchmarks
        run_benchmarks()
        return

    # Initialize Maze
    maze = Maze(args.rows, args.cols)
    if args.maze:
        if not os.path.exists(args.maze):
            print(f"Error: Maze file '{args.maze}' not found.", file=sys.stderr)
            sys.exit(1)
        try:
            print(f"Loading maze from: {args.maze}")
            maze.load_from_file(args.maze)
        except (ValueError, FileNotFoundError, OSError) as e:
            print(f"Error: Failed to load maze from '{args.maze}': {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Generate initial solvable maze
        maze.generate_random_maze()

    # Launch Pygame User Interface
    try:
        import pygame
        from ui import MazeUI
        ui = MazeUI(maze)
        ui.run()
    except pygame.error as e:
        print(f"\n[Error] Could not initialize graphical window: {e}", file=sys.stderr)
        print("This typically happens in headless environments without a display server.")
        print("The algorithms, benchmark suite, and automated test suite function independently:")
        print("  - Run automated tests:  python -m pytest -v")
        print("  - Run benchmarks:       python benchmark.py")
        sys.exit(1)


if __name__ == "__main__":
    main()
