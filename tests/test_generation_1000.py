"""
Phase 3.3: Maze Generation Testing Suite (1,000+ Deterministic Seeds)
Verifies:
1. Start/Goal validity, distinctness, and walkability.
2. Solid outer wall borders.
3. 100% solvability verified via independent reference BFS.
4. Valid grid values across dimensions from 5 to 40 (odd/even squares and rectangles).
"""

import random
from collections import deque
import pytest

from maze import Maze


def reference_bfs_solvable(grid, rows, cols, start, goal):
    """Independent reference BFS checking solvability."""
    if start == goal:
        return True
    q = deque([(start[0], start[1])])
    visited = {start}
    while q:
        r, c = q.popleft()
        if (r, c) == goal:
            return True
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] != '#':
                if (nr, nc) not in visited:
                    visited.add((nr, nc))
                    q.append((nr, nc))
    return False


def test_small_generation_cases():
    """Explicitly verify small generation cases: 5x5, 5x6, 6x5, 6x6, 7x7, 10x10."""
    small_dims = [(5, 5), (5, 6), (6, 5), (6, 6), (7, 7), (10, 10)]
    for r, c in small_dims:
        m = Maze(r, c)
        m.generate_random_maze(seed=42)
        
        # 1. Start and Goal valid
        assert m.is_valid(m.start[0], m.start[1])
        assert m.is_valid(m.goal[0], m.goal[1])
        assert m.start != m.goal
        
        # 2. Walkable
        assert m.is_walkable(m.start[0], m.start[1])
        assert m.is_walkable(m.goal[0], m.goal[1])
        
        # 3. Outer borders are solid walls
        for col in range(c):
            assert m.is_wall(0, col), f"Top border not wall at (0, {col}) for {r}x{c}"
            assert m.is_wall(r - 1, col), f"Bottom border not wall at ({r-1}, {col}) for {r}x{c}"
        for row in range(r):
            assert m.is_wall(row, 0), f"Left border not wall at ({row}, 0) for {r}x{c}"
            assert m.is_wall(row, c - 1), f"Right border not wall at ({row}, {c-1}) for {r}x{c}"
            
        # 4. Solvable
        assert reference_bfs_solvable(m.grid, r, c, m.start, m.goal), f"Small maze {r}x{c} not solvable"


def test_1000_seeds_maze_generation():
    """
    Test maze generation across 1,000 deterministic seeds covering dimensions from 5 to 40:
    - Odd square
    - Even square
    - Odd rectangular
    - Even rectangular
    - Mixed odd/even dimensions
    """
    dimension_pool = [
        # Odd square
        (5, 5), (7, 7), (15, 15), (25, 25), (31, 31),
        # Even square
        (6, 6), (10, 10), (20, 20), (30, 30), (40, 40),
        # Odd rectangular
        (15, 25), (25, 15), (21, 35), (31, 15),
        # Even rectangular
        (10, 20), (20, 10), (20, 30), (40, 24),
        # Mixed odd/even
        (15, 20), (20, 15), (25, 30), (30, 25), (35, 40), (40, 35)
    ]
    
    total_seeds = 1000
    for seed in range(1, total_seeds + 1):
        r, c = dimension_pool[(seed - 1) % len(dimension_pool)]
        m = Maze(r, c)
        m.generate_random_maze(seed=seed)
        
        # 1. Start and Goal valid and distinct
        sr, sc = m.start
        gr, gc = m.goal
        assert 0 <= sr < r and 0 <= sc < c, f"Seed {seed} ({r}x{c}): start out of bounds"
        assert 0 <= gr < r and 0 <= gc < c, f"Seed {seed} ({r}x{c}): goal out of bounds"
        assert (sr, sc) != (gr, gc), f"Seed {seed} ({r}x{c}): start equals goal"
        
        # 2. Start and Goal walkable
        assert m.grid[sr][sc] != '#', f"Seed {seed} ({r}x{c}): start is a wall"
        assert m.grid[gr][gc] != '#', f"Seed {seed} ({r}x{c}): goal is a wall"
        
        # 3. Outer borders are solid walls
        for col_idx in range(c):
            assert m.grid[0][col_idx] == '#', f"Seed {seed} ({r}x{c}): top border not wall at (0, {col_idx})"
            assert m.grid[r - 1][col_idx] == '#', f"Seed {seed} ({r}x{c}): bottom border not wall at ({r-1}, {col_idx})"
        for row_idx in range(r):
            assert m.grid[row_idx][0] == '#', f"Seed {seed} ({r}x{c}): left border not wall at ({row_idx}, 0)"
            assert m.grid[row_idx][c - 1] == '#', f"Seed {seed} ({r}x{c}): right border not wall at ({row_idx}, {c-1})"
            
        # 4. Solvability verified via independent BFS
        solvable = reference_bfs_solvable(m.grid, r, c, (sr, sc), (gr, gc))
        assert solvable is True, f"Seed {seed} ({r}x{c}): Maze is not solvable"
        
        # 5. No invalid grid characters
        valid_chars = {'#', '.', 'S', 'G'}
        for row in range(r):
            for col in range(c):
                assert m.grid[row][col] in valid_chars, f"Seed {seed} ({r}x{c}): Invalid char {m.grid[row][col]}"
