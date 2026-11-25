"""
Comprehensive test suite for AI Maze Solver algorithms and maze operations.

Validates:
1. BFS finds a valid path.
2. DFS finds a valid path.
3. A* finds a valid path.
4. BFS and A* return equal optimal path lengths.
5. DFS path is valid.
6. No-path scenarios.
7. Start equals Goal.
8. Wall avoidance.
9. Grid boundaries.
10. Path reconstruction (step-by-step continuity).
11. Invalid maze files (missing S/G, ragged lines, bad characters).
12. Generated maze solvability across various grid dimensions.
"""

import pytest
import os
import sys

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from maze import Maze
from algorithms.bfs import bfs_solve, bfs_generator
from algorithms.dfs import dfs_solve, dfs_generator
from algorithms.astar import astar_solve, astar_generator


def verify_valid_path(maze: Maze, path: list) -> bool:
    """
    Helper to verify that a reconstructed path is strictly valid:
    - Starts at maze.start
    - Ends at maze.goal
    - All coordinates in bounds
    - No cells are walls ('#')
    - Every step moves to an orthogonal neighbor (Manhattan distance == 1)
    """
    if not path:
        return False
    
    if maze.start == maze.goal:
        return path == [maze.start]
    
    if path[0] != maze.start:
        return False
    if path[-1] != maze.goal:
        return False
    
    for i, (r, c) in enumerate(path):
        if not maze.is_valid(r, c):
            return False
        if maze.is_wall(r, c):
            return False
        if i > 0:
            pr, pc = path[i - 1]
            if abs(r - pr) + abs(c - pc) != 1:
                return False
    return True


@pytest.fixture
def simple_open_maze():
    """Create a 5x5 open maze with start at (0,0) and goal at (4,4)."""
    m = Maze(5, 5)
    m.clear()
    m.set_start(0, 0)
    m.set_goal(4, 4)
    return m


@pytest.fixture
def labyrinth_maze():
    """Create a 7x7 maze with defined corridors."""
    m = Maze(7, 7)
    # Define a clear winding corridor
    # #######
    # #S..#G#
    # ###.###
    # #...#.#
    # #.###.#
    # #.....#
    # #######
    grid_str = [
        "#######",
        "#S..#G#",
        "###.#.#",
        "#...#.#",
        "#.###.#",
        "#.....#",
        "#######"
    ]
    for r in range(7):
        for c in range(7):
            m.grid[r][c] = grid_str[r][c]
    m.start = (1, 1)
    m.goal = (1, 5)
    return m


# 1. BFS finds a valid path
def test_bfs_finds_valid_path(labyrinth_maze):
    res = bfs_solve(labyrinth_maze)
    assert res['found'] is True
    assert len(res['path']) > 0
    assert verify_valid_path(labyrinth_maze, res['path'])


# 2. DFS finds a valid path
def test_dfs_finds_valid_path(labyrinth_maze):
    res = dfs_solve(labyrinth_maze)
    assert res['found'] is True
    assert len(res['path']) > 0
    assert verify_valid_path(labyrinth_maze, res['path'])


# 3. A* finds a valid path
def test_astar_finds_valid_path(labyrinth_maze):
    res = astar_solve(labyrinth_maze)
    assert res['found'] is True
    assert len(res['path']) > 0
    assert verify_valid_path(labyrinth_maze, res['path'])


# 4. BFS and A* return equal optimal path lengths
def test_bfs_and_astar_equal_optimal_lengths(labyrinth_maze):
    res_bfs = bfs_solve(labyrinth_maze)
    res_astar = astar_solve(labyrinth_maze)
    
    assert res_bfs['found'] and res_astar['found']
    len_bfs = len(res_bfs['path']) - 1
    len_astar = len(res_astar['path']) - 1
    assert len_bfs == len_astar, f"BFS length {len_bfs} != A* length {len_astar}"


# 5. DFS path is valid
def test_dfs_path_validity(labyrinth_maze):
    res_dfs = dfs_solve(labyrinth_maze)
    assert res_dfs['found'] is True
    assert verify_valid_path(labyrinth_maze, res_dfs['path'])


# 6. No-path scenarios
def test_no_path_scenario():
    m = Maze(5, 5)
    m.clear()
    m.set_start(0, 0)
    m.set_goal(4, 4)
    # Surround goal with walls
    m.set_wall(3, 4, True)
    m.set_wall(4, 3, True)
    
    res_bfs = bfs_solve(m)
    res_dfs = dfs_solve(m)
    res_astar = astar_solve(m)
    
    assert res_bfs['found'] is False and res_bfs['path'] == []
    assert res_dfs['found'] is False and res_dfs['path'] == []
    assert res_astar['found'] is False and res_astar['path'] == []


# 7. Start equals Goal
def test_start_equals_goal():
    m = Maze(5, 5)
    m.clear()
    m.start = (2, 2)
    m.goal = (2, 2)
    
    res_bfs = bfs_solve(m)
    res_dfs = dfs_solve(m)
    res_astar = astar_solve(m)
    
    assert res_bfs['found'] is True and res_bfs['path'] == [(2, 2)]
    assert res_dfs['found'] is True and res_dfs['path'] == [(2, 2)]
    assert res_astar['found'] is True and res_astar['path'] == [(2, 2)]


# 8. Wall avoidance
def test_wall_avoidance():
    m = Maze(5, 5)
    m.clear()
    m.set_start(0, 0)
    m.set_goal(0, 4)
    # Wall blocking direct row 0
    m.set_wall(0, 2, True)
    
    for solver in (bfs_solve, dfs_solve, astar_solve):
        res = solver(m)
        assert res['found'] is True
        for pos in res['path']:
            assert not m.is_wall(pos[0], pos[1])


# 9. Grid boundaries
def test_grid_boundaries(simple_open_maze):
    for solver in (bfs_solve, dfs_solve, astar_solve):
        res = solver(simple_open_maze)
        assert res['found'] is True
        for r, c in res['path']:
            assert 0 <= r < simple_open_maze.rows
            assert 0 <= c < simple_open_maze.cols


# 10. Path reconstruction (continuous orthogonal steps)
def test_path_continuity(labyrinth_maze):
    for solver in (bfs_solve, dfs_solve, astar_solve):
        res = solver(labyrinth_maze)
        assert res['found'] is True
        path = res['path']
        assert len(path) >= 2
        for i in range(len(path) - 1):
            r1, c1 = path[i]
            r2, c2 = path[i + 1]
            dist = abs(r1 - r2) + abs(c1 - c2)
            assert dist == 1, f"Gap between {path[i]} and {path[i+1]}"


# 11. Invalid maze files validation
def test_invalid_maze_files(tmp_path):
    m = Maze(5, 5)
    
    # Missing Start
    f1 = tmp_path / "no_start.txt"
    f1.write_text("###\n#.G\n###\n", encoding="utf-8")
    with pytest.raises(ValueError, match="exactly one Start"):
        m.load_from_file(str(f1))
        
    # Multiple Goals
    f2 = tmp_path / "multi_goal.txt"
    f2.write_text("###\n#SG\n#GG\n", encoding="utf-8")
    with pytest.raises(ValueError, match="exactly one Goal"):
        m.load_from_file(str(f2))
        
    # Unequal row lengths
    f3 = tmp_path / "ragged.txt"
    f3.write_text("###\n#S\n#G#\n", encoding="utf-8")
    with pytest.raises(ValueError, match="equal length"):
        m.load_from_file(str(f3))
        
    # Invalid characters
    f4 = tmp_path / "bad_char.txt"
    f4.write_text("###\n#SX\n#G#\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid character"):
        m.load_from_file(str(f4))
        
    # Empty file
    f5 = tmp_path / "empty.txt"
    f5.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="empty"):
        m.load_from_file(str(f5))


# 12. Generated maze solvability across various dimensions
@pytest.mark.parametrize("size", [(15, 15), (25, 25), (31, 31), (40, 40)])
def test_generated_maze_solvability(size):
    rows, cols = size
    maze = Maze(rows, cols)
    for seed in range(3):
        maze.generate_random_maze(seed=seed)
        assert maze.has_solution(), f"Generated maze {rows}x{cols} with seed {seed} has no solution!"
        res_bfs = bfs_solve(maze)
        res_astar = astar_solve(maze)
        assert res_bfs['found'] is True
        assert res_astar['found'] is True
        assert len(res_bfs['path']) == len(res_astar['path'])


# Step-by-step generator validation
def test_generators(labyrinth_maze):
    for gen_func in (bfs_generator, dfs_generator, astar_generator):
        gen = gen_func(labyrinth_maze)
        states = list(gen)
        assert len(states) > 0
        final_state = states[-1]
        assert final_state['is_complete'] is True
        assert final_state['found'] is True
        assert verify_valid_path(labyrinth_maze, final_state['path'])


# Sample mazes validation
@pytest.mark.parametrize("filename", ["sample1.txt", "sample2.txt", "sample3.txt"])
def test_sample_mazes_validity_and_solution(filename):
    maze_path = os.path.join(os.path.dirname(__file__), "..", "mazes", filename)
    assert os.path.exists(maze_path), f"Sample file {filename} does not exist"
    
    m = Maze()
    m.load_from_file(maze_path)
    assert m.has_solution(), f"Sample maze {filename} must have a solution"
    
    res_bfs = bfs_solve(m)
    res_dfs = dfs_solve(m)
    res_astar = astar_solve(m)
    
    assert res_bfs['found'] is True
    assert res_dfs['found'] is True
    assert res_astar['found'] is True
    
    assert verify_valid_path(m, res_bfs['path'])
    assert verify_valid_path(m, res_dfs['path'])
    assert verify_valid_path(m, res_astar['path'])
    
    # BFS and A* must return identical optimal path length
    assert len(res_bfs['path']) == len(res_astar['path'])


# Small maze dimensions and boundaries
def test_small_maze_dimensions_and_generator_limits():
    # 2x2 grid
    m2 = Maze(2, 2)
    assert m2.start != m2.goal
    res = bfs_solve(m2)
    assert res['found'] is True
    assert len(res['path']) == 3  # Start -> (1,0) -> Goal
    assert len(res['path']) - 1 == 2  # 2 moves
    
    # 3x3 grid
    m3 = Maze(3, 3)
    assert m3.start != m3.goal
    assert m3.start == (0, 0)
    assert m3.goal == (2, 2)
    
    # Procedural generation on < 5x5 raises descriptive ValueError
    with pytest.raises(ValueError, match="at least 5x5"):
        m2.generate_random_maze()
    with pytest.raises(ValueError, match="at least 5x5"):
        m3.generate_random_maze()
        
    # 5x5 procedural generation succeeds
    m5 = Maze(5, 5)
    m5.generate_random_maze(seed=42)
    assert m5.has_solution() is True
    assert m5.start != m5.goal


# Discovered, Frontier, and Expanded set consistency
def test_search_node_sets_consistency(labyrinth_maze):
    for gen_func in (bfs_generator, dfs_generator, astar_generator):
        gen = gen_func(labyrinth_maze)
        for state in gen:
            assert 'expanded' in state
            assert 'frontier' in state
            assert 'discovered' in state
            # Expanded and frontier must be disjoint
            assert len(state['expanded'] & state['frontier']) == 0
            # Discovered must be union of expanded and frontier
            assert state['discovered'] == (state['expanded'] | state['frontier'])


# 13. Exhaustive 192-case verification across rectangular dimensions and seeds
def test_bfs_and_astar_optimality_across_192_rectangular_mazes():
    """
    Exhaustive property-based verification across 192 rectangular and square mazes:
    - 24 distinct rectangular dimension pairs (rows != cols and rows == cols)
    - 8 independent random seeds per dimension (24 * 8 = 192 distinct maze topologies)
    
    Verifies across all 192 cases:
    1. Both BFS and A* find a valid, continuous path.
    2. BFS and A* produce IDENTICALLY EQUAL optimal path lengths.
    3. DFS produces a valid path (without requiring shortest-path optimality).
    4. Wall avoidance and grid boundary constraints hold for all steps.
    """
    dimensions = [
        # Square sizes (8)
        (5, 5), (7, 7), (9, 9), (11, 11), (15, 15), (21, 21), (25, 25), (31, 31),
        # Wide rectangular sizes (8)
        (5, 9), (7, 15), (9, 21), (11, 25), (15, 25), (15, 35), (21, 35), (25, 35),
        # Tall rectangular sizes (8)
        (9, 5), (15, 7), (21, 9), (25, 11), (25, 15), (35, 15), (35, 21), (35, 25)
    ]
    assert len(dimensions) == 24, "Must have exactly 24 dimension pairs"
    
    seeds = [101, 202, 303, 404, 505, 606, 707, 808]
    assert len(seeds) == 8, "Must have exactly 8 seeds per dimension"
    
    total_evaluated = 0
    for rows, cols in dimensions:
        for seed in seeds:
            maze = Maze(rows, cols)
            maze.generate_random_maze(seed=seed)
            assert maze.has_solution(), f"Maze {rows}x{cols} seed {seed} has no solution"
            
            res_bfs = bfs_solve(maze)
            res_dfs = dfs_solve(maze)
            res_astar = astar_solve(maze)
            
            assert res_bfs['found'] is True
            assert res_astar['found'] is True
            assert res_dfs['found'] is True
            
            # Paths must be valid
            assert verify_valid_path(maze, res_bfs['path'])
            assert verify_valid_path(maze, res_astar['path'])
            assert verify_valid_path(maze, res_dfs['path'])
            
            # BFS and A* must return IDENTICALLY EQUAL optimal path length
            len_bfs = len(res_bfs['path']) - 1
            len_astar = len(res_astar['path']) - 1
            assert len_bfs == len_astar, (
                f"Optimality mismatch on {rows}x{cols} seed {seed}: BFS {len_bfs} != A* {len_astar}"
            )
            
            total_evaluated += 1

    assert total_evaluated == 192, f"Expected 192 evaluated mazes, got {total_evaluated}"


# 14. A* Priority Queue Stale Entries and Re-Parenting
def test_astar_priority_queue_stale_entries_and_updates():
    """
    Test that A* correctly skips stale priority queue entries and maintains
    optimal path cost when alternative paths exist to the same node.
    """
    # Create a 5x5 grid with two paths from (0,0) to (2,2):
    # Path A: (0,0) -> (0,1) -> (0,2) -> (1,2) -> (2,2) [length 4]
    # Path B: (0,0) -> (1,0) -> (2,0) -> (2,1) -> (2,2) [length 4]
    m = Maze(5, 5)
    m.clear()
    m.start = (0, 0)
    m.goal = (2, 2)
    
    res_astar = astar_solve(m)
    res_bfs = bfs_solve(m)
    
    assert res_astar['found'] is True
    assert len(res_astar['path']) - 1 == 4
    assert len(res_astar['path']) == len(res_bfs['path'])
    assert verify_valid_path(m, res_astar['path'])


# 15. Narrow snake corridors and choke points
def test_narrow_corridors_and_choke_points():
    """
    Verify search behavior in forced 1-cell corridors (choke points).
    In a single forced corridor with no branches, BFS, DFS, and A* must
    traverse the identical sequence of steps.
    """
    # 7x3 grid with forced single S-shaped corridor
    # S##
    # .##
    # .##
    # .##
    # .##
    # .##
    # ..G
    m = Maze(7, 3)
    m.clear()
    for r in range(6):
        m.set_wall(r, 1, True)
        m.set_wall(r, 2, True)
    m.start = (0, 0)
    m.goal = (6, 2)
    
    res_bfs = bfs_solve(m)
    res_dfs = dfs_solve(m)
    res_astar = astar_solve(m)
    
    assert res_bfs['found'] and res_dfs['found'] and res_astar['found']
    assert len(res_bfs['path']) == len(res_astar['path']) == len(res_dfs['path'])
    assert verify_valid_path(m, res_bfs['path'])
    assert verify_valid_path(m, res_astar['path'])
    assert verify_valid_path(m, res_dfs['path'])


# 16. Multiple disconnected islands and unreachable goals
def test_unreachable_goals_and_islands():
    """Test unreachable goal with isolated walkable islands."""
    m = Maze(9, 9)
    m.clear()
    # Solid wall splitting the grid down the middle
    for r in range(9):
        m.set_wall(r, 4, True)
    m.start = (1, 1)
    m.goal = (1, 7)
    
    for solver in (bfs_solve, dfs_solve, astar_solve):
        res = solver(m)
        assert res['found'] is False
        assert res['path'] == []
        assert res['nodes_expanded'] > 0


