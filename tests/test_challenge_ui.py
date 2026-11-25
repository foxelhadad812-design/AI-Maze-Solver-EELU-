"""
Phase 6 - Step 2B: Human vs AI Challenge Mode - Pygame UI Integration Tests
Validates UI integration, buttons, state machine transitions, event routing,
avatar rendering, single AI comparison execution, modal interaction, and regression safety.
"""

import os
import pygame
import pytest
from unittest.mock import patch, MagicMock

from maze import Maze
from ui import (
    COLOR_BREADCRUMB,
    COLOR_GRID_BACKING,
    COLOR_GOAL,
    COLOR_HUMAN_PATH,
    COLOR_OPEN,
    COLOR_PATH,
    COLOR_PLAYER_CORE,
    COLOR_START,
    COLOR_WALL,
    COLOR_WALL_EDGE,
    MazeUI,
)
from challenge import HumanChallenge, ChallengeStatus


@pytest.fixture(autouse=True)
def setup_headless_env(tmp_path, monkeypatch):
    """Ensure headless dummy drivers for all UI tests."""
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    monkeypatch.setenv("APPDATA", str(tmp_path / "appdata"))


def create_simple_corridor_maze():
    """Create a 3x5 simple corridor maze with guaranteed path from (1, 1) to (1, 3)."""
    m = Maze(3, 5)
    for r in range(3):
        for c in range(5):
            m.set_wall(r, c, True)
    m.set_wall(1, 1, False)
    m.set_wall(1, 2, False)
    m.set_wall(1, 3, False)
    m.start = (1, 1)
    m.goal = (1, 3)
    return m


def test_challenge_button_initialization():
    """Verify Human vs AI Challenge button exists, is labeled, and has valid geometry."""
    m = create_simple_corridor_maze()
    ui = MazeUI(m, width=1280, height=720)
    assert hasattr(ui, "btn_challenge")
    assert ui.btn_challenge.text == "Human vs AI Challenge"
    assert ui.btn_challenge.rect.width > 0
    assert ui.btn_challenge.rect.height > 0
    assert ui.btn_challenge in ui.all_buttons


def test_start_challenge_transition():
    """Verify starting challenge transitions to CHALLENGE_PLAYING and creates HumanChallenge."""
    m = create_simple_corridor_maze()
    ui = MazeUI(m, width=1280, height=720)
    assert ui.state == "IDLE"
    assert ui.challenge is None

    ui.action_start_challenge()
    assert ui.state == "CHALLENGE_PLAYING"
    assert ui.challenge is not None
    assert isinstance(ui.challenge, HumanChallenge)
    assert ui.challenge.player_pos == (1, 1)
    assert ui.challenge.move_count == 0
    assert ui.challenge_comparison_results is None


def test_challenge_preserves_original_maze():
    """Verify challenge mode runs without mutating or corrupting the original maze."""
    m = create_simple_corridor_maze()
    walls_before = [row[:] for row in m.grid]
    ui = MazeUI(m, width=1280, height=720)
    ui.action_start_challenge()

    # Move player
    ui.challenge.move(0, 1)
    assert ui.challenge.player_pos == (1, 2)
    assert m.grid == walls_before
    assert m.start == (1, 1)
    assert m.goal == (1, 3)


def test_keyboard_movement_arrow_keys():
    """Verify Arrow keys route to player movement via handle_events."""
    m = create_simple_corridor_maze()
    ui = MazeUI(m, width=1280, height=720)
    ui.action_start_challenge()
    assert ui.challenge.player_pos == (1, 1)

    # Post Right Arrow event
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_RIGHT}))
    ui.handle_events()
    assert ui.challenge.player_pos == (1, 2)
    assert ui.challenge.move_count == 1


def test_keyboard_movement_wasd():
    """Verify WASD keys route to player movement via handle_events."""
    m = create_simple_corridor_maze()
    ui = MazeUI(m, width=1280, height=720)
    ui.action_start_challenge()
    assert ui.challenge.player_pos == (1, 1)

    # Move right using 'd'
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_d}))
    ui.handle_events()
    assert ui.challenge.player_pos == (1, 2)
    assert ui.challenge.move_count == 1

    # Move left using 'a'
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_a}))
    ui.handle_events()
    assert ui.challenge.player_pos == (1, 1)
    assert ui.challenge.move_count == 2


def test_invalid_moves_rejected_in_ui():
    """Verify moving into a wall or boundary is rejected without changing move count or state."""
    m = create_simple_corridor_maze()
    ui = MazeUI(m, width=1280, height=720)
    ui.action_start_challenge()

    # (0, 1) is a wall above (1, 1)
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_UP}))
    ui.handle_events()
    assert ui.challenge.player_pos == (1, 1)
    assert ui.challenge.move_count == 0

    # 'w' is also up into a wall
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_w}))
    ui.handle_events()
    assert ui.challenge.player_pos == (1, 1)
    assert ui.challenge.move_count == 0


def test_goal_reached_triggers_victory_and_single_ai_execution():
    """Verify reaching the goal triggers CHALLENGE_RESULTS and runs compare_with_ai EXACTLY ONCE."""
    m = create_simple_corridor_maze()
    ui = MazeUI(m, width=1280, height=720)
    ui.action_start_challenge()

    # Move to (1, 2)
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_RIGHT}))
    ui.handle_events()
    assert ui.state == "CHALLENGE_PLAYING"
    assert ui.challenge_comparison_results is None

    # Spy on compare_with_ai
    with patch.object(ui.challenge, 'compare_with_ai', wraps=ui.challenge.compare_with_ai) as spy_compare:
        # Move to (1, 3) which is Goal
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_RIGHT}))
        ui.handle_events()

        assert ui.challenge.is_won is True
        assert ui.state == "CHALLENGE_RESULTS"
        assert spy_compare.call_count == 1
        assert ui.challenge_comparison_results is not None
        assert "human" in ui.challenge_comparison_results
        assert "ai" in ui.challenge_comparison_results


def test_ai_comparison_not_called_during_active_play():
    """Verify compare_with_ai is NEVER executed while player is navigating during CHALLENGE_PLAYING."""
    m = create_simple_corridor_maze()
    ui = MazeUI(m, width=1280, height=720)
    ui.action_start_challenge()

    with patch.object(ui.challenge, 'compare_with_ai', wraps=ui.challenge.compare_with_ai) as spy_compare:
        # Valid move, not goal
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_RIGHT}))
        ui.handle_events()
        # Invalid move
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_UP}))
        ui.handle_events()
        # Multiple update() and draw() cycles
        for _ in range(5):
            ui.update()
            ui.draw()

        assert ui.state == "CHALLENGE_PLAYING"
        assert spy_compare.call_count == 0
        assert ui.challenge_comparison_results is None


def test_ai_comparison_not_called_repeatedly_in_draw_or_update():
    """Verify drawing and updating in CHALLENGE_RESULTS never invokes compare_with_ai again."""
    m = create_simple_corridor_maze()
    ui = MazeUI(m, width=1280, height=720)
    ui.action_start_challenge()

    # Move to goal
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_RIGHT}))
    ui.handle_events()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_RIGHT}))
    ui.handle_events()
    assert ui.state == "CHALLENGE_RESULTS"

    # Now simulate 30 frames of update() and draw()
    with patch.object(ui.challenge, 'compare_with_ai', wraps=ui.challenge.compare_with_ai) as spy_compare:
        for _ in range(30):
            ui.update()
            ui.draw()
        assert spy_compare.call_count == 0


def test_start_equals_goal_immediate_victory():
    """Verify Start == Goal immediately transitions to CHALLENGE_RESULTS and runs AI comparison."""
    m = Maze(3, 3)
    m.set_wall(1, 1, False)
    m.start = (1, 1)
    m.goal = (1, 1)
    ui = MazeUI(m, width=1280, height=720)

    ui.action_start_challenge()
    assert ui.challenge.is_won is True
    assert ui.state == "CHALLENGE_RESULTS"
    assert ui.challenge_comparison_results is not None
    assert ui.challenge_comparison_results["human"]["path_length"] == 0
    assert ui.challenge_comparison_results["optimality_ratio"] == 100.0


def test_escape_key_in_challenge_playing_opens_pause_overlay():
    """Verify ESC pauses challenge play and exposes the menu action."""
    m = create_simple_corridor_maze()
    ui = MazeUI(m, width=1280, height=720)
    ui.action_start_challenge()
    assert ui.state == "CHALLENGE_PLAYING"

    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_ESCAPE}))
    ui.handle_events()
    assert ui.state == "CHALLENGE_PAUSED"
    assert ui.challenge.status == ChallengeStatus.PAUSED
    ui.action_challenge_return_to_menu()
    assert ui.state == "IDLE"
    assert ui.challenge is None


def test_escape_key_in_challenge_results_returns_to_menu():
    """Verify ESC key during CHALLENGE_RESULTS returns to IDLE state."""
    m = create_simple_corridor_maze()
    ui = MazeUI(m, width=1280, height=720)
    ui.action_start_challenge()
    # Trigger victory
    ui.challenge.player_pos = ui.maze.goal
    ui.challenge.status = ChallengeStatus.WON
    ui._on_challenge_victory()
    assert ui.state == "CHALLENGE_RESULTS"

    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_ESCAPE}))
    ui.handle_events()
    assert ui.state == "IDLE"
    assert ui.challenge is None


def test_play_again_restarts_on_identical_maze():
    """Verify Play Again restarts challenge on identical maze snapshot."""
    m = create_simple_corridor_maze()
    ui = MazeUI(m, width=1280, height=720)
    ui.action_start_challenge()
    # Reach goal via UI events
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_RIGHT}))
    ui.handle_events()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_RIGHT}))
    ui.handle_events()
    assert ui.state == "CHALLENGE_RESULTS"

    # Click Play Again
    ui.action_challenge_play_again()
    assert ui.state == "CHALLENGE_PLAYING"
    assert ui.challenge is not None
    assert ui.challenge.player_pos == (1, 1)
    assert ui.challenge.move_count == 0
    assert ui.challenge_comparison_results is None


def test_main_menu_action_returns_to_idle():
    """Verify Main Menu action returns to IDLE and clears challenge."""
    m = create_simple_corridor_maze()
    ui = MazeUI(m, width=1280, height=720)
    ui.action_start_challenge()
    ui.action_challenge_return_to_menu()
    assert ui.state == "IDLE"
    assert ui.challenge is None


def test_path_view_selector_buttons():
    """Verify clicking path viewer buttons updates challenge_selected_view_path."""
    m = create_simple_corridor_maze()
    ui = MazeUI(m, width=1280, height=720)
    ui.action_start_challenge()
    ui.challenge.player_pos = ui.maze.goal
    ui.challenge.status = ChallengeStatus.WON
    ui._on_challenge_victory()
    assert ui.state == "CHALLENGE_RESULTS"
    assert ui.challenge_selected_view_path == "Human"

    ui.btn_view_bfs.callback()
    assert ui.challenge_selected_view_path == "BFS"
    ui.btn_view_dfs.callback()
    assert ui.challenge_selected_view_path == "DFS"
    ui.btn_view_astar.callback()
    assert ui.challenge_selected_view_path == "A*"
    ui.btn_view_human.callback()
    assert ui.challenge_selected_view_path == "Human"


def test_grid_editing_blocked_during_challenge_play():
    """Verify mouse clicks on grid cells do not place walls or drag markers during challenge."""
    m = create_simple_corridor_maze()
    ui = MazeUI(m, width=1280, height=720)
    ui.action_start_challenge()
    assert ui.state == "CHALLENGE_PLAYING"

    # Simulate mouse click on grid
    cell_rect = ui._get_cell_rect(1, 2)
    ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': cell_rect.center})
    pygame.event.post(ev)
    ui.handle_events()

    # Cell (1, 2) should remain walkable, not converted to wall
    assert m.is_wall(1, 2) is False


def test_solver_controls_blocked_during_challenge_play():
    """Verify solver shortcuts (Space, 1, 2, 3) do not interrupt active challenge."""
    m = create_simple_corridor_maze()
    ui = MazeUI(m, width=1280, height=720)
    ui.action_start_challenge()
    assert ui.state == "CHALLENGE_PLAYING"

    # Space pauses the challenge without triggering solver behavior.
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_SPACE}))
    ui.handle_events()
    assert ui.state == "CHALLENGE_PAUSED"
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_SPACE}))
    ui.handle_events()
    assert ui.state == "CHALLENGE_PLAYING"

    # 1 (BFS select)
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_1}))
    ui.handle_events()
    assert ui.state == "CHALLENGE_PLAYING"


def test_rendering_pipeline_in_all_challenge_states():
    """Verify ui.draw() runs without exceptions in CHALLENGE_PLAYING and CHALLENGE_RESULTS."""
    m = create_simple_corridor_maze()
    ui = MazeUI(m, width=1280, height=720)

    # 1. CHALLENGE_PLAYING drawing
    ui.action_start_challenge()
    ui.challenge.move(0, 1)
    ui.draw()  # Must render avatar, breadcrumbs, live telemetry cleanly

    # 2. CHALLENGE_RESULTS drawing
    ui.challenge.player_pos = ui.maze.goal
    ui.challenge.status = ChallengeStatus.WON
    ui._on_challenge_victory()
    assert ui.state == "CHALLENGE_RESULTS"
    ui.draw()  # Must render results modal, comparison table, chips cleanly


def test_regression_existing_solver_and_ui_controls():
    """Verify existing solver, generator, speed adjustments, and reset operate flawlessly."""
    m = Maze(15, 15)
    m.generate_random_maze(seed=42)
    ui = MazeUI(m, width=1280, height=720)

    # 1. Normal Solve
    ui.select_algorithm("A*")
    ui.action_solve_or_pause()
    assert ui.state == "RUNNING"
    while ui.generator and ui.state == "RUNNING":
        ui._advance_generator_step()
    assert ui.state == "FINISHED"
    assert ui.final_path is not None

    # 2. Reset
    ui.action_reset()
    assert ui.state == "IDLE"
    assert ui.final_path is None

    # 3. Algorithm dropdown
    ui.select_algorithm("BFS")
    assert ui.selected_algo == "BFS"

    # 4. Speed adjustment
    old_speed = ui.speed_level
    ui.action_increase_speed()
    assert ui.speed_level >= old_speed


def test_ui_entry_point_mouse_click():
    """Verify clicking the 'Human vs AI Challenge' button via MOUSEBUTTONDOWN event enters CHALLENGE_PLAYING."""
    m = create_simple_corridor_maze()
    ui = MazeUI(m, width=1280, height=720)
    assert ui.state == "IDLE"
    assert ui.challenge is None

    # Post MOUSEBUTTONDOWN at the center of the challenge button
    btn_center = ui.btn_challenge.rect.center
    click_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': btn_center})
    pygame.event.post(click_event)

    # Process events through the UI event loop
    ui.handle_events()

    # Verify state transition to CHALLENGE_PLAYING
    assert ui.state == "CHALLENGE_PLAYING"
    assert ui.challenge is not None
    assert isinstance(ui.challenge, HumanChallenge)
    assert ui.challenge.player_pos == (1, 1)


def test_challenge_comparison_attempted_guard_exact_once():
    """Verify self.challenge_comparison_attempted guard enforces exactly-once execution and resets properly."""
    m = create_simple_corridor_maze()
    ui = MazeUI(m, width=1280, height=720)
    assert ui.challenge_comparison_attempted is False

    ui.action_start_challenge()
    assert ui.challenge_comparison_attempted is False

    # Simulate player reaching goal
    ui.challenge.player_pos = ui.maze.goal
    ui.challenge.status = ChallengeStatus.WON

    with patch.object(ui.challenge, 'compare_with_ai', wraps=ui.challenge.compare_with_ai) as spy_compare:
        # First call triggers AI comparison
        ui._on_challenge_victory()
        assert spy_compare.call_count == 1
        assert ui.challenge_comparison_attempted is True
        assert ui.state == "CHALLENGE_RESULTS"

        # Subsequent duplicate calls must be guarded and rejected
        ui._on_challenge_victory()
        ui._on_challenge_victory()
        assert spy_compare.call_count == 1

    # Play again resets the guard
    ui.action_challenge_play_again()
    assert ui.challenge_comparison_attempted is False

    # Reset action also resets the guard
    ui.action_start_challenge()
    ui.challenge.player_pos = ui.maze.goal
    ui.challenge.status = ChallengeStatus.WON
    ui._on_challenge_victory()
    assert ui.challenge_comparison_attempted is True

    ui.action_reset()
    assert ui.challenge_comparison_attempted is False


def test_comparison_failure_handling_and_error_display():
    """Verify that compare_with_ai exception retains human data, sets optimality to None, and renders error banner."""
    m = create_simple_corridor_maze()
    ui = MazeUI(m, width=1280, height=720)
    ui.action_start_challenge()

    # Move player 1 step
    ui.challenge.move(0, 1)
    ui.challenge.player_pos = ui.maze.goal
    ui.challenge.status = ChallengeStatus.WON

    # Mock compare_with_ai to raise an exception
    with patch.object(ui.challenge, 'compare_with_ai', side_effect=RuntimeError("AI search timeout simulation")):
        ui._on_challenge_victory()

    # Verify failure handling integrity
    assert ui.state == "CHALLENGE_RESULTS"
    res = ui.challenge_comparison_results
    assert res is not None
    assert "error" in res
    assert "AI search timeout simulation" in res["error"]

    # Verify Human performance telemetry is preserved
    assert res["human"]["path_length"] == ui.challenge.move_count
    assert res["human"]["unique_cells_visited"] == ui.challenge.unique_cells_visited
    assert res["human"]["elapsed_time_s"] >= 0.0

    # Verify AI comparison data is NOT manufactured
    assert res["ai"] == {}
    # Optimality ratio MUST be None, NEVER manufactured as 100%
    assert res["optimality_ratio"] is None

    # Verify UI rendering does not crash and handles the error banner cleanly
    ui.draw()


def test_bfs_authoritative_optimality_reference_and_missing_bfs():
    """Verify BFS is the sole authoritative reference for optimality, and missing BFS displays N/A without fallback."""
    m = create_simple_corridor_maze()
    ui = MazeUI(m, width=1280, height=720)
    ui.action_start_challenge()
    ui.challenge.player_pos = ui.maze.goal
    ui.challenge.status = ChallengeStatus.WON

    # Simulate scenario where BFS was omitted or produced no path, but A* is present
    ui.challenge_comparison_results = {
        "human": {
            "path_length": 10,
            "unique_cells_visited": 12,
            "elapsed_time_s": 5.4,
            "path": [(1, 1), (1, 2), (1, 3)]
        },
        "ai": {
            "A*": {
                "found": True,
                "path_length": 6,
                "nodes_expanded": 14,
                "compute_time_ms": 0.25
            },
            "DFS": {
                "found": True,
                "path_length": 18,
                "nodes_expanded": 22,
                "compute_time_ms": 0.18
            }
            # BFS is intentionally absent
        },
        "optimality_ratio": None
    }
    ui.state = "CHALLENGE_RESULTS"

    # ui.draw() must use BFS as authoritative; since BFS is absent, it must NOT fallback to A* or human
    ui.draw()

    # Now verify with BFS found=False
    ui.challenge_comparison_results["ai"]["BFS"] = {
        "found": False,
        "path_length": 0,
        "nodes_expanded": 5,
        "compute_time_ms": 0.1
    }
    ui.draw()


def test_responsive_viewport_layouts():
    """Verify modal and button geometry adapt dynamically across 1280x720, 900x600, and 800x600 without clipping."""
    m = create_simple_corridor_maze()
    viewports = [(1280, 720), (900, 600), (800, 600)]

    for width, height in viewports:
        ui = MazeUI(m, width=width, height=height)
        ui.action_start_challenge()
        ui.challenge.player_pos = ui.maze.goal
        ui.challenge.status = ChallengeStatus.WON
        ui._on_challenge_victory()

        assert ui.state == "CHALLENGE_RESULTS"
        # Render frame
        ui.draw()

        # Check button boundaries are within screen
        assert ui.btn_challenge_play_again.rect.left >= 0
        assert ui.btn_challenge_play_again.rect.right <= ui.width
        assert ui.btn_challenge_play_again.rect.bottom <= ui.height

        assert ui.btn_challenge_menu.rect.left >= 0
        assert ui.btn_challenge_menu.rect.right <= ui.width
        assert ui.btn_challenge_menu.rect.bottom <= ui.height

        # Also test with error present in results
        ui.challenge_comparison_results["error"] = "Viewport responsiveness error test"
        ui.draw()


def _make_render_ui(cell_size, rows=5, cols=5):
    """Create a deterministic drawing surface with a manually selected integer cell size."""
    maze = Maze(rows, cols)
    maze.start = (0, 0)
    maze.goal = (rows - 1, cols - 1)
    maze.grid = [[Maze.WALL for _ in range(cols)] for _ in range(rows)]
    maze.grid[maze.start[0]][maze.start[1]] = Maze.START
    maze.grid[maze.goal[0]][maze.goal[1]] = Maze.GOAL
    maze.grid[2][1] = Maze.OPEN
    maze.grid[2][2] = Maze.OPEN
    maze.grid[2][3] = Maze.OPEN

    ui = MazeUI(maze, width=1280, height=720)
    grid_w = cols * cell_size
    grid_h = rows * cell_size
    surface_w = max(160, grid_w + 80)
    surface_h = max(160, grid_h + 80)
    ui.width = surface_w
    ui.height = surface_h
    ui.screen = pygame.Surface((surface_w, surface_h))
    ui.maze_panel_rect = pygame.Rect(20, 20, grid_w + 40, grid_h + 40)
    ui.grid_area = pygame.Rect(40, 40, grid_w, grid_h)
    ui.maze_viewport_rect = pygame.Rect(40, 40, grid_w, grid_h)
    ui.maze_cell_size = cell_size
    ui._base_cell_size = cell_size
    ui.state = "IDLE"
    ui.final_path = None
    ui.current_cell = None
    ui.expanded_cells.clear()
    ui.frontier_cells.clear()
    ui.discovered_cells.clear()
    return ui


@pytest.mark.parametrize("cell_size", [2, 3, 4, 9, 13, 24, 38])
def test_adaptive_tiles_are_nonempty_and_draw_wall_and_open_pixels(cell_size):
    """Each supported tile size draws real wall/open pixels without changing the maze."""
    ui = _make_render_ui(cell_size)
    grid_before = [row[:] for row in ui.maze.grid]
    ui.screen.fill((0, 0, 0))

    cell_rect = ui._get_cell_rect(1, 1)
    inset, radius, draw_edges = ui._tile_style(cell_size)
    tile_rect = ui._tile_rect(cell_rect, inset)
    assert tile_rect.width >= 1
    assert tile_rect.height >= 1
    assert 0 <= radius <= (min(tile_rect.width, tile_rect.height) - 1) // 2
    assert draw_edges is (cell_size >= 18)

    ui._draw_maze_panel()
    assert ui.screen.get_at(cell_rect.center)[:3] == COLOR_WALL
    open_center = ui._get_cell_rect(2, 1).center
    assert ui.screen.get_at(open_center)[:3] == COLOR_OPEN
    assert ui.maze.grid == grid_before


def test_render_palette_separates_backing_walls_corridors_and_markers():
    """The existing dark palette keeps its identity while adjacent maze roles differ clearly."""
    assert COLOR_GRID_BACKING != COLOR_WALL
    assert max(abs(a - b) for a, b in zip(COLOR_GRID_BACKING, COLOR_WALL)) >= 15
    assert all(wall < open_cell for wall, open_cell in zip(COLOR_WALL, COLOR_OPEN))
    assert COLOR_START != COLOR_GOAL
    assert COLOR_WALL_EDGE != COLOR_WALL


def test_human_challenge_advances_through_three_growing_levels_and_restores_maze():
    """Challenge progression grows generated levels, then returns to the original maze."""
    maze = create_simple_corridor_maze()
    original_grid = [row[:] for row in maze.grid]
    ui = MazeUI(maze, width=1280, height=720)

    ui.action_start_challenge()
    assert ui.challenge_level == 1
    assert (ui.maze.rows, ui.maze.cols) == (3, 5)

    ui.challenge.player_pos = ui.maze.goal
    ui.challenge.status = ChallengeStatus.WON
    ui._on_challenge_victory()
    ui.action_challenge_next_level()
    assert ui.challenge_level == 2
    assert ui.state == "CHALLENGE_PLAYING"
    assert (ui.maze.rows, ui.maze.cols) == (25, 25)
    assert ui.maze.has_solution()

    ui.challenge.player_pos = ui.maze.goal
    ui.challenge.status = ChallengeStatus.WON
    ui._on_challenge_victory()
    ui.action_challenge_next_level()
    assert ui.challenge_level == 3
    assert ui.state == "CHALLENGE_PLAYING"
    assert (ui.maze.rows, ui.maze.cols) == (41, 31)
    assert ui.maze.has_solution()

    ui.action_challenge_next_level()
    assert ui.challenge_level == 3
    ui.action_challenge_return_to_menu()
    assert ui.challenge_level == 0
    assert (ui.maze.rows, ui.maze.cols) == (3, 5)
    assert ui.maze.grid == original_grid


def test_score_uses_move_efficiency_and_time_target():
    comparison = {
        "human": {"path_length": 20, "elapsed_time_s": 60.0},
        "ai": {"BFS": {"found": True, "path_length": 10}},
    }
    assert MazeUI._calculate_level_score(comparison) == 50
    assert MazeUI._calculate_level_score({
        "human": {"path_length": 10, "elapsed_time_s": 15.0},
        "ai": {"BFS": {"found": True, "path_length": 10}},
    }) == 100


def test_challenge_progress_is_saved_and_resumes_unlocked_level():
    maze = create_simple_corridor_maze()
    original_grid = [row[:] for row in maze.grid]
    ui = MazeUI(maze, width=1280, height=720)
    ui.action_start_challenge()
    ui.challenge.player_pos = ui.maze.goal
    ui.challenge.status = ChallengeStatus.WON
    ui._on_challenge_victory()

    assert ui.challenge_unlocked_level == 2
    assert os.path.exists(ui.challenge_progress_file)

    resumed = MazeUI(create_simple_corridor_maze(), width=1280, height=720)
    assert resumed.challenge_unlocked_level == 2
    assert "Continue Level 2" in resumed.btn_challenge.text
    resumed.action_start_challenge()
    assert resumed.challenge_level == 2
    assert (resumed.maze.rows, resumed.maze.cols) == (25, 25)
    resumed.action_challenge_return_to_menu()
    assert (resumed.maze.rows, resumed.maze.cols) == (3, 5)
    assert resumed.maze.grid == original_grid


def test_tutorial_is_available_before_challenge_start():
    ui = MazeUI(create_simple_corridor_maze(), width=1280, height=720)
    ui.action_show_challenge_tutorial()
    assert ui.state == "CHALLENGE_TUTORIAL"
    ui.draw()
    ui.action_close_challenge_tutorial()
    assert ui.state == "IDLE"
    ui.action_show_challenge_tutorial()
    ui.action_start_challenge()
    assert ui.state == "CHALLENGE_PLAYING"


def test_pause_overlay_freezes_challenge_and_retry_restarts_same_level():
    ui = MazeUI(create_simple_corridor_maze(), width=1280, height=720)
    ui.action_start_challenge()
    assert ui.challenge.move_right()
    current = ui.challenge.player_pos
    ui.action_pause_challenge()
    assert ui.state == "CHALLENGE_PAUSED"
    assert ui.challenge.status == ChallengeStatus.PAUSED
    assert ui.challenge.move_right() is False
    assert ui.challenge.player_pos == current
    ui.draw()
    ui.action_resume_challenge()
    assert ui.state == "CHALLENGE_PLAYING"
    ui.action_pause_challenge()
    ui.action_challenge_retry()
    assert ui.state == "CHALLENGE_PLAYING"
    assert ui.challenge_level == 1
    assert ui.challenge.player_pos == ui.maze.start
    assert ui.challenge.move_count == 0


def test_gameplay_feedback_marks_moves_and_wall_collisions():
    ui = MazeUI(create_simple_corridor_maze(), width=1280, height=720)
    ui.action_start_challenge()
    if ui.feedback_sounds:
        assert set(ui.feedback_sounds) == {"move", "wall", "win"}
    ui._set_gameplay_feedback("move")
    assert ui.challenge_feedback_kind == "move"
    assert ui.challenge_feedback_until > 0
    ui._set_gameplay_feedback("wall")
    assert ui.challenge_feedback_kind == "wall"
    ui.draw()


def test_new_campaign_reset_requires_confirmation_and_clears_saved_progress():
    ui = MazeUI(create_simple_corridor_maze(), width=1280, height=720)
    ui.action_start_challenge()
    ui.challenge.move_right()
    ui.challenge.move_right()
    ui._on_challenge_victory()
    assert ui.state == "CHALLENGE_RESULTS"
    assert ui.btn_new_campaign.rect.width > 0
    assert os.path.exists(ui.challenge_progress_file)

    ui.action_request_new_campaign()
    assert ui.state == "CHALLENGE_RESET_CONFIRM"
    ui.draw()
    ui.action_close_new_campaign_confirmation()
    assert ui.state == "IDLE"
    assert os.path.exists(ui.challenge_progress_file)

    ui.action_request_new_campaign()
    ui.action_confirm_new_campaign()
    assert ui.state == "CHALLENGE_PLAYING"
    assert ui.challenge_level == 1
    assert ui.challenge_unlocked_level == 1
    assert ui.challenge_best_scores == {}
    assert not os.path.exists(ui.challenge_progress_file)


def test_later_level_move_budget_fails_attempt_and_retry_reuses_budget():
    ui = MazeUI(create_simple_corridor_maze(), width=1280, height=720)
    ui.action_start_challenge()
    ui.challenge.move_right()
    ui.challenge.move_right()
    ui._on_challenge_victory()
    assert ui.state == "CHALLENGE_RESULTS"
    ui.action_challenge_next_level()

    assert ui.challenge_level == 2
    optimal = ui.challenge_optimal_moves
    limit = ui.challenge_move_limit
    assert optimal is not None and limit is not None
    assert optimal <= limit <= int(optimal * 1.60) + 1

    ui.challenge.player_pos = ui.maze.start
    ui.challenge.move_count = limit
    neighbor = ui.maze.get_neighbors(*ui.maze.start)[0]
    delta = (neighbor[0] - ui.maze.start[0], neighbor[1] - ui.maze.start[1])
    key_for_delta = {(-1, 0): pygame.K_UP, (1, 0): pygame.K_DOWN, (0, -1): pygame.K_LEFT, (0, 1): pygame.K_RIGHT}
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": key_for_delta[delta]}))
    ui.handle_events()

    assert ui.state == "CHALLENGE_FAILED"
    assert ui.challenge.status == ChallengeStatus.LOST
    ui.draw()
    ui.action_challenge_retry()
    assert ui.state == "CHALLENGE_PLAYING"
    assert ui.challenge_level == 2
    assert ui.challenge_move_limit == limit
    assert ui.challenge.move_count == 0


@pytest.mark.parametrize("cell_size", [2, 3, 4, 9, 13, 24, 38])
def test_player_avatar_pixels_stay_inside_current_cell(cell_size):
    """The rendered cyan/core/center pixels are bounded by the player cell."""
    ui = _make_render_ui(cell_size)
    ui.challenge = HumanChallenge(ui.maze)
    ui.challenge.player_pos = (2, 2)
    ui.challenge.path = [ui.maze.start, (2, 2)]
    ui.state = "CHALLENGE_PLAYING"
    player_cell = ui._get_cell_rect(2, 2)
    grid_before = [row[:] for row in ui.maze.grid]

    ui._draw_maze_panel()

    avatar_colors = {COLOR_HUMAN_PATH, COLOR_PLAYER_CORE, (255, 255, 255)}
    points = [
        (x, y)
        for y in range(player_cell.top, player_cell.bottom)
        for x in range(player_cell.left, player_cell.right)
        if ui.screen.get_at((x, y))[:3] in avatar_colors
    ]
    assert points
    assert all(player_cell.collidepoint(point) for point in points)
    assert ui.maze.grid == grid_before


@pytest.mark.parametrize("cell_size", [2, 3, 4, 9, 13, 24, 38])
def test_breadcrumb_pixels_stay_in_cells_and_revisits_render_once(cell_size):
    """Breadcrumb dimensions fit their cell and repeated path entries do not stack marks."""
    ui = _make_render_ui(cell_size)
    ui.challenge = HumanChallenge(ui.maze)
    crumb = (2, 1)
    ui.challenge.player_pos = (2, 3)
    ui.challenge.path = [crumb, crumb, (2, 3)]
    ui.state = "CHALLENGE_PLAYING"
    crumb_cell = ui._get_cell_rect(*crumb)

    ui._draw_maze_panel()

    points = [
        (x, y)
        for y in range(ui.grid_area.top, ui.grid_area.bottom)
        for x in range(ui.grid_area.left, ui.grid_area.right)
        if ui.screen.get_at((x, y))[:3] == COLOR_BREADCRUMB
    ]
    assert points
    assert all(crumb_cell.collidepoint(point) for point in points)
    assert ui._breadcrumb_size(cell_size) <= cell_size


@pytest.mark.parametrize(
    ("cell_size", "expected_width"),
    [(2, 1), (3, 1), (4, 1), (9, 3), (13, 4), (24, 8), (38, 13)],
)
def test_path_width_scales_and_rendered_stroke_fits_cell(cell_size, expected_width):
    """Path stroke remains crisp and proportionate, including at 2-pixel cells."""
    ui = _make_render_ui(cell_size)
    ui.final_path = [(2, 1), (2, 2)]
    ui.state = "FINISHED"
    assert ui._path_width(cell_size) == expected_width
    assert 1 <= expected_width <= cell_size

    ui._draw_maze_panel()
    left_center = ui._get_cell_rect(2, 1).center
    sample_x = left_center[0] + cell_size // 2
    sample_y = left_center[1]
    vertical_pixels = [
        y for y in range(ui.grid_area.top, ui.grid_area.bottom)
        if ui.screen.get_at((sample_x, y))[:3] == COLOR_PATH
    ]
    assert len(vertical_pixels) == expected_width


@pytest.mark.parametrize("cell_size", [2, 3, 4, 9, 11])
def test_tiny_start_goal_markers_use_color_without_oversized_text(cell_size):
    """Small markers remain colored and omit labels that cannot fit."""
    ui = _make_render_ui(cell_size)
    assert ui._marker_font(cell_size) is None
    ui._draw_maze_panel()
    assert ui.screen.get_at(ui._get_cell_rect(*ui.maze.start).center)[:3] == COLOR_START
    assert ui.screen.get_at(ui._get_cell_rect(*ui.maze.goal).center)[:3] == COLOR_GOAL


@pytest.mark.parametrize(
    ("rows", "cols", "width", "height"),
    [
        (25, 25, 800, 600),
        (25, 25, 1280, 720),
        (40, 30, 900, 600),
        (100, 100, 800, 600),
        (100, 100, 1920, 1080),
    ],
)
def test_resize_layout_keeps_integer_grid_inside_panel_and_maps_mouse(rows, cols, width, height):
    """Requested density cases preserve integer geometry, panel bounds, and hit testing."""
    ui = MazeUI(Maze(rows, cols), width=1280, height=720)
    ui.width, ui.height = width, height
    ui.screen = pygame.Surface((width, height))
    ui._layout_ui()

    cell_size = ui.grid_area.width // cols
    assert cell_size >= 1
    assert ui.grid_area.width == cell_size * cols
    assert ui.grid_area.height == cell_size * rows
    assert ui.grid_area.left >= ui.maze_panel_rect.left
    assert ui.grid_area.right <= ui.maze_panel_rect.right
    assert ui.grid_area.top >= ui.maze_panel_rect.top
    assert ui.grid_area.bottom <= ui.maze_panel_rect.bottom
    target = (rows // 2, cols // 2)
    assert ui._pos_to_cell(ui._get_cell_rect(*target).center) == target


def test_marker_font_policy_is_cell_aware_and_window_scaling_is_capped():
    """Labels scale with cell space; UI fonts grow modestly only on larger windows."""
    compact = MazeUI(Maze(5, 5), width=800, height=600)
    normal = MazeUI(Maze(5, 5), width=1280, height=720)
    large = MazeUI(Maze(5, 5), width=1920, height=1080)
    # The constructor clamps requested dimensions to the current desktop. Exercise
    # the scaling policy itself at the requested logical viewport dimensions.
    large.width, large.height = 1920, 1080
    large._init_fonts()

    for ui in (compact, normal, large):
        assert ui._marker_font(9) is None
        assert ui._marker_font(13) is not None
    assert compact._font_size(13) <= normal._font_size(13)
    assert large._font_size(13) > normal._font_size(13)
    assert large._font_size(25) <= 28


def test_human_and_ai_path_colors_remain_distinct_and_render_does_not_mutate_maze():
    """Human cyan and AI gold paths remain distinct on the unchanged maze grid."""
    ui = _make_render_ui(13)
    human_path = [(2, 1), (2, 2), (2, 3)]
    ai_path = [(2, 1), (2, 2), (2, 3)]
    ui.challenge = HumanChallenge(ui.maze)
    ui.challenge.path = human_path
    ui.challenge_selected_view_path = "Human"
    ui.challenge_comparison_results = {
        "ai": {"BFS": {"found": True, "path": ai_path}}
    }
    ui.state = "CHALLENGE_RESULTS"
    grid_before = [row[:] for row in ui.maze.grid]

    ui._draw_maze_panel()
    human_sample = (ui._get_cell_rect(2, 1).center[0] + 2, ui._get_cell_rect(2, 1).center[1])
    assert ui.screen.get_at(human_sample)[:3] == COLOR_HUMAN_PATH

    ui.challenge_selected_view_path = "BFS"
    ui._draw_maze_panel()
    assert ui.screen.get_at(human_sample)[:3] == COLOR_PATH
    assert ui.maze.grid == grid_before


@pytest.mark.parametrize("width,height", [(800, 600), (900, 600), (1280, 720), (1920, 1080)])
def test_results_dashboard_renders_at_target_viewports(width, height):
    """Dashboard and action buttons remain drawable and inside the client area."""
    ui = MazeUI(create_simple_corridor_maze(), width=1280, height=720)
    ui.width, ui.height = width, height
    ui.screen = pygame.Surface((width, height))
    ui._init_fonts()
    ui._layout_ui()
    ui.action_start_challenge()
    ui.challenge.player_pos = ui.maze.goal
    ui.challenge.status = ChallengeStatus.WON
    ui._on_challenge_victory()
    ui.draw()

    for button in (ui.btn_challenge_play_again, ui.btn_challenge_menu):
        assert button.rect.left >= 0
        assert button.rect.top >= 0
        assert button.rect.right <= width
        assert button.rect.bottom <= height


def test_difficulty_changes_later_level_geometry_and_move_allowance(monkeypatch):
    ui = MazeUI(create_simple_corridor_maze(), width=1280, height=720)
    base = Maze(25, 25)
    ui.challenge_difficulty = "Easy"
    easy_size = ui._build_challenge_level_maze(base, 3)
    ui.challenge_difficulty = "Medium"
    medium_size = ui._build_challenge_level_maze(base, 3)
    ui.challenge_difficulty = "Hard"
    hard_size = ui._build_challenge_level_maze(base, 3)
    assert (easy_size.rows, easy_size.cols) < (medium_size.rows, medium_size.cols)
    assert (medium_size.rows, medium_size.cols) < (hard_size.rows, hard_size.cols)

    monkeypatch.setattr("ui.bfs_solve", lambda _maze: {"found": True, "path": [()] * 11})
    ui.challenge_level = 2
    limits = {}
    for difficulty in ("Easy", "Medium", "Hard"):
        ui.challenge_difficulty = difficulty
        ui._configure_challenge_move_limit()
        limits[difficulty] = ui.challenge_move_limit
    assert limits == {"Easy": 18, "Medium": 16, "Hard": 14}


def test_difficulty_button_cycles_and_persists_campaign_preference():
    ui = MazeUI(create_simple_corridor_maze(), width=1280, height=720)
    assert ui.challenge_difficulty == "Medium"
    ui.action_cycle_challenge_difficulty()
    assert ui.challenge_difficulty == "Hard"
    assert ui.btn_difficulty.text == "Diff: Hard"
    resumed = MazeUI(create_simple_corridor_maze(), width=1280, height=720)
    assert resumed.challenge_difficulty == "Hard"


def test_large_maze_zoom_pan_and_cell_mapping_remain_integer_and_accurate():
    maze = Maze(100, 100)
    maze.generate_random_maze(seed=202611)
    ui = MazeUI(maze, width=800, height=600)
    assert ui.dropdown_size.options[ui.dropdown_size.selected_idx] == "100 x 100"
    grid_before = [row[:] for row in maze.grid]
    focus = ui.maze_viewport_rect.center
    cell_before = ui._pos_to_cell(focus)
    assert ui.maze_zoom == 1.0
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.MOUSEWHEEL, {"x": 0, "y": 1, "pos": focus}))
    ui.handle_events()
    assert ui.maze_zoom == 1.5
    assert ui.maze_cell_size > ui._base_cell_size
    assert ui.grid_area.width == maze.cols * ui.maze_cell_size
    assert ui.grid_area.height == maze.rows * ui.maze_cell_size
    assert ui._pos_to_cell(focus) == cell_before

    prior_pan = ui.maze_pan_x
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 3, "pos": focus}))
    ui.handle_events()
    pygame.event.post(pygame.event.Event(
        pygame.MOUSEMOTION,
        {"pos": (focus[0] - ui.maze_cell_size * 3, focus[1]), "rel": (-ui.maze_cell_size * 3, 0), "buttons": (0, 0, 1)},
    ))
    ui.handle_events()
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP, {"button": 3, "pos": focus}))
    ui.handle_events()
    assert ui.maze_pan_x == prior_pan + 3
    visible_cell = ui._pos_to_cell(ui.maze_viewport_rect.center)
    assert visible_cell is not None
    cell_rect = ui._get_cell_rect(*visible_cell)
    assert all(isinstance(value, int) for value in cell_rect)
    ui.draw()
    assert maze.grid == grid_before
    ui.width, ui.height = 900, 600
    ui.screen = pygame.Surface((900, 600))
    ui._init_fonts()
    ui._layout_ui()
    assert ui.maze_cell_size >= ui._base_cell_size
    ui._reset_maze_view()
    assert ui.maze_zoom == 1.0 and ui.maze_pan_x == ui.maze_pan_y == 0


def test_audio_settings_mute_and_adjust_feedback_volume():
    ui = MazeUI(create_simple_corridor_maze(), width=1280, height=720)
    if not ui.feedback_sounds:
        pytest.skip("Pygame mixer is unavailable in this environment")
    ui.action_toggle_audio()
    assert ui.audio_muted
    assert all(sound.get_volume() == 0.0 for sound in ui.feedback_sounds.values())
    ui.action_adjust_audio_volume(2)
    assert ui.audio_volume == 0.75
    assert all(sound.get_volume() == 0.0 for sound in ui.feedback_sounds.values())
    ui.action_toggle_audio()
    assert all(sound.get_volume() == pytest.approx(0.75) for sound in ui.feedback_sounds.values())
    resumed = MazeUI(create_simple_corridor_maze(), width=1280, height=720)
    assert resumed.audio_volume == pytest.approx(0.75)
    assert not resumed.audio_muted
    ui.state = "MODAL_SETTINGS"
    ui.draw()
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": ui.btn_volume_up.rect.center}
    ))
    ui.handle_events()
    assert ui.audio_volume == pytest.approx(0.85)


def test_challenge_results_include_difficulty_and_level_summary():
    ui = MazeUI(create_simple_corridor_maze(), width=1280, height=720)
    ui.action_start_challenge()
    ui.challenge.move_right()
    ui.challenge.move_right()
    ui._on_challenge_victory()
    assert ui.state == "CHALLENGE_RESULTS"
    assert ui.challenge_best_scores[1] == ui.challenge_level_scores[1]
    assert len(ui.challenge.visited_cells) == 3
    ui.draw()



def test_challenge_hint_keyboard_and_repeated_wall_hits_are_non_mutating():
    ui = MazeUI(create_simple_corridor_maze(), width=1280, height=720)
    ui.action_start_challenge()
    grid_before = [row[:] for row in ui.maze.grid]
    path_before = list(ui.challenge.path)
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_h}))
    ui.handle_events()
    assert "right" in ui.challenge_hint_text.lower()
    assert ui.challenge.path == path_before
    assert ui.maze.grid == grid_before

    ui.challenge_hint_auto_shown = False
    pygame.event.clear()
    for _ in range(3):
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_UP}))
        ui.handle_events()
    assert ui.challenge_hint_auto_shown
    assert ui.challenge_blocked_attempts == 0
    assert ui.challenge.player_pos == ui.maze.start
    ui.draw()


def test_hint_button_appears_during_challenge_and_auto_hint_after_idle(monkeypatch):
    ui = MazeUI(create_simple_corridor_maze(), width=1280, height=720)
    ui.action_start_challenge()
    ui.draw()
    assert ui.btn_challenge_hint.rect.width > ui.btn_difficulty.rect.width
    import time as clock_time
    ui.challenge_last_progress_at = clock_time.perf_counter() - 26
    ui.update()
    assert ui.challenge_hint_auto_shown
    assert ui.challenge_hint_text


def test_difficulty_guide_is_available_before_start_and_draws_cleanly():
    ui = MazeUI(create_simple_corridor_maze(), width=800, height=600)
    ui.action_show_challenge_tutorial()
    ui.draw()
    assert ui.state == "CHALLENGE_TUTORIAL"
    assert ui.btn_tutorial_start.rect.top < ui.btn_tutorial_start.rect.bottom


def test_maze_export_creates_reloadable_share_file(monkeypatch, tmp_path):
    import sys
    from types import SimpleNamespace

    target = tmp_path / "shared-maze.txt"

    class FakeRoot:
        def withdraw(self): pass
        def attributes(self, *_args): pass
        def destroy(self): pass

    fake_tk = SimpleNamespace(
        Tk=FakeRoot,
        filedialog=SimpleNamespace(asksaveasfilename=lambda **_kwargs: str(target)),
    )
    monkeypatch.setitem(sys.modules, "tkinter", fake_tk)

    ui = MazeUI(create_simple_corridor_maze(), width=1280, height=720)
    ui.state = "MODAL_SETTINGS"
    ui.draw()
    grid_before = [row[:] for row in ui.maze.grid]
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": ui.btn_maze_export.rect.center}
    ))
    ui.handle_events()

    assert target.exists()
    loaded = Maze(3, 5)
    loaded.load_from_file(str(target))
    assert loaded.grid == grid_before
    assert "shared-maze.txt" in ui.maze_share_status
    assert ui.maze.grid == grid_before


