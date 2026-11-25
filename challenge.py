"""
Human Challenge Core Domain Module.

Manages the lifecycle, manual player locomotion, monotonic timing,
and isolated AI comparison orchestration for Human vs AI Challenge Mode.

This module is completely independent of Pygame and graphical rendering.
"""

from enum import Enum
import time
from typing import Tuple, List, Set, Optional, Dict, Any, Callable

from maze import Maze
from algorithms.bfs import bfs_solve
from algorithms.dfs import dfs_solve
from algorithms.astar import astar_solve


class ChallengeStatus(str, Enum):
    """Lifecycle states of a human maze challenge session."""
    READY = "READY"
    PLAYING = "PLAYING"
    PAUSED = "PAUSED"
    WON = "WON"
    LOST = "LOST"


class HumanChallenge:
    """
    Manages an interactive human maze solving challenge.
    
    Responsibilities:
    - Track player position, move history, and unique visited cells.
    - Enforce orthogonal movement and reject walls/boundaries.
    - Measure elapsed wall-clock time using a monotonic clock.
    - Calculate path length as valid transitions (excluding Start).
    - Provide division-by-zero safe optimality ratios.
    - Orchestrate isolated AI benchmarking against independent maze clones.
    """

    VALID_DIRECTIONS: Set[Tuple[int, int]] = {
        (-1, 0),  # Up
        (1, 0),   # Down
        (0, -1),  # Left
        (0, 1)    # Right
    }

    def __init__(self, maze: Maze, clock_func: Callable[[], float] = time.perf_counter):
        """
        Initialize a human challenge session for the provided maze.
        
        Args:
            maze: The Maze instance to solve.
            clock_func: Injectable monotonic clock function returning float seconds.
                        Defaults to time.perf_counter.
        """
        self.maze = maze
        self.clock_func = clock_func

        self.player_pos: Tuple[int, int] = maze.start
        self.goal: Tuple[int, int] = maze.goal
        self.path: List[Tuple[int, int]] = [maze.start]
        self.visited_cells: Set[Tuple[int, int]] = {maze.start}
        self.move_count: int = 0

        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.pause_started: Optional[float] = None
        self.paused_duration: float = 0.0
        self.status: ChallengeStatus = ChallengeStatus.READY

        # Handle Start-equals-Goal edge case immediately upon initialization
        if self.player_pos == self.goal:
            self._trigger_victory()

    def _trigger_victory(self) -> None:
        """Mark challenge as won and freeze elapsed time."""
        now = self.clock_func()
        if self.start_time is None:
            self.start_time = now
        self.end_time = now
        self.status = ChallengeStatus.WON

    def start(self) -> None:
        """
        Start the challenge session and arm the monotonic clock.
        
        Idempotent behavior:
        - READY -> PLAYING: arms start_time.
        - PLAYING -> PLAYING: no change; preserves the original start_time.
        - WON -> WON: no change.
        - Start == Goal: preserves immediate victory.
        """
        # Idempotent: If already PLAYING or WON, do not restart timer
        if self.status == ChallengeStatus.PAUSED:
            self.resume()
            return
        if self.status in (ChallengeStatus.PLAYING, ChallengeStatus.WON, ChallengeStatus.LOST):
            return

        now = self.clock_func()
        self.start_time = now
        self.end_time = None

        if self.player_pos == self.goal:
            self._trigger_victory()
        else:
            self.status = ChallengeStatus.PLAYING

    def reset(self) -> None:
        """Reset the challenge session to its initial state."""
        self.player_pos = self.maze.start
        self.goal = self.maze.goal
        self.path = [self.maze.start]
        self.visited_cells = {self.maze.start}
        self.move_count = 0
        self.start_time = None
        self.end_time = None
        self.pause_started = None
        self.paused_duration = 0.0

        if self.player_pos == self.goal:
            self._trigger_victory()
        else:
            self.status = ChallengeStatus.READY

    def move(self, dr: int, dc: int) -> bool:
        """
        Attempt an orthogonal player movement by delta (dr, dc).
        
        Execution Order:
        1. Reject if already won.
        2. Validate direction (orthogonal Manhattan only).
        3. Calculate target cell (nr, nc).
        4. Validate target walkability (boundary and walls).
           If rejected, return False without changing position, moves, status, or timer.
        5. If valid and status is READY, start the challenge timer now.
        6. Execute valid movement transition.
        7. If target is Goal, trigger victory.
        
        Args:
            dr: Row delta (-1 for Up, +1 for Down, 0 for Left/Right).
            dc: Column delta (-1 for Left, +1 for Right, 0 for Up/Down).
            
        Returns:
            True if the move is legal and executed.
            False if rejected (diagonal, wall collision, boundary, or game not active).
        """
        # Reject movement if challenge has already finished
        if self.status in (ChallengeStatus.WON, ChallengeStatus.LOST, ChallengeStatus.PAUSED):
            return False

        # 1. Validate direction
        if (dr, dc) not in self.VALID_DIRECTIONS:
            return False

        # 2. Calculate target cell
        nr, nc = self.player_pos[0] + dr, self.player_pos[1] + dc

        # 3. Validate target walkability BEFORE changing any state or starting timer
        if not self.maze.is_walkable(nr, nc):
            return False

        # 4. Target is walkable. If still in READY state, arm challenge now
        if self.status == ChallengeStatus.READY:
            self.start()

        # Reject if not in PLAYING state (safeguard)
        if self.status != ChallengeStatus.PLAYING:
            return False

        # 5. Execute valid transition
        self.player_pos = (nr, nc)
        self.path.append(self.player_pos)
        self.visited_cells.add(self.player_pos)
        self.move_count += 1

        # 6. Check goal arrival
        if self.player_pos == self.goal:
            self._trigger_victory()

        return True

    def pause(self) -> bool:
        """Pause active play and freeze elapsed-time accumulation."""
        if self.status != ChallengeStatus.PLAYING:
            return False
        self.pause_started = self.clock_func()
        self.status = ChallengeStatus.PAUSED
        return True

    def resume(self) -> bool:
        """Resume a paused challenge without counting the paused duration."""
        if self.status != ChallengeStatus.PAUSED or self.pause_started is None:
            return False
        self.paused_duration += max(0.0, self.clock_func() - self.pause_started)
        self.pause_started = None
        self.status = ChallengeStatus.PLAYING
        return True

    def fail(self) -> bool:
        """Freeze the timer and mark a challenge attempt as failed."""
        if self.status != ChallengeStatus.PLAYING:
            return False
        self.end_time = self.clock_func()
        self.status = ChallengeStatus.LOST
        return True

    def move_up(self) -> bool:
        """Convenience method for moving Up (-1, 0)."""
        return self.move(-1, 0)

    def move_down(self) -> bool:
        """Convenience method for moving Down (1, 0)."""
        return self.move(1, 0)

    def move_left(self) -> bool:
        """Convenience method for moving Left (0, -1)."""
        return self.move(0, -1)

    def move_right(self) -> bool:
        """Convenience method for moving Right (0, 1)."""
        return self.move(0, 1)

    @property
    def elapsed_time(self) -> float:
        """
        Elapsed wall-clock time in seconds using the monotonic clock.
        Freezes upon challenge completion.
        """
        if self.start_time is None:
            return 0.0
        stop_time = self.end_time if self.end_time is not None else self.clock_func()
        paused = self.paused_duration
        if self.status == ChallengeStatus.PAUSED and self.pause_started is not None:
            paused += max(0.0, stop_time - self.pause_started)
        return max(0.0, stop_time - self.start_time - paused)

    @property
    def human_path_length(self) -> int:
        """
        Number of successful movement transitions from Start to current position.
        The initial Start position is not counted as a move.
        """
        return max(0, len(self.path) - 1)

    @property
    def unique_cells_visited(self) -> int:
        """Total number of distinct maze cells visited during the challenge."""
        return len(self.visited_cells)

    @property
    def is_won(self) -> bool:
        """Return True if the challenge has been completed successfully."""
        return self.status == ChallengeStatus.WON

    @property
    def is_playing(self) -> bool:
        """Return True if the challenge is actively underway."""
        return self.status == ChallengeStatus.PLAYING

    @property
    def is_ready(self) -> bool:
        """Return True if the challenge is waiting to start."""
        return self.status == ChallengeStatus.READY

    def get_result(self) -> Dict[str, Any]:
        """Return a structured summary of the human player's performance."""
        return {
            "status": self.status.value,
            "final_position": self.player_pos,
            "move_count": self.move_count,
            "unique_cells_visited": len(self.visited_cells),
            "elapsed_time": self.elapsed_time,
            "elapsed_time_s": self.elapsed_time,
            "human_path_length": self.human_path_length,
            "path_length": self.human_path_length,
            "path": list(self.path)
        }

    def calculate_optimality_ratio(self, bfs_path_length: int) -> float:
        """
        Calculate the human optimality ratio relative to the BFS optimal path length.
        
        Rules:
        - Challenge must be in WON status.
        - If human moves == 0 and bfs_path_length == 0: returns 100.0% (Start equals Goal).
        - If both lengths are positive: returns (bfs_path_length / human_moves) * 100.0.
        - Raises RuntimeError if challenge is not won.
        - Raises ValueError if lengths are negative or maze is unsolvable.
        """
        if self.status != ChallengeStatus.WON:
            raise RuntimeError("Cannot calculate optimality ratio for an incomplete challenge.")

        # Start equals Goal edge case: player started at Goal with 0 moves
        if self.move_count == 0 and bfs_path_length == 0:
            return 100.0

        if bfs_path_length <= 0 or self.move_count <= 0:
            raise ValueError(
                f"Cannot calculate optimality ratio for non-positive path lengths "
                f"(bfs_path_length={bfs_path_length}, human_moves={self.move_count})."
            )

        return (bfs_path_length / self.move_count) * 100.0

    def compare_with_ai(self) -> Dict[str, Any]:
        """
        Execute BFS, DFS, and A* on independent clones of the maze and compile comparison metrics.
        
        Mandatory rules:
        - Must not run before the human player wins (raises RuntimeError).
        - Each algorithm receives an independent deep clone.
        - Clone invariants (dimensions, topology, Start, Goal, isolation) are verified.
        - Original maze remains completely immutable.
        - Computes transitions (len(path) - 1).
        - Guards against division by zero in optimality calculation.
        """
        if self.status != ChallengeStatus.WON:
            raise RuntimeError("AI comparison cannot be run before the challenge is won.")

        solvers = [
            ("BFS", bfs_solve),
            ("DFS", dfs_solve),
            ("A*", astar_solve)
        ]

        ai_results: Dict[str, Dict[str, Any]] = {}
        original_grid_snapshot = [row[:] for row in self.maze.grid]
        original_start = self.maze.start
        original_goal = self.maze.goal
        original_rows = self.maze.rows
        original_cols = self.maze.cols

        seen_clones: List[Maze] = []

        for name, solver in solvers:
            clone = self.maze.clone()

            # Strict clone invariant verification against original maze
            if (clone.rows != original_rows or clone.cols != original_cols or
                clone.start != original_start or clone.goal != original_goal or
                clone.grid != original_grid_snapshot or
                clone is self.maze or clone.grid is self.maze.grid or
                any(clone.grid[r] is self.maze.grid[r] for r in range(original_rows))):
                raise AssertionError(f"Clone invariant verification failed for algorithm {name} against original.")

            # Strict clone isolation verification against previously created clones
            for prev_clone in seen_clones:
                if (clone is prev_clone or clone.grid is prev_clone.grid or
                    any(clone.grid[r] is prev_clone.grid[r] for r in range(original_rows))):
                    raise AssertionError(f"Clone isolation failed between {name} and previous clones.")

            seen_clones.append(clone)

            # Time algorithmic execution with monotonic clock
            t0 = self.clock_func()
            res = solver(clone)
            t_elapsed_ms = (self.clock_func() - t0) * 1000.0

            # Consistency check: If human solved the maze, algorithm must find a path
            if not res.get("found", False):
                raise RuntimeError(
                    f"Consistency error: {name} failed to find a path on a maze solved by human player."
                )

            path = res.get("path", [])
            path_length = max(0, len(path) - 1)

            ai_results[name] = {
                "path_length": path_length,
                "nodes_expanded": res["nodes_expanded"],
                "time_ms": res.get("time_ms", t_elapsed_ms),
                "compute_time_ms": t_elapsed_ms,
                "found": res["found"],
                "path": list(path)
            }

        # Verify original maze immutability
        if (self.maze.grid != original_grid_snapshot or
            self.maze.start != original_start or
            self.maze.goal != original_goal or
            any(self.maze.grid[r] != original_grid_snapshot[r] for r in range(original_rows))):
            raise AssertionError("Original maze was mutated during AI comparison.")

        bfs_opt_length = ai_results["BFS"]["path_length"]
        optimality = self.calculate_optimality_ratio(bfs_opt_length)

        return {
            "human": self.get_result(),
            "ai": ai_results,
            "optimality_ratio": optimality,
            "optimal_path_length": bfs_opt_length
        }
