"""
Phase 3.4: Comprehensive Edge Cases Testing Suite
Covers:
1. Algorithm edge cases:
   - Start == Goal
   - Start adjacent to Goal
   - One-cell-wide corridor
   - Goal completely enclosed by walls
   - Start completely enclosed by walls
   - 2x2, 5x5, non-square, even dimensions, odd dimensions, 100x100
2. File loading edge cases:
   - Empty file, ragged rows, invalid chars, 0/2 Starts, 0/2 Goals, missing file, valid file, minimum 2x2.
3. Large maze 100x100 performance:
   - Generation and solve measurements across BFS, DFS, and A*.
"""

import os
import tempfile
import time
import pytest

from maze import Maze
from algorithms.bfs import bfs_solve
from algorithms.dfs import dfs_solve
from algorithms.astar import astar_solve


def test_edge_case_start_equals_goal():
    """Start equals goal: returns path [start], 0 path steps, nodes_expanded <= 1, found=True."""
    m = Maze(10, 10)
    m.start = (4, 4)
    m.goal = (4, 4)
    
    for name, solver in [("BFS", bfs_solve), ("DFS", dfs_solve), ("A*", astar_solve)]:
        res = solver(m.clone())
        assert res['found'] is True, f"{name}: expected found=True when start==goal"
        assert res['path'] == [(4, 4)], f"{name}: path must be [start]"
        assert res['nodes_expanded'] in (0, 1)


def test_edge_case_start_adjacent_to_goal():
    """Start directly adjacent to goal: optimal path length is exactly 1 step."""
    m = Maze(10, 10)
    m.start = (2, 2)
    m.goal = (2, 3)
    
    res_b = bfs_solve(m.clone())
    res_a = astar_solve(m.clone())
    res_d = dfs_solve(m.clone())
    
    assert res_b['found'] is True and len(res_b['path']) - 1 == 1
    assert res_a['found'] is True and len(res_a['path']) - 1 == 1
    assert res_d['found'] is True and len(res_d['path']) - 1 >= 1


def test_edge_case_one_cell_wide_corridor():
    """One-cell-wide forced corridor: all algorithms follow the exact same path."""
    m = Maze(5, 5)
    # Fill entire grid with walls except a single snake path
    for r in range(5):
        for c in range(5):
            m.grid[r][c] = '#'
    
    path_coords = [(1, 1), (1, 2), (1, 3), (2, 3), (3, 3), (3, 2), (3, 1)]
    for r, c in path_coords:
        m.grid[r][c] = '.'
        
    m.start = (1, 1)
    m.goal = (3, 1)
    
    res_b = bfs_solve(m.clone())
    res_a = astar_solve(m.clone())
    res_d = dfs_solve(m.clone())
    
    assert res_b['found'] is True and res_b['path'] == path_coords
    assert res_a['found'] is True and res_a['path'] == path_coords
    assert res_d['found'] is True and res_d['path'] == path_coords


def test_edge_case_start_enclosed_by_walls():
    """Start completely surrounded by walls: search terminates with found=False."""
    m = Maze(7, 7)
    m.start = (2, 2)
    m.goal = (5, 5)
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        m.set_wall(2 + dr, 2 + dc, True)
        
    for name, solver in [("BFS", bfs_solve), ("DFS", dfs_solve), ("A*", astar_solve)]:
        res = solver(m.clone())
        assert res['found'] is False
        assert res['path'] == [] or res['path'] is None


def test_edge_case_goal_enclosed_by_walls():
    """Goal completely surrounded by walls: search exhausts with found=False."""
    m = Maze(7, 7)
    m.start = (1, 1)
    m.goal = (4, 4)
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        m.set_wall(4 + dr, 4 + dc, True)
        
    for name, solver in [("BFS", bfs_solve), ("DFS", dfs_solve), ("A*", astar_solve)]:
        res = solver(m.clone())
        assert res['found'] is False
        assert res['path'] == [] or res['path'] is None


def test_edge_case_2x2_maze():
    """Minimum supported dimension 2x2."""
    m = Maze(2, 2)
    assert m.start != m.goal
    res = bfs_solve(m)
    assert res['found'] is True
    assert len(res['path']) == 3


def test_edge_case_5x5_maze():
    """Standard small 5x5 maze."""
    m = Maze(5, 5)
    m.generate_random_maze(seed=99)
    assert m.has_solution() is True
    res_b = bfs_solve(m)
    res_a = astar_solve(m)
    assert res_b['found'] is True and res_a['found'] is True
    assert len(res_b['path']) == len(res_a['path'])


def test_edge_case_non_square_and_even_dimensions():
    """Non-square even dimensions (e.g. 6x14)."""
    m = Maze(6, 14)
    m.generate_random_maze(seed=123)
    assert m.has_solution() is True
    res_b = bfs_solve(m)
    res_a = astar_solve(m)
    assert res_b['found'] is True
    assert len(res_b['path']) == len(res_a['path'])


# --- FILE LOADING EDGE CASES ---

def test_file_loading_empty_file():
    m = Maze()
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as tf:
        tf.write("")
        path = tf.name
    try:
        with pytest.raises(ValueError, match="empty"):
            m.load_from_file(path)
    finally:
        os.remove(path)


def test_file_loading_ragged_rows():
    m = Maze()
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as tf:
        tf.write("S..\n....\n..G\n")
        path = tf.name
    try:
        with pytest.raises(ValueError, match="equal length"):
            m.load_from_file(path)
    finally:
        os.remove(path)


def test_file_loading_invalid_characters():
    m = Maze()
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as tf:
        tf.write("S..#\n..X.\n...G\n")
        path = tf.name
    try:
        with pytest.raises(ValueError, match="Invalid character"):
            m.load_from_file(path)
    finally:
        os.remove(path)


def test_file_loading_zero_start_markers():
    m = Maze()
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as tf:
        tf.write("...#\n....\n...G\n")
        path = tf.name
    try:
        with pytest.raises(ValueError, match="exactly one Start"):
            m.load_from_file(path)
    finally:
        os.remove(path)


def test_file_loading_two_start_markers():
    m = Maze()
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as tf:
        tf.write("S..#\n.S..\n...G\n")
        path = tf.name
    try:
        with pytest.raises(ValueError, match="exactly one Start"):
            m.load_from_file(path)
    finally:
        os.remove(path)


def test_file_loading_zero_goal_markers():
    m = Maze()
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as tf:
        tf.write("S..#\n....\n....\n")
        path = tf.name
    try:
        with pytest.raises(ValueError, match="exactly one Goal"):
            m.load_from_file(path)
    finally:
        os.remove(path)


def test_file_loading_two_goal_markers():
    m = Maze()
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as tf:
        tf.write("S..#\n..G.\n...G\n")
        path = tf.name
    try:
        with pytest.raises(ValueError, match="exactly one Goal"):
            m.load_from_file(path)
    finally:
        os.remove(path)


def test_file_loading_missing_file():
    m = Maze()
    with pytest.raises(ValueError, match="Could not read file"):
        m.load_from_file("definitely_nonexistent_maze_file.txt")


def test_file_loading_minimum_supported_dimensions():
    m = Maze()
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as tf:
        tf.write("S.\n.G\n")
        path = tf.name
    try:
        m.load_from_file(path)
        assert m.rows == 2 and m.cols == 2
        assert m.start == (0, 0)
        assert m.goal == (1, 1)
    finally:
        os.remove(path)


# --- 100x100 LARGE MAZE BENCHMARK ---

def test_large_maze_100x100_performance():
    """Generate and solve 100x100 maze, measuring timing and path validity."""
    t0 = time.perf_counter()
    m = Maze(100, 100)
    m.generate_random_maze(seed=42)
    gen_time = (time.perf_counter() - t0) * 1000.0
    
    assert m.has_solution() is True
    
    # BFS
    t0 = time.perf_counter()
    res_b = bfs_solve(m.clone())
    bfs_time = (time.perf_counter() - t0) * 1000.0
    assert res_b['found'] is True
    
    # A*
    t0 = time.perf_counter()
    res_a = astar_solve(m.clone())
    astar_time = (time.perf_counter() - t0) * 1000.0
    assert res_a['found'] is True
    assert len(res_b['path']) == len(res_a['path'])
    
    # DFS
    t0 = time.perf_counter()
    res_d = dfs_solve(m.clone())
    dfs_time = (time.perf_counter() - t0) * 1000.0
    assert res_d['found'] is True
    assert len(res_d['path']) >= len(res_b['path'])
    
    print(f"\n100x100 Performance: Gen={gen_time:.1f}ms | BFS={bfs_time:.1f}ms ({res_b['nodes_expanded']} nodes) | "
          f"A*={astar_time:.1f}ms ({res_a['nodes_expanded']} nodes) | DFS={dfs_time:.1f}ms ({res_d['nodes_expanded']} nodes)")
