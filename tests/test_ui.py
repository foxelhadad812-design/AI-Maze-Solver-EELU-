"""
Tests for Pygame User Interface logic and interactions.
Uses SDL_VIDEODRIVER='dummy' to verify headless execution.
"""

import os
import sys

# Use dummy video driver for headless CI/testing
os.environ["SDL_VIDEODRIVER"] = "dummy"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pygame
from maze import Maze
from ui import MazeUI


def test_ui_initialization_and_actions():
    """Verify that MazeUI initializes properly and responds to actions."""
    m = Maze(15, 15)
    m.generate_random_maze(seed=42)
    
    ui = MazeUI(m, width=800, height=600)
    assert ui.state == "IDLE"
    assert ui.selected_algo == "A*"
    
    # Test selecting algorithm
    ui.select_algorithm("BFS")
    assert ui.selected_algo == "BFS"
    assert "BFS" in ui.algo_dropdown.selected_value
    
    ui.select_algorithm("DFS")
    assert ui.selected_algo == "DFS"
    assert "DFS" in ui.algo_dropdown.selected_value
    
    # Test speed adjustment
    initial_speed = ui.speed_level
    ui.action_increase_speed()
    assert ui.speed_level >= initial_speed
    ui.action_decrease_speed()
    
    # Test Run and Step
    ui.action_step()
    assert ui.state == "PAUSED"
    assert ui.generator is not None
    
    # Test Pause / Resume
    ui.action_pause_resume()
    assert ui.state == "RUNNING"
    
    # Test Update loop
    for _ in range(50):
        ui.update()
        if ui.state in ["FINISHED", "NO_PATH"]:
            break
            
    # Test Draw call
    ui.draw()
    
    # Test Reset
    ui.action_reset()
    assert ui.state == "IDLE"
    assert len(ui.visited_cells) == 0
    assert ui.final_path is None
    
    # Test Comparison Mode
    ui.action_compare_algorithms()
    assert ui.state == "COMPARING"
    assert ui.compare_results is not None
    assert len(ui.compare_results) == 3
    ui.draw()
    
    ui.close_comparison()
    assert ui.state == "IDLE"
    assert ui.compare_results is None
    
    # Test Generate Maze
    ui.action_generate_maze()
    assert ui.maze.has_solution() is True
    
    # Test Load Sample Maze
    ui.action_load_sample_maze()
    assert ui.maze.has_solution() is True
    
    pygame.quit()


def test_regression_no_duplicate_search_execution(monkeypatch):
    """
    Regression Test 1: Verify action_solve_or_pause executes the search exactly ONCE
    via the generator, without calling synchronous solve on a clone.
    """
    import algorithms.astar as astar_mod
    import algorithms.bfs as bfs_mod
    import algorithms.dfs as dfs_mod

    solve_called = {"astar": 0, "bfs": 0, "dfs": 0}

    def fake_astar_solve(maze):
        solve_called["astar"] += 1
        raise AssertionError("astar_solve should NOT be called during UI solve!")

    def fake_bfs_solve(maze):
        solve_called["bfs"] += 1
        raise AssertionError("bfs_solve should NOT be called during UI solve!")

    def fake_dfs_solve(maze):
        solve_called["dfs"] += 1
        raise AssertionError("dfs_solve should NOT be called during UI solve!")

    monkeypatch.setattr(astar_mod, "astar_solve", fake_astar_solve)
    monkeypatch.setattr(bfs_mod, "bfs_solve", fake_bfs_solve)
    monkeypatch.setattr(dfs_mod, "dfs_solve", fake_dfs_solve)

    m = Maze(15, 15)
    m.generate_random_maze(seed=42)
    ui = MazeUI(m, width=800, height=600)
    ui.select_algorithm("A*")

    # Animated solve
    ui.animate_search = True
    ui.action_solve_or_pause()
    assert ui.state == "RUNNING"
    assert solve_called["astar"] == 0

    while ui.state == "RUNNING":
        ui.update()

    assert ui.state == "FINISHED"
    assert ui.final_path is not None
    assert ui.nodes_expanded > 0
    assert ui.path_length > 0
    assert ui.search_compute_time > 0
    assert ui.execution_time_ms > 0
    assert solve_called["astar"] == 0

    # Instant solve (animate_search = False)
    ui.action_reset()
    ui.animate_search = False
    ui.action_solve_or_pause()
    # Must immediately be finished without calling astar_solve
    assert ui.state == "FINISHED"
    assert ui.final_path is not None
    assert ui.nodes_expanded > 0
    assert solve_called["astar"] == 0

    pygame.quit()


def test_regression_animate_search_toggle_while_running():
    """
    Regression Test 2: Verify that unchecking Animate Search while RUNNING
    safely finishes the search immediately instead of getting stuck in RUNNING.
    """
    m = Maze(15, 15)
    m.generate_random_maze(seed=42)
    ui = MazeUI(m, width=800, height=600)
    ui.select_algorithm("A*")
    ui.animate_search = True
    ui.speed_level = 1

    # Start search
    ui.action_solve_or_pause()
    assert ui.state == "RUNNING"
    ui.update()
    assert ui.state == "RUNNING"

    # 1. Test unchecking via checkbox on_toggle callback
    ui._on_toggle_animate(False)
    assert ui.state == "FINISHED"
    assert ui.final_path is not None
    assert ui.path_length > 0
    assert ui.generator is None

    # 2. Test programmatic attribute toggle and update() loop
    ui.action_reset()
    ui.animate_search = True
    ui.action_solve_or_pause()
    assert ui.state == "RUNNING"
    ui.update()
    assert ui.state == "RUNNING"

    # Set animate_search = False directly
    ui.animate_search = False
    ui.update()
    assert ui.state == "FINISHED"
    assert ui.final_path is not None
    assert ui.generator is None

    pygame.quit()


def test_regression_shortcuts_and_modal_file_management(monkeypatch):
    """
    Regression Test 3: Verify that keyboard shortcuts L, M and the Settings modal
    file management buttons cleanly trigger file loading and sample cycling.
    """
    m = Maze(25, 25)
    m.generate_random_maze(seed=42)
    ui = MazeUI(m, width=1280, height=720)
    
    # 1. Verify default size selection is 25 x 25
    assert "25 x 25" in ui.dropdown_size.selected_value
    
    # 2. Test shortcut 'M' (Cycle Sample Mazes)
    initial_sample = ui.sample_index
    # Post key event for 'M'
    ev_m = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_m)
    pygame.event.post(ev_m)
    ui.handle_events()
    assert ui.maze.has_solution() is True
    assert ui.sample_index != initial_sample
    assert "Loaded sample" in ui.status_message
    
    # 3. Test Settings modal file buttons and Escape
    ui.state = "MODAL_SETTINGS"
    assert ui.btn_modal_load is not None
    assert ui.btn_modal_samples is not None
    
    # Simulate clicking modal samples button
    prev_sample_idx = ui.sample_index
    ui.btn_modal_samples.callback()
    assert ui.sample_index != prev_sample_idx
    
    # Simulate Escape key in modal
    ev_esc = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
    pygame.event.post(ev_esc)
    ui.handle_events()
    assert ui.state == "IDLE"
    
    # 4. Test Load Custom File action with dummy path
    sample1_path = os.path.join(os.path.dirname(__file__), "..", "mazes", "sample1.txt")
    assert os.path.exists(sample1_path)
    ui.maze.load_from_file(sample1_path)
    assert ui.maze.rows == 15
    assert ui.maze.cols == 15
    assert ui.maze.has_solution() is True
    
    pygame.quit()
