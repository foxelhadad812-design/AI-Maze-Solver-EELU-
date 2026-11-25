"""
Automated test suite for Human Challenge Mode (Step 2A).

Covers:
1. Initial player position.
2. Initial move counter.
3. Initial unique visited cell count.
4. Valid upward movement.
5. Valid downward movement.
6. Valid left movement.
7. Valid right movement.
8. Wall collision rejection.
9. Boundary collision rejection.
10. Initial wall/boundary collision does not start the timer.
11. Invalid and diagonal movement rejection.
12. Move counter correctness and monotonicity.
13. Unique cell tracking with repeated visits.
14. Goal detection and victory trigger.
15. Movement rejection after victory.
16. Monotonic timer start and stop behavior with injectable clock.
17. Idempotent start() preserves original start_time.
18. Reset behavior.
19. Start-equals-Goal behavior (immediate victory with 0 moves).
20. Zero-length optimality ratio (100% when Start equals Goal).
21. AI comparison prohibited before victory.
22. Maze clone isolation: 3 distinct Maze objects, separate grid lists, independent nested rows.
23. Original maze immutability during AI comparison.
24. Suboptimal vs optimal path optimality ratios.
25. Convenience directional helper methods (move_up, move_down, move_left, move_right).
26. Structured result dictionary completeness.
"""

import os
import sys
import pytest

# Ensure parent directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from maze import Maze
from challenge import HumanChallenge, ChallengeStatus


class FakeClock:
    """Deterministic monotonic clock fixture for high-resolution timing tests."""
    def __init__(self, initial_time: float = 1000.0):
        self.time_val = initial_time

    def __call__(self) -> float:
        return self.time_val

    def advance(self, seconds: float) -> None:
        self.time_val += seconds


@pytest.fixture
def fake_clock():
    """Return a fresh FakeClock initialized to 1000.0 seconds."""
    return FakeClock(1000.0)


@pytest.fixture
def open_maze_5x5():
    """Create a fully walkable 5x5 maze with start=(1, 1) and goal=(3, 3)."""
    maze = Maze(5, 5)
    for r in range(5):
        for c in range(5):
            if (r, c) == maze.start:
                maze.grid[r][c] = Maze.START
            elif (r, c) == maze.goal:
                maze.grid[r][c] = Maze.GOAL
            else:
                maze.grid[r][c] = Maze.OPEN
    return maze


# ============================================================================
# 1. INITIALIZATION TESTS
# ============================================================================

def test_initial_player_position(open_maze_5x5):
    """Verify player starts exactly at maze.start."""
    ch = HumanChallenge(open_maze_5x5)
    assert ch.player_pos == open_maze_5x5.start
    assert ch.goal == open_maze_5x5.goal
    assert ch.path == [open_maze_5x5.start]


def test_initial_move_counter(open_maze_5x5):
    """Verify initial move count is zero."""
    ch = HumanChallenge(open_maze_5x5)
    assert ch.move_count == 0
    assert ch.human_path_length == 0


def test_initial_unique_visited_cells(open_maze_5x5):
    """Verify initial visited cells contains only the start position."""
    ch = HumanChallenge(open_maze_5x5)
    assert ch.visited_cells == {open_maze_5x5.start}
    assert len(ch.visited_cells) == 1
    assert ch.status == ChallengeStatus.READY
    assert ch.is_ready is True
    assert ch.is_playing is False
    assert ch.is_won is False


# ============================================================================
# 2. MOVEMENT VALIDATION TESTS
# ============================================================================

def test_valid_orthogonal_move_down(open_maze_5x5):
    """Verify valid downward movement updates coordinates and move count."""
    ch = HumanChallenge(open_maze_5x5)
    start_r, start_c = open_maze_5x5.start
    success = ch.move(1, 0)
    assert success is True
    assert ch.player_pos == (start_r + 1, start_c)
    assert ch.move_count == 1
    assert ch.human_path_length == 1
    assert ch.path == [open_maze_5x5.start, (start_r + 1, start_c)]


def test_valid_orthogonal_move_right(open_maze_5x5):
    """Verify valid rightward movement updates coordinates and move count."""
    ch = HumanChallenge(open_maze_5x5)
    start_r, start_c = open_maze_5x5.start
    success = ch.move(0, 1)
    assert success is True
    assert ch.player_pos == (start_r, start_c + 1)
    assert ch.move_count == 1


def test_valid_orthogonal_move_up_and_left(open_maze_5x5):
    """Verify upward and leftward movement after moving away from boundary."""
    ch = HumanChallenge(open_maze_5x5)
    # Move right then down
    ch.move(0, 1)  # (1, 2)
    ch.move(1, 0)  # (2, 2)
    assert ch.player_pos == (2, 2)
    
    # Move Up
    success_up = ch.move(-1, 0)  # (1, 2)
    assert success_up is True
    assert ch.player_pos == (1, 2)
    
    # Move Left
    success_left = ch.move(0, -1)  # (1, 1)
    assert success_left is True
    assert ch.player_pos == (1, 1)


def test_wall_collision_rejection(open_maze_5x5):
    """Verify movement into walls is rejected without incrementing moves."""
    # Place a wall directly below start (2, 1)
    start_r, start_c = open_maze_5x5.start
    open_maze_5x5.set_wall(start_r + 1, start_c, True)
    ch = HumanChallenge(open_maze_5x5)

    # Attempt to move into wall
    success = ch.move(1, 0)
    assert success is False
    assert ch.player_pos == open_maze_5x5.start
    assert ch.move_count == 0
    assert ch.human_path_length == 0
    assert ch.path == [open_maze_5x5.start]


def test_initial_wall_collision_does_not_start_timer(open_maze_5x5, fake_clock):
    """Verify that an initial wall collision in READY state does not start the timer."""
    start_r, start_c = open_maze_5x5.start
    open_maze_5x5.set_wall(start_r + 1, start_c, True)

    ch = HumanChallenge(open_maze_5x5, clock_func=fake_clock)
    assert ch.status == ChallengeStatus.READY
    assert ch.start_time is None

    fake_clock.advance(10.0)
    # Attempt to move into wall
    assert ch.move(1, 0) is False

    fake_clock.advance(5.0)
    # Challenge must remain READY with no active timer
    assert ch.status == ChallengeStatus.READY
    assert ch.start_time is None
    assert ch.elapsed_time == 0.0
    assert ch.move_count == 0
    assert ch.player_pos == open_maze_5x5.start


def test_boundary_collision_rejection(open_maze_5x5):
    """Verify movement outside maze boundary is rejected without incrementing moves."""
    maze = Maze(3, 3)
    maze.start = (0, 0)
    maze.goal = (2, 2)
    ch = HumanChallenge(maze)

    # Attempt to move Up past top boundary (r = -1)
    assert ch.move(-1, 0) is False
    assert ch.player_pos == (0, 0)
    assert ch.move_count == 0

    # Attempt to move Left past left boundary (c = -1)
    assert ch.move(0, -1) is False
    assert ch.player_pos == (0, 0)
    assert ch.move_count == 0


def test_initial_boundary_collision_does_not_start_timer(fake_clock):
    """Verify that an initial boundary collision in READY state does not start the timer."""
    maze = Maze(3, 3)
    maze.start = (0, 0)
    maze.goal = (2, 2)

    ch = HumanChallenge(maze, clock_func=fake_clock)
    assert ch.status == ChallengeStatus.READY
    assert ch.start_time is None

    fake_clock.advance(10.0)
    # Attempt to move out of bounds (Up)
    assert ch.move(-1, 0) is False
    # Attempt to move out of bounds (Left)
    assert ch.move(0, -1) is False

    fake_clock.advance(5.0)
    # Challenge must remain READY with no active timer
    assert ch.status == ChallengeStatus.READY
    assert ch.start_time is None
    assert ch.elapsed_time == 0.0
    assert ch.move_count == 0
    assert ch.player_pos == (0, 0)


def test_invalid_and_diagonal_movement_rejection(open_maze_5x5):
    """Verify diagonal, zero, or arbitrary delta movements are rejected."""
    ch = HumanChallenge(open_maze_5x5)

    # Diagonals
    assert ch.move(1, 1) is False
    assert ch.move(-1, -1) is False
    assert ch.move(1, -1) is False
    assert ch.move(-1, 1) is False

    # Zero displacement
    assert ch.move(0, 0) is False

    # Multistep jumps
    assert ch.move(2, 0) is False
    assert ch.move(0, 3) is False

    assert ch.move_count == 0
    assert ch.player_pos == open_maze_5x5.start


def test_convenience_directional_methods(open_maze_5x5):
    """Verify move_up, move_down, move_left, move_right methods."""
    ch = HumanChallenge(open_maze_5x5)
    assert ch.move_right() is True
    assert ch.player_pos == (1, 2)
    assert ch.move_down() is True
    assert ch.player_pos == (2, 2)
    assert ch.move_left() is True
    assert ch.player_pos == (2, 1)
    assert ch.move_up() is True
    assert ch.player_pos == (1, 1)
    assert ch.move_count == 4


# ============================================================================
# 3. UNIQUE CELL TRACKING & MOVE COUNTING
# ============================================================================

def test_unique_cell_tracking_with_repeated_visits(open_maze_5x5):
    """Verify unique visited cells set ignores duplicate revisits."""
    ch = HumanChallenge(open_maze_5x5)
    # Start at (1, 1) -> move right to (1, 2) -> move left back to (1, 1)
    ch.move(0, 1)  # (1, 2)
    ch.move(0, -1) # (1, 1)
    
    assert ch.move_count == 2
    assert ch.human_path_length == 2
    assert len(ch.path) == 3  # [(1,1), (1,2), (1,1)]
    # Visited distinct cells should be only 2
    assert ch.visited_cells == {(1, 1), (1, 2)}
    assert len(ch.visited_cells) == 2


# ============================================================================
# 4. VICTORY, LIFECYCLE & RESET TESTS
# ============================================================================

def test_goal_detection_and_victory(open_maze_5x5):
    """Verify reaching the goal cell triggers victory and stops the timer."""
    ch = HumanChallenge(open_maze_5x5)
    # Start is (1, 1), Goal is (3, 3)
    # Move: (1,1) -> (2,1) -> (3,1) -> (3,2) -> (3,3)
    assert ch.move(1, 0) is True  # (2, 1)
    assert ch.move(1, 0) is True  # (3, 1)
    assert ch.move(0, 1) is True  # (3, 2)
    assert ch.is_won is False

    assert ch.move(0, 1) is True  # (3, 3) reaches Goal!
    assert ch.player_pos == open_maze_5x5.goal
    assert ch.is_won is True
    assert ch.status == ChallengeStatus.WON
    assert ch.move_count == 4
    assert ch.human_path_length == 4


def test_movement_rejection_after_victory(open_maze_5x5):
    """Verify that any movement attempt after winning is rejected."""
    ch = HumanChallenge(open_maze_5x5)
    # Navigate to Goal: (1,1) -> (2,1) -> (3,1) -> (3,2) -> (3,3)
    ch.move(1, 0)
    ch.move(1, 0)
    ch.move(0, 1)
    ch.move(0, 1)
    assert ch.is_won is True

    # Try to move away from goal
    assert ch.move(0, -1) is False
    assert ch.move(1, 0) is False
    assert ch.move(-1, 0) is False
    assert ch.move_count == 4  # Unchanged
    assert ch.player_pos == open_maze_5x5.goal


def test_reset_behavior(open_maze_5x5):
    """Verify reset restores initial challenge state completely."""
    ch = HumanChallenge(open_maze_5x5)
    ch.move(1, 0)
    ch.move(0, 1)
    assert ch.move_count == 2
    assert ch.player_pos != open_maze_5x5.start

    ch.reset()
    assert ch.player_pos == open_maze_5x5.start
    assert ch.move_count == 0
    assert ch.human_path_length == 0
    assert ch.path == [open_maze_5x5.start]
    assert ch.visited_cells == {open_maze_5x5.start}
    assert ch.status == ChallengeStatus.READY
    assert ch.start_time is None
    assert ch.end_time is None
    assert ch.elapsed_time == 0.0


# ============================================================================
# 5. HIGH-RESOLUTION DETERMINISTIC TIMING TESTS
# ============================================================================

def test_timer_start_and_stop_behavior(open_maze_5x5, fake_clock):
    """Verify monotonic timer starts, advances, and freezes upon victory."""
    ch = HumanChallenge(open_maze_5x5, clock_func=fake_clock)
    assert ch.elapsed_time == 0.0

    # Start challenge
    ch.start()
    assert ch.status == ChallengeStatus.PLAYING
    
    # Advance fake time by 5.25 seconds during play
    fake_clock.advance(5.25)
    assert ch.elapsed_time == 5.25

    # Move to goal
    ch.move(1, 0)
    ch.move(1, 0)
    ch.move(0, 1)
    fake_clock.advance(3.0)
    ch.move(0, 1)  # Reaches goal at 1008.25s
    
    assert ch.is_won is True
    completion_time = ch.elapsed_time
    assert completion_time == 8.25

    # Advance clock further after winning; elapsed time must remain frozen!
    fake_clock.advance(100.0)
    assert ch.elapsed_time == 8.25


def test_start_idempotency_preserves_timer(open_maze_5x5, fake_clock):
    """
    Verify start() is idempotent:
    1. Start the challenge.
    2. Advance the clock by 10 seconds.
    3. Call start() again while PLAYING.
    4. Advance the clock by another 5 seconds.
    5. Verify elapsed_time is 15 seconds, not 5 seconds.
    """
    ch = HumanChallenge(open_maze_5x5, clock_func=fake_clock)
    assert ch.status == ChallengeStatus.READY

    ch.start()
    assert ch.status == ChallengeStatus.PLAYING
    fake_clock.advance(10.0)
    assert ch.elapsed_time == 10.0

    # Call start() again while in PLAYING state
    ch.start()
    assert ch.status == ChallengeStatus.PLAYING

    # Advance clock another 5 seconds
    fake_clock.advance(5.0)
    # Elapsed time must be 15.0 seconds (original start_time preserved, NOT restarted)
    assert ch.elapsed_time == 15.0


def test_pause_and_resume_exclude_paused_time_and_reject_paused_moves(open_maze_5x5, fake_clock):
    """Pause freezes the challenge clock and movement until resumed."""
    ch = HumanChallenge(open_maze_5x5, clock_func=fake_clock)
    ch.start()
    fake_clock.advance(4.0)
    assert ch.pause() is True
    assert ch.status == ChallengeStatus.PAUSED
    assert ch.elapsed_time == 4.0
    pos_before = ch.player_pos
    moves_before = ch.move_count

    fake_clock.advance(25.0)
    assert ch.elapsed_time == 4.0
    assert ch.move_right() is False
    assert ch.player_pos == pos_before
    assert ch.move_count == moves_before

    assert ch.resume() is True
    assert ch.status == ChallengeStatus.PLAYING
    fake_clock.advance(3.0)
    assert ch.elapsed_time == 7.0

    # A second pause/resume cycle adds only active time.
    assert ch.pause() is True
    fake_clock.advance(6.0)
    assert ch.resume() is True
    assert ch.elapsed_time == 7.0


def test_move_budget_failure_freezes_timer_and_closes_movement(open_maze_5x5, fake_clock):
    ch = HumanChallenge(open_maze_5x5, clock_func=fake_clock)
    ch.start()
    fake_clock.advance(3.0)
    assert ch.fail() is True
    assert ch.status == ChallengeStatus.LOST
    elapsed = ch.elapsed_time
    fake_clock.advance(20.0)
    assert ch.elapsed_time == elapsed
    assert ch.move_right() is False
    assert ch.fail() is False


# ============================================================================
# 6. START EQUALS GOAL EDGE CASE TESTS
# ============================================================================

def test_start_equals_goal_immediate_completion(fake_clock):
    """Verify Start equals Goal immediately completes with 0 moves."""
    maze = Maze(3, 3)
    maze.start = (1, 1)
    maze.goal = (1, 1)

    ch = HumanChallenge(maze, clock_func=fake_clock)
    assert ch.is_won is True
    assert ch.status == ChallengeStatus.WON
    assert ch.move_count == 0
    assert ch.human_path_length == 0
    assert ch.path == [(1, 1)]
    assert ch.visited_cells == {(1, 1)}

    # Attempting to move is rejected
    assert ch.move(1, 0) is False
    assert ch.move_count == 0


def test_start_equals_goal_optimality_ratio(fake_clock):
    """Verify zero-length Start equals Goal yields exactly 100% optimality without ZeroDivisionError."""
    maze = Maze(3, 3)
    maze.start = (1, 1)
    maze.goal = (1, 1)

    ch = HumanChallenge(maze, clock_func=fake_clock)
    assert ch.is_won is True
    
    # BFS optimal path length for start == goal is 0 moves
    opt_ratio = ch.calculate_optimality_ratio(bfs_path_length=0)
    assert opt_ratio == 100.0


# ============================================================================
# 7. OPTIMALITY RATIO CALCULATIONS
# ============================================================================

def test_optimal_player_optimality_ratio(open_maze_5x5):
    """Verify optimal player achieves 100.0% optimality ratio."""
    ch = HumanChallenge(open_maze_5x5)
    # Optimal path from (1, 1) to (3, 3) has Manhattan length 4:
    ch.move(1, 0)
    ch.move(1, 0)
    ch.move(0, 1)
    ch.move(0, 1)
    assert ch.is_won is True
    assert ch.move_count == 4

    ratio = ch.calculate_optimality_ratio(bfs_path_length=4)
    assert ratio == 100.0


def test_suboptimal_player_optimality_ratio(open_maze_5x5):
    """Verify suboptimal player with detours achieves < 100.0% ratio."""
    ch = HumanChallenge(open_maze_5x5)
    # Take a detour: move right, left, right, down, down, right
    ch.move(0, 1)  # (1, 2)
    ch.move(0, -1) # (1, 1) back
    ch.move(0, 1)  # (1, 2)
    ch.move(1, 0)  # (2, 2)
    ch.move(1, 0)  # (3, 2)
    ch.move(0, 1)  # (3, 3) goal
    assert ch.is_won is True
    assert ch.move_count == 6  # 2 extra detour moves

    ratio = ch.calculate_optimality_ratio(bfs_path_length=4)
    assert ratio == pytest.approx((4 / 6) * 100.0, rel=1e-3)


def test_optimality_ratio_prohibited_before_victory(open_maze_5x5):
    """Verify calculate_optimality_ratio raises RuntimeError if challenge is not won."""
    ch = HumanChallenge(open_maze_5x5)
    assert ch.is_won is False
    with pytest.raises(RuntimeError, match="Cannot calculate optimality ratio for an incomplete challenge"):
        ch.calculate_optimality_ratio(bfs_path_length=4)


def test_optimality_ratio_invalid_path_length_raises_value_error(open_maze_5x5):
    """Verify calculate_optimality_ratio raises ValueError for negative or invalid path lengths."""
    ch = HumanChallenge(open_maze_5x5)
    ch.move(1, 0)
    ch.move(1, 0)
    ch.move(0, 1)
    ch.move(0, 1)
    assert ch.is_won is True

    with pytest.raises(ValueError, match="Cannot calculate optimality ratio"):
        ch.calculate_optimality_ratio(bfs_path_length=-1)


# ============================================================================
# 8. AI COMPARISON ORCHESTRATION & CLONE ISOLATION
# ============================================================================

def test_ai_comparison_prohibited_before_victory(open_maze_5x5):
    """Verify AI comparison raises RuntimeError if invoked before player wins."""
    ch = HumanChallenge(open_maze_5x5)
    assert ch.is_won is False
    with pytest.raises(RuntimeError, match="AI comparison cannot be run before the challenge is won"):
        ch.compare_with_ai()


def test_ai_comparison_execution_and_clone_isolation(open_maze_5x5):
    """Verify AI comparison executes BFS, DFS, A* on independent clones and preserves original maze."""
    # Capture original maze state snapshot
    original_grid = [row[:] for row in open_maze_5x5.grid]
    original_start = open_maze_5x5.start
    original_goal = open_maze_5x5.goal

    ch = HumanChallenge(open_maze_5x5)
    # Solve maze manually
    ch.move(1, 0)
    ch.move(1, 0)
    ch.move(0, 1)
    ch.move(0, 1)
    assert ch.is_won is True

    # Run AI comparison
    comparison = ch.compare_with_ai()

    # Verify return structure
    assert "human" in comparison
    assert "ai" in comparison
    assert "optimality_ratio" in comparison
    assert "optimal_path_length" in comparison

    # Verify algorithms evaluated
    ai = comparison["ai"]
    assert "BFS" in ai
    assert "DFS" in ai
    assert "A*" in ai

    # Verify BFS and A* found optimal path (4 transitions)
    assert ai["BFS"]["found"] is True
    assert ai["BFS"]["path_length"] == 4
    assert ai["A*"]["found"] is True
    assert ai["A*"]["path_length"] == 4

    # Verify human results
    assert comparison["human"]["move_count"] == 4
    assert comparison["optimality_ratio"] == 100.0

    # Verify original maze immutability
    assert open_maze_5x5.grid == original_grid
    assert open_maze_5x5.start == original_start
    assert open_maze_5x5.goal == original_goal


def test_ai_clone_three_distinct_objects_and_no_shared_rows(open_maze_5x5, monkeypatch):
    """
    Verify AI comparison creates 3 distinct Maze objects with independent
    top-level grids and nested grid rows for BFS, DFS, and A*.
    """
    import challenge
    captured_mazes = []

    orig_bfs = challenge.bfs_solve
    orig_dfs = challenge.dfs_solve
    orig_astar = challenge.astar_solve

    def spy_bfs(m):
        captured_mazes.append(("BFS", m))
        return orig_bfs(m)

    def spy_dfs(m):
        captured_mazes.append(("DFS", m))
        return orig_dfs(m)

    def spy_astar(m):
        captured_mazes.append(("A*", m))
        return orig_astar(m)

    monkeypatch.setattr(challenge, "bfs_solve", spy_bfs)
    monkeypatch.setattr(challenge, "dfs_solve", spy_dfs)
    monkeypatch.setattr(challenge, "astar_solve", spy_astar)

    ch = HumanChallenge(open_maze_5x5)
    # Solve maze:
    ch.move(1, 0)
    ch.move(1, 0)
    ch.move(0, 1)
    ch.move(0, 1)
    assert ch.is_won is True

    ch.compare_with_ai()

    assert len(captured_mazes) == 3
    m_bfs = captured_mazes[0][1]
    m_dfs = captured_mazes[1][1]
    m_astar = captured_mazes[2][1]

    # 1. Three distinct Maze object identities
    assert m_bfs is not m_dfs
    assert m_bfs is not m_astar
    assert m_dfs is not m_astar
    assert len({id(m_bfs), id(m_dfs), id(m_astar)}) == 3

    # None is the original maze
    assert m_bfs is not open_maze_5x5
    assert m_dfs is not open_maze_5x5
    assert m_astar is not open_maze_5x5

    # 2. No shared top-level grid list
    assert m_bfs.grid is not m_dfs.grid
    assert m_bfs.grid is not m_astar.grid
    assert m_dfs.grid is not m_astar.grid
    assert m_bfs.grid is not open_maze_5x5.grid
    assert len({id(m_bfs.grid), id(m_dfs.grid), id(m_astar.grid)}) == 3

    # 3. No shared nested grid rows
    for r in range(open_maze_5x5.rows):
        assert m_bfs.grid[r] is not m_dfs.grid[r]
        assert m_bfs.grid[r] is not m_astar.grid[r]
        assert m_dfs.grid[r] is not m_astar.grid[r]
        assert m_bfs.grid[r] is not open_maze_5x5.grid[r]
        assert m_dfs.grid[r] is not open_maze_5x5.grid[r]
        assert m_astar.grid[r] is not open_maze_5x5.grid[r]

    # 4. Identical initial maze contents
    assert m_bfs.grid == open_maze_5x5.grid
    assert m_dfs.grid == open_maze_5x5.grid
    assert m_astar.grid == open_maze_5x5.grid
    assert m_bfs.start == m_dfs.start == m_astar.start == open_maze_5x5.start
    assert m_bfs.goal == m_dfs.goal == m_astar.goal == open_maze_5x5.goal
    assert m_bfs.rows == m_dfs.rows == m_astar.rows == open_maze_5x5.rows
    assert m_bfs.cols == m_dfs.cols == m_astar.cols == open_maze_5x5.cols


def test_ai_comparison_on_suboptimal_run(open_maze_5x5):
    """Verify AI comparison accurately calculates optimality ratio when human takes detours."""
    ch = HumanChallenge(open_maze_5x5)
    # Detour run: 6 moves instead of optimal 4
    ch.move(0, 1)
    ch.move(0, -1)
    ch.move(0, 1)
    ch.move(1, 0)
    ch.move(1, 0)
    ch.move(0, 1)
    assert ch.is_won is True
    assert ch.move_count == 6

    comparison = ch.compare_with_ai()
    assert comparison["optimal_path_length"] == 4
    assert comparison["human"]["move_count"] == 6
    assert comparison["optimality_ratio"] == pytest.approx((4 / 6) * 100.0, rel=1e-3)


def test_result_structure_completeness(open_maze_5x5, fake_clock):
    """Verify get_result returns all specified metadata fields."""
    ch = HumanChallenge(open_maze_5x5, clock_func=fake_clock)
    ch.move(1, 0)
    fake_clock.advance(2.5)

    res = ch.get_result()
    assert res["status"] == "PLAYING"
    assert res["final_position"] == (2, 1)
    assert res["move_count"] == 1
    assert res["unique_cells_visited"] == 2
    assert res["elapsed_time"] == 2.5
    assert res["human_path_length"] == 1
    assert res["path"] == [(1, 1), (2, 1)]
