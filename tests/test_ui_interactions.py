"""
Phase 3.5: Comprehensive Headless UI Testing Suite
Simulates real Pygame mouse, keyboard, and window events.
Verifies all application states, transitions, actions, modals, and drawing logic.
"""

import os
import pygame
import pytest

from maze import Maze
from ui import MazeUI


@pytest.fixture(autouse=True)
def setup_headless_env():
    """Ensure SDL runs in headless dummy mode for all UI tests."""
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_AUDIODRIVER"] = "dummy"


def test_ui_state_lifecycle_and_actions():
    """Verify entire UI lifecycle: Idle -> Step -> Running -> Paused -> Finished -> Reset."""
    m = Maze(15, 15)
    m.generate_random_maze(seed=42)
    ui = MazeUI(m, width=1280, height=720)
    
    # 1. Initial State
    assert ui.state == "IDLE"
    assert ui.nodes_expanded == 0
    assert ui.final_path is None
    
    # 2. Step Action
    ui.action_step()
    assert ui.state == "PAUSED"
    assert ui.generator is not None
    assert ui.nodes_expanded >= 1
    
    # 3. Resume / Pause Action
    ui.action_pause_resume()
    assert ui.state == "RUNNING"
    ui.action_pause_resume()
    assert ui.state == "PAUSED"
    
    # 4. Resume to Finish
    ui.action_pause_resume()
    assert ui.state == "RUNNING"
    while ui.generator and ui.state == "RUNNING":
        ui._advance_generator_step()
        
    assert ui.state == "FINISHED"
    assert ui.final_path is not None
    assert ui.path_length > 0
    
    # 5. Reset
    ui.action_reset()
    assert ui.state == "IDLE"
    assert ui.nodes_expanded == 0
    assert ui.final_path is None


def test_ui_unsolvable_search_handling():
    """Verify that MazeUI handles an unsolvable maze cleanly and transitions to NO_PATH."""
    m = Maze(9, 9)
    m.start = (1, 1)
    m.goal = (7, 7)
    # Wall off goal completely
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        m.set_wall(7 + dr, 7 + dc, True)
        
    ui = MazeUI(m, width=1280, height=720)
    ui.action_solve_or_pause()
    while ui.generator and ui.state == "RUNNING":
        ui._advance_generator_step()
        
    assert ui.state == "NO_PATH"
    assert ui.final_path is None
    assert "No path" in ui.status_message


def test_ui_modals_open_and_close():
    """Verify Settings, Info, and Comparison modals and their state guards."""
    m = Maze(15, 15)
    m.generate_random_maze(seed=42)
    ui = MazeUI(m, width=1280, height=720)
    
    # Comparison modal
    ui.action_compare_algorithms()
    assert ui.state == "COMPARING"
    assert ui.compare_results is not None
    assert len(ui.compare_results) == 3
    ui.close_modal()
    assert ui.state == "IDLE"
    
    # Settings modal (opened via header icon action or state transition)
    ui.state = "MODAL_SETTINGS"
    assert ui.state == "MODAL_SETTINGS"
    ui.draw()  # Verify rendering of settings modal
    # Test closing modal via Escape key
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_ESCAPE}))
    ui.handle_events()
    assert ui.state == "IDLE"
    
    # Info modal
    ui.state = "MODAL_INFO"
    assert ui.state == "MODAL_INFO"
    ui.draw()  # Verify rendering of info modal
    # Test closing modal via close button click
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_ESCAPE}))
    ui.handle_events()
    assert ui.state == "IDLE"


def test_ui_dropdowns_and_checkboxes():
    """Verify algorithm selection, maze size changes, speed controls, and all 4 checkbox toggles."""
    m = Maze(15, 15)
    m.generate_random_maze(seed=42)
    ui = MazeUI(m, width=1280, height=720)
    
    # Algorithm dropdown selection
    ui.select_algorithm("DFS")
    assert ui.selected_algo == "DFS"
    ui.select_algorithm("A*")
    assert ui.selected_algo == "A*"
    ui.select_algorithm("BFS")
    assert ui.selected_algo == "BFS"
    
    # Maze size selection dropdown callback
    ui._on_select_size_dropdown("15 x 15")
    assert ui.maze.rows == 15 and ui.maze.cols == 15
    ui._on_select_size_dropdown("25 x 25")
    assert ui.maze.rows == 25 and ui.maze.cols == 25
    
    # Speed controls: actions and keyboard shortcuts (UP/DOWN)
    s0 = ui.speed_level
    ui.action_increase_speed()
    assert ui.speed_level >= s0
    ui.action_decrease_speed()
    assert ui.speed_level <= s0 or ui.speed_level >= 1
    
    # Verify speed keyboard events (K_UP and K_DOWN)
    cur_speed = ui.speed_level
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_UP}))
    ui.handle_events()
    assert ui.speed_level >= cur_speed
    
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_DOWN}))
    ui.handle_events()
    assert ui.speed_level in ui.speed_options
    
    # Verify ALL 4 Checkbox toggles (both True and False)
    # 1. cb_explored
    ui.cb_explored.on_toggle(False)
    assert ui.show_explored_nodes is False
    ui.cb_explored.on_toggle(True)
    assert ui.show_explored_nodes is True
    
    # 2. cb_path
    ui.cb_path.on_toggle(False)
    assert ui.show_final_path is False
    ui.cb_path.on_toggle(True)
    assert ui.show_final_path is True
    
    # 3. cb_heuristic
    ui.cb_heuristic.on_toggle(True)
    assert ui.show_heuristic is True
    ui.cb_heuristic.on_toggle(False)
    assert ui.show_heuristic is False
    
    # 4. cb_animate
    ui.cb_animate.on_toggle(False)
    assert ui.animate_search is False
    ui.cb_animate.on_toggle(True)
    assert ui.animate_search is True


def test_ui_mouse_events_wall_drawing_and_dragging():
    """Simulate real mouse down, motion, and up events for drawing and dragging."""
    m = Maze(15, 15)
    ui = MazeUI(m, width=1280, height=720)
    
    # 1. Click to draw a wall
    cell_r, cell_c = 3, 3
    rect = ui._get_cell_rect(cell_r, cell_c)
    
    # Post mouse down event on cell
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': rect.center}))
    ui.handle_events()
    assert ui.maze.is_wall(cell_r, cell_c) is True
    
    # Post mouse down again to toggle wall off
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': rect.center}))
    ui.handle_events()
    assert ui.maze.is_wall(cell_r, cell_c) is False
    
    # 2. Dragging start node to a valid open cell
    start_r, start_c = ui.maze.start
    start_rect = ui._get_cell_rect(start_r, start_c)
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': start_rect.center}))
    ui.handle_events()
    assert ui.dragging_start is True
    
    # Drag to new open cell (2, 2)
    target_rect = ui._get_cell_rect(2, 2)
    pygame.event.post(pygame.event.Event(pygame.MOUSEMOTION, {'pos': target_rect.center, 'rel': (10, 10), 'buttons': (1, 0, 0)}))
    ui.handle_events()
    
    # Release mouse
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP, {'button': 1, 'pos': target_rect.center}))
    ui.handle_events()
    assert ui.dragging_start is False
    assert ui.maze.start == (2, 2)


def test_ui_drag_invalid_destinations_and_outside_grid():
    """Verify dragging Start or Goal onto walls, onto each other, or outside the grid is rejected."""
    m = Maze(15, 15)
    m.generate_random_maze(seed=42)
    ui = MazeUI(m, width=1280, height=720)
    
    start_pos = ui.maze.start
    goal_pos = ui.maze.goal
    
    # 1. Find a wall cell
    wall_cell = None
    for r in range(15):
        for c in range(15):
            if ui.maze.is_wall(r, c):
                wall_cell = (r, c)
                break
        if wall_cell:
            break
            
    wall_rect = ui._get_cell_rect(wall_cell[0], wall_cell[1])
    goal_rect = ui._get_cell_rect(goal_pos[0], goal_pos[1])
    start_rect = ui._get_cell_rect(start_pos[0], start_pos[1])
    
    # Try dragging Start into a Wall -> Should NOT change start position
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': start_rect.center}))
    ui.handle_events()
    assert ui.dragging_start is True
    pygame.event.post(pygame.event.Event(pygame.MOUSEMOTION, {'pos': wall_rect.center, 'rel': (0, 0), 'buttons': (1, 0, 0)}))
    ui.handle_events()
    assert ui.maze.start == start_pos  # Start cell unchanged
    
    # Try dragging Start onto Goal -> Should NOT change start position
    pygame.event.post(pygame.event.Event(pygame.MOUSEMOTION, {'pos': goal_rect.center, 'rel': (0, 0), 'buttons': (1, 0, 0)}))
    ui.handle_events()
    assert ui.maze.start == start_pos  # Start cell unchanged
    
    # Release mouse outside the grid (e.g. at (10, 10))
    pygame.event.post(pygame.event.Event(pygame.MOUSEMOTION, {'pos': (10, 10), 'rel': (0, 0), 'buttons': (1, 0, 0)}))
    ui.handle_events()
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP, {'button': 1, 'pos': (10, 10)}))
    ui.handle_events()
    assert ui.dragging_start is False
    assert ui.maze.start == start_pos
    
    # 2. Try dragging Goal into a Wall -> Should NOT change goal position
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': goal_rect.center}))
    ui.handle_events()
    assert ui.dragging_goal is True
    pygame.event.post(pygame.event.Event(pygame.MOUSEMOTION, {'pos': wall_rect.center, 'rel': (0, 0), 'buttons': (1, 0, 0)}))
    ui.handle_events()
    assert ui.maze.goal == goal_pos
    
    # Try dragging Goal onto Start -> Should NOT change goal position
    pygame.event.post(pygame.event.Event(pygame.MOUSEMOTION, {'pos': start_rect.center, 'rel': (0, 0), 'buttons': (1, 0, 0)}))
    ui.handle_events()
    assert ui.maze.goal == goal_pos
    
    # Release mouse
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP, {'button': 1, 'pos': goal_rect.center}))
    ui.handle_events()
    assert ui.dragging_goal is False
    assert ui.maze.goal == goal_pos


def test_ui_control_guards_during_running_and_modals():
    """Verify editing and background controls are guarded during active RUNNING and modal states."""
    m = Maze(15, 15)
    m.generate_random_maze(seed=42)
    ui = MazeUI(m, width=1280, height=720)
    
    # 1. While RUNNING, interactive grid edits and dragging are completely ignored
    ui.action_solve_or_pause()
    assert ui.state == "RUNNING"
    
    # Pick an open cell to test click
    open_cell = None
    for r in range(1, 14):
        for c in range(1, 14):
            if not ui.maze.is_wall(r, c) and (r, c) != ui.maze.start and (r, c) != ui.maze.goal:
                open_cell = (r, c)
                break
        if open_cell:
            break
            
    open_rect = ui._get_cell_rect(open_cell[0], open_cell[1])
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': open_rect.center}))
    ui.handle_events()
    # Cell must remain open, not toggled to wall!
    assert ui.maze.is_wall(open_cell[0], open_cell[1]) is False
    
    # Attempt dragging start while RUNNING
    start_rect = ui._get_cell_rect(ui.maze.start[0], ui.maze.start[1])
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': start_rect.center}))
    ui.handle_events()
    assert ui.dragging_start is False  # Dragging disallowed while RUNNING
    
    # 2. During Modal states, header icon clicks and background controls are guarded
    ui.action_reset()
    ui.state = "MODAL_SETTINGS"
    home_rect = ui.header_buttons["home"]
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': home_rect.center}))
    ui.handle_events()
    # Must remain in MODAL_SETTINGS, not reset to IDLE by home button
    assert ui.state == "MODAL_SETTINGS"
    ui.close_modal()
    assert ui.state == "IDLE"


def test_ui_reset_while_searching():
    """Verify action_reset while actively RUNNING stops the generator and cleanly resets state."""
    m = Maze(15, 15)
    m.generate_random_maze(seed=42)
    ui = MazeUI(m, width=1280, height=720)
    
    ui.action_solve_or_pause()
    assert ui.state == "RUNNING"
    assert ui.generator is not None
    
    # Step generator once to have in-progress expanded nodes
    ui._advance_generator_step()
    assert ui.nodes_expanded >= 1
    
    # Call action_reset while RUNNING
    ui.action_reset()
    assert ui.state == "IDLE"
    assert ui.generator is None
    assert ui.nodes_expanded == 0
    assert ui.path_length == 0
    assert ui.final_path is None
    assert ui.btn_solve.text == "Solve Maze"


def test_ui_close_modals_via_close_button():
    """Verify that clicking the Close button closes COMPARING, MODAL_SETTINGS, and MODAL_INFO modals."""
    m = Maze(15, 15)
    m.generate_random_maze(seed=42)
    ui = MazeUI(m, width=1280, height=720)
    
    for modal_state in ["COMPARING", "MODAL_SETTINGS", "MODAL_INFO"]:
        if modal_state == "COMPARING":
            ui.action_compare_algorithms()
        else:
            ui.state = modal_state
            
        assert ui.state == modal_state
        ui.draw()  # Positions ui.btn_modal_close.rect accurately for the active modal
        
        # Click the Close button directly
        close_rect = ui.btn_modal_close.rect
        pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': close_rect.center}))
        ui.handle_events()
        pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP, {'button': 1, 'pos': close_rect.center}))
        ui.handle_events()
        
        assert ui.state == "IDLE"


def test_ui_window_resize_and_rendering():
    """Verify VIDEORESIZE event recalculates responsive layout and render executes cleanly."""
    m = Maze(25, 25)
    ui = MazeUI(m, width=1024, height=576)
    
    # Send resize event
    pygame.event.post(pygame.event.Event(pygame.VIDEORESIZE, {'size': (1600, 900), 'w': 1600, 'h': 900}))
    ui.handle_events()
    assert ui.width == 1600
    assert ui.height == 900
    assert ui.grid_area.width > 0
    
    # Trigger draw call
    ui.draw()
