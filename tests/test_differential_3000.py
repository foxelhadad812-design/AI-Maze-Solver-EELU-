"""
Phase 3.2: Differential Testing Suite (3,000+ Mazes)
Compares BFS, DFS, and A* against an independent reference BFS implementation.
Ensures zero coupling with project search helper functions.
"""

import random
from collections import deque
import pytest

from maze import Maze
from algorithms.bfs import bfs_solve, bfs_generator
from algorithms.dfs import dfs_solve, dfs_generator
from algorithms.astar import astar_solve, astar_generator


def reference_bfs(grid, rows, cols, start, goal):
    """
    Independent reference Breadth-First Search.
    Does not use any project code, data structures, or helper functions.
    grid uses '#' for wall, '.' for open.
    """
    if start == goal:
        return True, 0
    q = deque([(start[0], start[1], 0)])
    visited = {start}
    while q:
        r, c, dist = q.popleft()
        if (r, c) == goal:
            return True, dist
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] != '#':
                if (nr, nc) not in visited:
                    visited.add((nr, nc))
                    q.append((nr, nc, dist + 1))
    return False, None


def validate_path(grid, rows, cols, start, goal, path):
    """Strict mathematical validation of a solution path."""
    if not path:
        return False, "Path is empty"
    if path[0] != start:
        return False, f"Path start {path[0]} != start {start}"
    if path[-1] != goal:
        return False, f"Path goal {path[-1]} != goal {goal}"
    if len(set(path)) != len(path):
        return False, "Path contains duplicate/cyclic nodes"
    for idx in range(len(path)):
        r, c = path[idx]
        if not (0 <= r < rows and 0 <= c < cols):
            return False, f"Coordinate ({r}, {c}) is out of bounds"
        if grid[r][c] == '#':
            return False, f"Coordinate ({r}, {c}) is a wall"
        if idx > 0:
            pr, pc = path[idx - 1]
            if abs(r - pr) + abs(c - pc) != 1:
                return False, f"Step ({pr},{pc}) -> ({r},{c}) is not an orthogonal cardinal step"
    return True, "Valid"


def test_differential_3000_mazes():
    """
    Generate 3,000 distinct deterministic random maze topologies (dimensions 2x2 to 25x25,
    wall densities 10% to 55%, random start/goal coordinates).
    Verify BFS and A* shortest path optimality, DFS path validity, and solve vs generator parity.
    """
    rng = random.Random(20261111)
    total_cases = 3000
    solvable_count = 0
    unsolvable_count = 0

    for i in range(total_cases):
        rows = rng.randint(2, 25)
        cols = rng.randint(2, 25)
        density = rng.uniform(0.10, 0.55)
        raw_grid = [['#' if rng.random() < density else '.' for _ in range(cols)] for _ in range(rows)]
        
        sr, sc = rng.randint(0, rows - 1), rng.randint(0, cols - 1)
        gr, gc = rng.randint(0, rows - 1), rng.randint(0, cols - 1)
        raw_grid[sr][sc] = '.'
        raw_grid[gr][gc] = '.'
        
        ref_found, ref_dist = reference_bfs(raw_grid, rows, cols, (sr, sc), (gr, gc))
        if ref_found:
            solvable_count += 1
        else:
            unsolvable_count += 1
            
        m = Maze(rows, cols)
        m.grid = [row[:] for row in raw_grid]
        m.start = (sr, sc)
        m.goal = (gr, gc)
        if (sr, sc) != (gr, gc):
            m.grid[sr][sc] = m.START
            m.grid[gr][gc] = m.GOAL
        
        # 1. BFS Verification
        res_bfs = bfs_solve(m.clone())
        assert res_bfs['found'] == ref_found, f"Case {i}: BFS found mismatch (got {res_bfs['found']}, exp {ref_found})"
        if ref_found:
            p_bfs = res_bfs['path']
            bfs_steps = len(p_bfs) - 1 if p_bfs else 0
            assert bfs_steps == ref_dist, f"Case {i}: BFS path steps {bfs_steps} != ref_dist {ref_dist}"
            valid, msg = validate_path(raw_grid, rows, cols, (sr, sc), (gr, gc), p_bfs)
            assert valid, f"Case {i}: BFS path invalid - {msg}"
        else:
            assert res_bfs['path'] == [] or res_bfs['path'] is None

        # 2. A* Verification
        res_astar = astar_solve(m.clone())
        assert res_astar['found'] == ref_found, f"Case {i}: A* found mismatch (got {res_astar['found']}, exp {ref_found})"
        if ref_found:
            p_astar = res_astar['path']
            astar_steps = len(p_astar) - 1 if p_astar else 0
            assert astar_steps == ref_dist, f"Case {i}: A* path steps {astar_steps} != ref_dist {ref_dist}"
            valid, msg = validate_path(raw_grid, rows, cols, (sr, sc), (gr, gc), p_astar)
            assert valid, f"Case {i}: A* path invalid - {msg}"
        else:
            assert res_astar['path'] == [] or res_astar['path'] is None

        # 3. DFS Verification
        res_dfs = dfs_solve(m.clone())
        assert res_dfs['found'] == ref_found, f"Case {i}: DFS found mismatch (got {res_dfs['found']}, exp {ref_found})"
        if ref_found:
            p_dfs = res_dfs['path']
            dfs_steps = len(p_dfs) - 1 if p_dfs else 0
            # DFS is non-optimal, but its path must be at least as long as shortest path
            assert dfs_steps >= ref_dist, f"Case {i}: DFS steps {dfs_steps} < ref_dist {ref_dist}"
            valid, msg = validate_path(raw_grid, rows, cols, (sr, sc), (gr, gc), p_dfs)
            assert valid, f"Case {i}: DFS path invalid - {msg}"
        else:
            assert res_dfs['path'] == [] or res_dfs['path'] is None

        # 4. Solve vs Generator Parity Verification (sampled every 25 cases = 120 full cases)
        if i % 25 == 0:
            for algo_name, solver, generator in [
                ("BFS", bfs_solve, bfs_generator),
                ("DFS", dfs_solve, dfs_generator),
                ("A*", astar_solve, astar_generator),
            ]:
                s_res = solver(m.clone())
                g_states = list(generator(m.clone()))
                final_g = g_states[-1]
                assert s_res['found'] == final_g['found'], f"Case {i} {algo_name}: Parity found mismatch"
                assert s_res['path'] == final_g['path'], f"Case {i} {algo_name}: Parity path mismatch"
                assert s_res['nodes_expanded'] == final_g['nodes_expanded'], f"Case {i} {algo_name}: Parity nodes mismatch"
                assert final_g['is_complete'] is True
                assert 'expanded' in final_g
                assert 'frontier' in final_g
                assert 'discovered' in final_g

    assert solvable_count > 0 and unsolvable_count > 0, "Test set must contain both solvable and unsolvable cases"
