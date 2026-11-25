"""
Search algorithms package for AI Maze Solver.
Contains implementations of BFS, DFS, and A* search algorithms.
"""

from .bfs import bfs_solve, bfs_generator
from .dfs import dfs_solve, dfs_generator
from .astar import astar_solve, astar_generator

__all__ = [
    "bfs_solve",
    "bfs_generator",
    "dfs_solve",
    "dfs_generator",
    "astar_solve",
    "astar_generator",
]
