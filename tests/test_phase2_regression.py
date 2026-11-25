"""
Regression tests for Phase 2 fixes:
1. Boundary semantics for is_wall() (negative and out-of-bounds coordinates return True).
2. Preserved in-bounds wall and open-cell behavior.
3. main.py error handling for missing and malformed maze files (clean error message and exit code 1).
4. Uncaught unexpected Python exceptions (not swallowed by broad try/except).
"""

import os
import sys
import subprocess
import tempfile
import pytest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from maze import Maze


def test_is_wall_negative_coordinates():
    """Verify that is_wall() returns True for negative row or column indices."""
    m = Maze(10, 10)
    assert m.is_wall(-1, 0) is True
    assert m.is_wall(0, -1) is True
    assert m.is_wall(-1, -1) is True
    assert m.is_wall(-10, 5) is True
    assert m.is_wall(5, -10) is True


def test_is_wall_beyond_grid_dimensions():
    """Verify that is_wall() returns True for coordinates exceeding grid dimensions."""
    m = Maze(10, 10)
    assert m.is_wall(10, 0) is True
    assert m.is_wall(0, 10) is True
    assert m.is_wall(10, 10) is True
    assert m.is_wall(15, 5) is True
    assert m.is_wall(5, 20) is True


def test_is_wall_in_bounds_behavior_preserved():
    """Verify that normal in-bounds wall and open-cell semantics remain intact."""
    m = Maze(10, 10)
    
    # Place wall at (3, 3)
    m.set_wall(3, 3, True)
    assert m.is_wall(3, 3) is True
    assert m.is_walkable(3, 3) is False
    
    # Open cell at (3, 4)
    m.set_wall(3, 4, False)
    assert m.is_wall(3, 4) is False
    assert m.is_walkable(3, 4) is True


def test_main_cli_missing_maze_file():
    """Verify that a missing maze file produces exit code 1 and a clean error message."""
    python_exe = sys.executable
    main_py = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "main.py"))
    
    res = subprocess.run(
        [python_exe, main_py, "--maze", "non_existent_file_xyz.txt"],
        capture_output=True,
        text=True
    )
    assert res.returncode == 1
    assert "Error: Maze file" in res.stderr
    assert "not found" in res.stderr
    # Must not dump a raw traceback
    assert "Traceback" not in res.stderr


def test_main_cli_malformed_maze_file():
    """Verify that a malformed maze file produces exit code 1 and a clean error message."""
    python_exe = sys.executable
    main_py = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "main.py"))
    
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as tf:
        tf.write("INVALID MAZE WITHOUT PROPER GRID")
        tf_path = tf.name
        
    try:
        res = subprocess.run(
            [python_exe, main_py, "--maze", tf_path],
            capture_output=True,
            text=True
        )
        assert res.returncode == 1
        assert "Error: Failed to load maze from" in res.stderr
        # Must not dump a raw unhandled traceback
        assert "Traceback" not in res.stderr
    finally:
        if os.path.exists(tf_path):
            os.remove(tf_path)


def test_unexpected_programming_exceptions_not_swallowed():
    """Verify that non-Pygame programming exceptions propagate rather than being swallowed."""
    import main
    
    # Test that main does not catch general Exception when launching UI
    # We inspect the code of main() or simulate an AttributeError
    import inspect
    source = inspect.getsource(main.main)
    
    # Ensure 'except Exception' is absent from main.py
    assert "except Exception" not in source, "main() must not catch broad 'Exception'"
    assert "except pygame.error" in source, "main() must strictly catch pygame.error"
