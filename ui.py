"""
Modern Pygame User Interface for the AI Maze Solver application.

Follows a high-end three-column dark dashboard design inspired by modern desktop applications:
- Full-width modern top header with logo, title, and action icons (Home, Stats, Settings, Info)
- LEFT COLUMN: Controls Card (Algorithm dropdown, Maze Size dropdown, Solve Maze, Reset, Generate,
               File picker, Samples, Compare) and Visualization Card (Checkboxes for Explored Nodes,
               Final Path, Animate Search, Show Heuristic).
- CENTER COLUMN: Dominant interactive maze visualization with rounded container, crisp cell borders,
                 distinct Start/Goal markers, and prominent golden solution path.
- RIGHT COLUMN: Algorithm Info Card (Dynamic title and academic description), Results Card
                (Path Length, Nodes Explored, Frontier Size, Discovered Cells, Execution Time, Status),
                and Color Legend Card.
- Fully responsive across resolutions (1648x912, 1386x958, 1280x820, down to 1100x700).
- Pure vector icons rendered with Pygame drawing primitives with zero external assets.
"""

import os
import time
import math
import json
from array import array
import pygame
from typing import Optional, Tuple, List, Dict, Any, Set

from maze import Maze
from algorithms.bfs import bfs_solve, bfs_generator
from algorithms.dfs import dfs_solve, dfs_generator
from algorithms.astar import astar_solve, astar_generator, manhattan_distance
from challenge import HumanChallenge
from comparison_worker import ComparisonWorker

# --- MAIN USER INTERFACE MANAGER ---
from ui_theme import *  # noqa: F401,F403 - preserve public palette constants
from ui_components import (
    Button, Checkbox, Dropdown, draw_header_icon, draw_icon_maze_logo, draw_rounded_rect,
)
from ui_rendering import UIRenderingMixin

class MazeUI(UIRenderingMixin):
    """Main responsive desktop application UI manager with AAA tactical styling and eye comfort."""

    def __init__(self, maze: Maze, width: int = 1280, height: int = 720):
        self.maze = maze

        os.environ['SDL_VIDEO_CENTERED'] = '1'
        pygame.init()
        pygame.font.init()
        pygame.display.set_caption("Maze Solver — Autonomous AI Search (BFS | DFS | A*)")

        # Auto-detect screen resolution to guarantee the window fits comfortably
        try:
            info = pygame.display.Info()
            if info.current_w > 0 and info.current_h > 0:
                max_w = min(1440, info.current_w - 60)
                max_h = min(820, info.current_h - 80)
                self.width = min(width, max_w)
                self.height = min(height, max_h)
                self.width = max(800, self.width)
                self.height = max(560, self.height)
            else:
                self.width = width
                self.height = height
        except Exception:
            self.width = width
            self.height = height

        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.audio_muted = False
        self.audio_volume = 0.55

        # Scale and load typography hierarchy for maximum eye comfort and readability
        self._init_fonts()
        self._init_feedback_audio()

        # Application State
        self.selected_algo = "A*"
        self.state = "IDLE"  # Solver, challenge, and modal states are managed by the event loop.
        self.status_message = "Ready to solve."

        # Search Sets
        self.generator = None
        self.expanded_cells: Set[Tuple[int, int]] = set()
        self.frontier_cells: Set[Tuple[int, int]] = set()
        self.discovered_cells: Set[Tuple[int, int]] = set()
        self.final_path: Optional[List[Tuple[int, int]]] = None
        self.current_cell: Optional[Tuple[int, int]] = None

        # Statistics
        self.nodes_expanded: int = 0
        self.path_length: int = 0
        self.execution_time_ms: float = 0.0
        self.search_compute_time: float = 0.0

        # Visualization Flags
        self.show_explored_nodes = True
        self.show_final_path = True
        self.animate_search = True
        self.show_heuristic = False

        # Speed Settings
        self.speed_options = [1, 2, 5, 10, 25, 50]
        self.speed_index = 2
        self.speed_level = self.speed_options[self.speed_index]

        # Mouse Dragging State
        self.dragging_start = False
        self.dragging_goal = False
        self.drawing_wall_mode: Optional[bool] = None

        # Comparison State
        self.compare_results: Optional[List[Dict[str, Any]]] = None
        self.comparison_error: Optional[str] = None
        self.comparison_worker = ComparisonWorker()

        # Challenge Mode State
        self.challenge: Optional[HumanChallenge] = None
        self.challenge_comparison_results: Optional[Dict[str, Any]] = None
        self.challenge_selected_view_path: Optional[str] = None
        self.challenge_comparison_attempted: bool = False
        self.challenge_level = 0
        self.challenge_original_maze: Optional[Maze] = None
        self.challenge_level_count = 3
        self.challenge_level_scores: Dict[int, int] = {}
        self.challenge_optimal_moves: Optional[int] = None
        self.challenge_move_limit: Optional[int] = None
        self.challenge_feedback_kind: Optional[str] = None
        self.challenge_feedback_until = 0.0
        self.challenge_hint_text: Optional[str] = None
        self.challenge_hint_until = 0.0
        self.challenge_last_progress_at = time.perf_counter()
        self.challenge_blocked_attempts = 0
        self.challenge_hint_auto_shown = False
        self.challenge_difficulty = "Medium"
        self.challenge_unlocked_level = 1
        self.challenge_best_scores: Dict[int, int] = {}
        self.challenge_campaign_completed = False
        app_data = os.environ.get("APPDATA") or os.path.join(os.path.expanduser("~"), ".ai_maze_solver")
        self.challenge_progress_file = os.path.join(app_data, "AI_Maze_Solver", "challenge_progress.json")
        self.user_settings_file = os.path.join(app_data, "AI_Maze_Solver", "user_settings.json")
        self._saved_campaign_base: Optional[Dict[str, Any]] = None
        self.maze_share_status = ""
        self.maze_zoom = 1.0
        self.maze_pan_x = 0
        self.maze_pan_y = 0
        self.maze_cell_size = 1
        self._base_cell_size = 1
        self.maze_viewport_rect = pygame.Rect(0, 0, 1, 1)
        self._maze_pan_drag = False
        self._maze_pan_last_pos: Optional[Tuple[int, int]] = None
        self._load_challenge_progress()
        self._load_user_settings()
        self._apply_audio_settings()

        # Sample Files
        self.sample_mazes = ["sample1.txt", "sample2.txt", "sample3.txt"]
        self.sample_index = 0

        # Header Icon Rects
        self.header_buttons = {}

        # Instantiate widgets and calculate initial responsive layout
        self._init_widgets()
        self._layout_ui()

    def _init_feedback_audio(self) -> None:
        """Build short optional tones with the standard library; keep play usable without audio."""
        self.feedback_sounds: Dict[str, pygame.mixer.Sound] = {}
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=256)
            mixer_info = pygame.mixer.get_init()
            if mixer_info is None:
                return
            sample_rate, sample_format, channels = mixer_info
            if sample_format != -16 or channels not in (1, 2):
                return
            for kind, notes, duration in (
                ("move", (660,), 0.055),
                ("wall", (155,), 0.11),
                ("win", (523, 659, 784), 0.32),
            ):
                frames = max(1, int(sample_rate * duration))
                samples = array("h")
                for index in range(frames):
                    note_index = min(len(notes) - 1, index * len(notes) // frames)
                    attack = min(1.0, index / max(1.0, sample_rate * 0.008))
                    release = min(1.0, (frames - index) / max(1.0, sample_rate * 0.025))
                    envelope = min(attack, release)
                    value = int(6500 * envelope * math.sin(2 * math.pi * notes[note_index] * index / sample_rate))
                    samples.append(value)
                    if channels == 2:
                        samples.append(value)
                self.feedback_sounds[kind] = pygame.mixer.Sound(buffer=samples.tobytes())
            self._apply_audio_settings()
        except (pygame.error, OverflowError, ValueError):
            self.feedback_sounds = {}

    def _apply_audio_settings(self) -> None:
        volume = 0.0 if self.audio_muted else max(0.0, min(1.0, self.audio_volume))
        for sound in getattr(self, "feedback_sounds", {}).values():
            sound.set_volume(volume)

    def _load_user_settings(self) -> None:
        try:
            with open(self.user_settings_file, "r", encoding="utf-8") as settings_file:
                settings = json.load(settings_file)
            difficulty = str(settings.get("challenge_difficulty", self.challenge_difficulty)).title()
            if difficulty in ("Easy", "Medium", "Hard"):
                self.challenge_difficulty = difficulty
            self.audio_muted = bool(settings.get("audio_muted", self.audio_muted))
            self.audio_volume = max(0.0, min(1.0, float(settings.get("audio_volume", self.audio_volume))))
        except (OSError, json.JSONDecodeError, AttributeError, TypeError, ValueError):
            pass

    def _save_user_settings(self) -> None:
        temp_path = self.user_settings_file + ".tmp"
        try:
            os.makedirs(os.path.dirname(self.user_settings_file), exist_ok=True)
            with open(temp_path, "w", encoding="utf-8") as settings_file:
                json.dump({
                    "challenge_difficulty": self.challenge_difficulty,
                    "audio_muted": self.audio_muted,
                    "audio_volume": self.audio_volume,
                }, settings_file, indent=2)
            os.replace(temp_path, self.user_settings_file)
        except OSError:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except OSError:
                pass

    def action_toggle_audio(self) -> None:
        self.audio_muted = not self.audio_muted
        self._apply_audio_settings()
        self._save_user_settings()

    def action_adjust_audio_volume(self, direction: int) -> None:
        self.audio_volume = round(max(0.0, min(1.0, self.audio_volume + direction * 0.1)), 2)
        self._apply_audio_settings()
        self._save_user_settings()

    def action_cycle_challenge_difficulty(self) -> None:
        options = ("Easy", "Medium", "Hard")
        self.challenge_difficulty = options[(options.index(self.challenge_difficulty) + 1) % len(options)]
        self.btn_difficulty.text = f"Diff: {self.challenge_difficulty}"
        self._save_user_settings()
        self.status_message = f"Challenge difficulty: {self.challenge_difficulty}."

    def _set_gameplay_feedback(self, kind: str) -> None:
        durations = {"move": 0.12, "wall": 0.45, "win": 1.2, "fail": 0.8}
        self.challenge_feedback_kind = kind
        self.challenge_feedback_until = time.perf_counter() + durations.get(kind, 0.25)
        self.status_message = {
            "move": "Step taken.",
            "wall": "Wall blocked.",
            "fail": "Move budget reached. Retry this level or return to the menu.",
            "win": "Goal reached!",
        }.get(kind, self.status_message)
        sound_kind = "win" if kind == "win" else "wall" if kind in ("wall", "fail") else "move"
        sound = getattr(self, "feedback_sounds", {}).get(sound_kind)
        if sound is not None and not self.audio_muted:
            try:
                sound.play()
            except pygame.error:
                pass

    @staticmethod
    def _maze_to_progress_record(maze: Maze) -> Dict[str, Any]:
        return {
            "rows": maze.rows,
            "cols": maze.cols,
            "grid": ["".join(row) for row in maze.grid],
            "start": list(maze.start),
            "goal": list(maze.goal),
        }

    @staticmethod
    def _maze_from_progress_record(record: Dict[str, Any]) -> Optional[Maze]:
        try:
            rows, cols = int(record["rows"]), int(record["cols"])
            grid_rows = record["grid"]
            if rows < 2 or cols < 2 or rows > 100 or cols > 100 or len(grid_rows) != rows:
                return None
            grid = [list(str(row)) for row in grid_rows]
            if any(len(row) != cols or any(cell not in (Maze.WALL, Maze.OPEN, Maze.START, Maze.GOAL) for cell in row) for row in grid):
                return None
            start = tuple(int(v) for v in record["start"])
            goal = tuple(int(v) for v in record["goal"])
            if len(start) != 2 or len(goal) != 2:
                return None
            maze = Maze(rows, cols)
            maze.grid = grid
            maze.start, maze.goal = start, goal
            if not maze.is_valid(*start) or not maze.is_valid(*goal):
                return None
            return maze
        except (KeyError, TypeError, ValueError):
            return None

    def _load_challenge_progress(self) -> None:
        """Load best scores and the next unlocked stage without blocking startup on bad data."""
        try:
            with open(self.challenge_progress_file, "r", encoding="utf-8") as progress_file:
                record = json.load(progress_file)
            self.challenge_unlocked_level = max(1, min(self.challenge_level_count, int(record.get("unlocked_level", 1))))
            difficulty = str(record.get("difficulty", "Medium")).title()
            self.challenge_difficulty = difficulty if difficulty in ("Easy", "Medium", "Hard") else "Medium"
            raw_scores = record.get("best_scores", {})
            self.challenge_best_scores = {
                int(level): max(0, min(100, int(score)))
                for level, score in raw_scores.items()
                if int(level) in range(1, self.challenge_level_count + 1)
            }
            self.challenge_campaign_completed = bool(record.get("campaign_completed", False))
            base_record = record.get("campaign_base_maze")
            if isinstance(base_record, dict):
                base_maze = self._maze_from_progress_record(base_record)
                self._saved_campaign_base = self._maze_to_progress_record(base_maze) if base_maze else None
        except (OSError, json.JSONDecodeError, AttributeError, TypeError, ValueError):
            self.challenge_unlocked_level = 1
            self.challenge_difficulty = "Medium"
            self.challenge_best_scores = {}
            self.challenge_campaign_completed = False
            self._saved_campaign_base = None

    def _save_challenge_progress(self) -> None:
        """Persist campaign unlocks and best scores atomically; failures do not interrupt play."""
        base = self.challenge_original_maze
        if base is not None:
            self._saved_campaign_base = self._maze_to_progress_record(base)
        record = {
            "version": 1,
            "unlocked_level": self.challenge_unlocked_level,
            "best_scores": {str(k): int(v) for k, v in self.challenge_best_scores.items()},
            "campaign_completed": self.challenge_campaign_completed,
            "campaign_base_maze": self._saved_campaign_base,
            "difficulty": self.challenge_difficulty,
        }
        temp_path = self.challenge_progress_file + ".tmp"
        try:
            os.makedirs(os.path.dirname(self.challenge_progress_file), exist_ok=True)
            with open(temp_path, "w", encoding="utf-8") as progress_file:
                json.dump(record, progress_file, indent=2)
            os.replace(temp_path, self.challenge_progress_file)
        except OSError:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except OSError:
                pass

    @staticmethod
    def _calculate_level_score(comparison: Dict[str, Any]) -> int:
        """Score moves (70%) and time (30%) against the level's BFS route and a clear target."""
        if comparison.get("error") or not comparison.get("ai", {}).get("BFS", {}).get("found"):
            return 0
        human = comparison.get("human", {})
        bfs = comparison.get("ai", {}).get("BFS", {})
        moves = max(0, int(human.get("path_length", human.get("move_count", 0))))
        optimal_moves = max(0, int(bfs.get("path_length", 0))) if bfs.get("found") else 0
        if moves == 0:
            move_score = 100.0 if optimal_moves == 0 else 0.0
        elif optimal_moves > 0:
            move_score = min(100.0, 100.0 * optimal_moves / moves)
        else:
            move_score = 0.0
        elapsed = max(0.0, float(human.get("elapsed_time_s", human.get("elapsed_time", 0.0))))
        target_seconds = max(30.0, float(optimal_moves or moves) * 2.0)
        time_score = 100.0 if elapsed <= target_seconds else 100.0 * target_seconds / elapsed
        return int(round(0.70 * move_score + 0.30 * time_score))

    def action_show_challenge_tutorial(self) -> None:
        self.state = "CHALLENGE_TUTORIAL"

    def action_close_challenge_tutorial(self) -> None:
        self.state = "IDLE"

    def action_request_new_campaign(self) -> None:
        self.state = "CHALLENGE_RESET_CONFIRM"

    def action_close_new_campaign_confirmation(self) -> None:
        self.state = "IDLE"

    def action_confirm_new_campaign(self) -> None:
        for path in (self.challenge_progress_file, self.challenge_progress_file + ".tmp"):
            try:
                if os.path.exists(path):
                    os.remove(path)
            except OSError:
                self.status_message = "Could not clear saved progress. Check file permissions."
                self.state = "IDLE"
                return
        self.challenge_unlocked_level = 1
        self.challenge_best_scores = {}
        self.challenge_campaign_completed = False
        self._saved_campaign_base = None
        self.btn_challenge.text = "Human vs AI Challenge"
        self._layout_ui()
        self.action_start_challenge()

    def action_pause_challenge(self) -> None:
        if self.challenge and self.challenge.pause():
            self.state = "CHALLENGE_PAUSED"

    def action_resume_challenge(self) -> None:
        if self.challenge and self.challenge.resume():
            self.state = "CHALLENGE_PLAYING"
            self.challenge_last_progress_at = time.perf_counter()

    def action_challenge_retry(self) -> None:
        if not self.challenge_original_maze or self.challenge_level < 1:
            return
        self._reset_challenge_hint_state()
        self._configure_challenge_move_limit()
        self.challenge = HumanChallenge(self.maze)
        self.challenge.start()
        self.challenge_comparison_results = None
        self.challenge_selected_view_path = "Human"
        self.challenge_comparison_attempted = False
        self.state = "CHALLENGE_PLAYING"
        self.status_message = f"Level {self.challenge_level} restarted. Reach the goal."

    def _init_fonts(self):
        """Scale and load typography hierarchy for maximum eye comfort, contrast, and readability."""
        is_compact = (self.height < 650)
        pt_offset = -1 if is_compact else 0
        self._font_scale = max(1.0, min(1.12, self.width / 1280, self.height / 720))

        def scaled_size(base_size: int) -> int:
            return max(10, int(round(base_size * self._font_scale)) + pt_offset)

        self._font_size = scaled_size
        self._marker_font_cache: Dict[int, pygame.font.Font] = {}
        self.font_logo = pygame.font.SysFont(["segoe ui", "arial", "sans-serif"], scaled_size(25), bold=True)
        self.font_subtitle = pygame.font.SysFont(["segoe ui", "arial", "sans-serif"], scaled_size(13))
        self.font_section = pygame.font.SysFont(["segoe ui", "arial", "sans-serif"], scaled_size(17), bold=True)
        self.font_body = pygame.font.SysFont(["segoe ui", "arial", "sans-serif"], scaled_size(15))
        self.font_body_bold = pygame.font.SysFont(["segoe ui", "arial", "sans-serif"], scaled_size(15), bold=True)
        self.font_tiny = pygame.font.SysFont(["segoe ui", "arial", "sans-serif"], scaled_size(10))
        self.font_algo_title = pygame.font.SysFont(["segoe ui", "arial", "sans-serif"], scaled_size(16), bold=True)
        self.font_stat_val = pygame.font.SysFont(["segoe ui", "arial", "sans-serif"], scaled_size(17), bold=True)
        self.font_desc = pygame.font.SysFont(["segoe ui", "arial", "sans-serif"], scaled_size(14))
        self.font_label_bold = pygame.font.SysFont(["segoe ui", "arial", "sans-serif"], scaled_size(14), bold=True)
        self.font_small = pygame.font.SysFont(["segoe ui", "arial", "sans-serif"], scaled_size(13))

    @staticmethod
    def _tile_style(cell_size: int) -> Tuple[int, int, bool]:
        """Return an inset, corner radius, and wall-edge flag safe for this cell size."""
        if cell_size <= 4:
            return 0, 0, False
        if cell_size <= 8:
            return 0, 1, False
        if cell_size < 18:
            return 1, min(2, max(1, cell_size // 6)), False
        return 2, (3 if cell_size < 28 else 4), True

    @staticmethod
    def _tile_rect(cell_rect: pygame.Rect, inset: int) -> pygame.Rect:
        """Build a non-empty tile rectangle for supported positive cell sizes."""
        safe_inset = min(max(0, inset), max(0, (min(cell_rect.width, cell_rect.height) - 1) // 2))
        return cell_rect.inflate(-2 * safe_inset, -2 * safe_inset)

    @staticmethod
    def _path_width(cell_size: int) -> int:
        """Keep path strokes proportional and no wider than one cell."""
        return max(1, min(cell_size, int(cell_size * 0.36)))

    @staticmethod
    def _breadcrumb_size(cell_size: int) -> int:
        """Return a centered breadcrumb size that always fits inside its cell."""
        if cell_size <= 4:
            return 1
        if cell_size <= 8:
            return 3
        size = max(3, int(cell_size * 0.30))
        if size % 2 == 0:
            size += 1
        return min(cell_size, size)

    @staticmethod
    def _avatar_style(cell_size: int) -> Tuple[str, int]:
        """Return either a pixel marker, compact square, or bounded circle radius."""
        if cell_size <= 3:
            return "pixel", 1
        if cell_size <= 7:
            size = max(2, min(cell_size - 2, int(cell_size * 0.55)))
            return "compact", size
        radius = min((cell_size - 1) // 2, max(1, int(cell_size * 0.30)))
        return "layered", radius

    @staticmethod
    def _centered_rect(cell_rect: pygame.Rect, size: int) -> pygame.Rect:
        """Return a square marker fully contained by a cell rectangle."""
        safe_size = max(1, min(size, cell_rect.width, cell_rect.height))
        return pygame.Rect(
            cell_rect.x + (cell_rect.width - safe_size) // 2,
            cell_rect.y + (cell_rect.height - safe_size) // 2,
            safe_size,
            safe_size,
        )

    def _marker_font(self, cell_size: int) -> Optional[pygame.font.Font]:
        """Use color-only Start/Goal markers when labels cannot fit meaningfully."""
        if cell_size < 12:
            return None
        font_size = min(self._font_size(17), max(8, int(cell_size * 0.55)))
        if font_size not in self._marker_font_cache:
            self._marker_font_cache[font_size] = pygame.font.SysFont(
                ["segoe ui", "arial", "sans-serif"], font_size, bold=True
            )
        return self._marker_font_cache[font_size]

    @property
    def visited_cells(self) -> Set[Tuple[int, int]]:
        """Backwards compatibility alias for expanded cells."""
        return self.expanded_cells

    def _init_widgets(self):
        """Initialize all buttons, dropdowns, and checkboxes."""
        dummy = pygame.Rect(0, 0, 100, 30)

        # Dropdowns
        self.algo_options = ["A* (A-Star)", "BFS (Breadth-First)", "DFS (Depth-First)"]
        self.dropdown_algo = Dropdown(dummy.copy(), self.algo_options, selected_idx=0,
                                      on_select=self._on_select_algorithm_dropdown, icon="wand")

        self.size_options = ["25 x 25", "20 x 15", "15 x 15", "30 x 20", "40 x 30"]
        cur_size_str = f"{self.maze.cols} x {self.maze.rows}"
        if cur_size_str not in self.size_options:
            self.size_options.append(cur_size_str)
        cur_idx = self.size_options.index(cur_size_str)
        self.dropdown_size = Dropdown(dummy.copy(), self.size_options, selected_idx=cur_idx,
                                      on_select=self._on_select_size_dropdown, icon="grid")

        # Primary Action Button (Pill shape)
        self.btn_solve = Button(dummy.copy(), "Solve Maze", self.action_solve_or_pause, is_primary=True, icon="play")

        # Secondary Buttons
        self.btn_reset = Button(dummy.copy(), "Reset", self.action_reset, icon="reload")
        self.btn_generate = Button(dummy.copy(), "Generate", self.action_generate_maze, icon="dice")

        # Human vs AI Challenge Button
        self.btn_challenge = Button(dummy.copy(), "Human vs AI Challenge", self.action_start_challenge, icon="dice")
        self.btn_challenge_tutorial = Button(dummy.copy(), "How to Play", self.action_show_challenge_tutorial, icon="info")
        self.btn_challenge_hint = Button(dummy.copy(), "Hint (H)", self.action_show_challenge_hint, icon="info")
        self.btn_difficulty = Button(dummy.copy(), f"Diff: {self.challenge_difficulty}", self.action_cycle_challenge_difficulty)
        self.btn_new_campaign = Button(dummy.copy(), "New Campaign", self.action_request_new_campaign, icon="reload")
        if self.challenge_unlocked_level > 1 and not self.challenge_campaign_completed:
            self.btn_challenge.text = f"Continue Level {self.challenge_unlocked_level}/{self.challenge_level_count}"

        # Challenge Results Modal Action Buttons
        self.btn_challenge_play_again = Button(dummy.copy(), "Play Again", self.action_challenge_play_again, is_primary=True, icon="reload")
        self.btn_challenge_next_level = Button(dummy.copy(), "Next Level", self.action_challenge_next_level, is_primary=True, icon="play")
        self.btn_challenge_menu = Button(dummy.copy(), "Main Menu", self.action_challenge_return_to_menu, icon="home")
        self.btn_challenge_resume = Button(dummy.copy(), "Resume", self.action_resume_challenge, is_primary=True, icon="play")
        self.btn_challenge_retry = Button(dummy.copy(), "Retry Level", self.action_challenge_retry, icon="reload")
        self.btn_tutorial_start = Button(dummy.copy(), "Start Challenge", self.action_start_challenge, is_primary=True, icon="play")
        self.btn_tutorial_close = Button(dummy.copy(), "Close", self.action_close_challenge_tutorial)
        self.btn_confirm_new_campaign = Button(dummy.copy(), "Start Over", self.action_confirm_new_campaign, is_primary=True, icon="reload")
        self.btn_cancel_new_campaign = Button(dummy.copy(), "Keep Progress", self.action_close_new_campaign_confirmation)
        self.btn_view_human = Button(dummy.copy(), "Human Path", lambda: setattr(self, 'challenge_selected_view_path', 'Human'))
        self.btn_view_bfs = Button(dummy.copy(), "BFS Path", lambda: setattr(self, 'challenge_selected_view_path', 'BFS'))
        self.btn_view_dfs = Button(dummy.copy(), "DFS Path", lambda: setattr(self, 'challenge_selected_view_path', 'DFS'))
        self.btn_view_astar = Button(dummy.copy(), "A* Path", lambda: setattr(self, 'challenge_selected_view_path', 'A*'))

        # Modal File Management Buttons
        self.btn_modal_load = Button(dummy.copy(), "Load File... (L)", self.action_load_custom_file, icon="folder")
        self.btn_modal_samples = Button(dummy.copy(), "Samples (M)", self.action_load_sample_maze, icon="dice")
        self.btn_maze_export = Button(dummy.copy(), "Save Maze for Sharing...", self.action_export_maze, icon="folder")
        self.btn_audio_toggle = Button(dummy.copy(), "Sound: On", self.action_toggle_audio)
        self.btn_volume_down = Button(dummy.copy(), "−", lambda: self.action_adjust_audio_volume(-1))
        self.btn_volume_up = Button(dummy.copy(), "+", lambda: self.action_adjust_audio_volume(1))

        # Checkboxes
        self.cb_explored = Checkbox(dummy.copy(), "Show Explored Nodes", checked=self.show_explored_nodes,
                                    on_toggle=lambda v: setattr(self, 'show_explored_nodes', v))
        self.cb_path = Checkbox(dummy.copy(), "Show Final Path", checked=self.show_final_path,
                                on_toggle=lambda v: setattr(self, 'show_final_path', v))
        self.cb_animate = Checkbox(dummy.copy(), "Animate Search", checked=self.animate_search,
                                   on_toggle=self._on_toggle_animate)
        self.cb_heuristic = Checkbox(dummy.copy(), "Show Heuristic (h)", checked=self.show_heuristic,
                                     on_toggle=lambda v: setattr(self, 'show_heuristic', v))

        # Modal Back Button
        self.btn_modal_close = Button(dummy.copy(), "Close (Esc)", self.close_modal, is_primary=True)

        self.all_buttons = [
            self.btn_solve, self.btn_reset, self.btn_generate, self.btn_challenge,
            self.btn_challenge_tutorial, self.btn_challenge_hint, self.btn_difficulty, self.btn_new_campaign
        ]

    def _on_toggle_animate(self, val: bool):
        """Handle toggling animate search. If disabled during active RUNNING, finish search immediately."""
        self.animate_search = val
        if not val and self.state == "RUNNING" and self.generator:
            while self.state == "RUNNING" and self.generator:
                self._advance_generator_step()

    def _on_select_algorithm_dropdown(self, val: str):
        if "A*" in val:
            self.select_algorithm("A*")
        elif "BFS" in val:
            self.select_algorithm("BFS")
        elif "DFS" in val:
            self.select_algorithm("DFS")

    def _on_select_size_dropdown(self, val: str):
        try:
            parts = val.split("x")
            cols = int(parts[0].strip())
            rows = int(parts[1].strip())
            self.action_reset()
            self.maze = Maze(rows, cols)
            self.maze.generate_random_maze()
            self.status_message = f"Created new {cols}x{rows} maze."
            self._layout_ui()
        except Exception as e:
            self.status_message = f"Size error: {e}"

    @property
    def algo_dropdown(self):
        return self.dropdown_algo

    def select_algorithm(self, algo_name: str):
        if self.state in ["RUNNING", "PAUSED"]:
            self.action_reset()
        self.selected_algo = algo_name
        if hasattr(self, "dropdown_algo"):
            for i, opt in enumerate(self.dropdown_algo.options):
                if algo_name in opt:
                    self.dropdown_algo.selected_idx = i
                    break
        self.status_message = f"Selected {algo_name} algorithm."

    def _layout_ui(self):
        """
        Responsive layout engine.
        Calculates all bounding boxes and relative positions for Header,
        Left Column, Center Maze Panel, and Right Column.
        Ensures a minimum 24px margin from window boundaries to prevent clipping.
        """
        margin = max(16, min(24, int(self.width * 0.018)))
        gap = max(12, min(16, int(self.width * 0.012)))
        header_h = 58

        self.header_rect = pygame.Rect(0, 0, self.width, header_h)

        # Header Action Buttons (Top-Right)
        btn_sz = 34
        bx = self.width - margin - btn_sz
        by = (header_h - btn_sz) // 2
        for btn_name in ["info", "settings", "stats", "home"]:
            self.header_buttons[btn_name] = pygame.Rect(bx, by, btn_sz, btn_sz)
            bx -= (btn_sz + 10)

        # Three Column Horizontal Sizing matching reference proportions
        side_col_w = max(245, min(305, int(self.width * 0.22)))
        content_y = header_h + 10
        content_h = self.height - content_y - margin

        left_x = margin
        center_x = left_x + side_col_w + gap
        center_w = self.width - 2 * side_col_w - 2 * margin - 2 * gap
        right_x = center_x + center_w + gap

        # LEFT COLUMN CARDS
        # 1. Controls Card
        card_ctrl_h = min(340, max(300, int(content_h * 0.52)))
        self.card_controls_rect = pygame.Rect(left_x, content_y, side_col_w, card_ctrl_h)
        # 2. Visualization Card
        card_vis_h = content_h - card_ctrl_h - gap
        self.card_vis_rect = pygame.Rect(left_x, content_y + card_ctrl_h + gap, side_col_w, card_vis_h)

        # Position elements in Controls Card
        cx = left_x + 14
        cw = side_col_w - 28
        cy = content_y + 36  # Below title
        
        # Algorithm Dropdown
        self.dropdown_algo.rect = pygame.Rect(cx, cy + 14, cw, 32)
        cy += 50

        # Maze Size Dropdown
        self.dropdown_size.rect = pygame.Rect(cx, cy + 14, cw, 32)
        cy += 52

        # Solve Maze Primary Button
        self.btn_solve.rect = pygame.Rect(cx, cy + 4, cw, 38)
        cy += 44

        # Secondary Buttons (Reset & Generate)
        hw = (cw - 10) // 2
        self.btn_reset.rect = pygame.Rect(cx, cy + 2, hw, 32)
        self.btn_generate.rect = pygame.Rect(cx + hw + 10, cy + 2, hw, 32)
        cy += 38

        # Human vs AI Challenge Button
        self.btn_challenge.rect = pygame.Rect(cx, cy + 4, cw, 36)
        half_w = (cw - 8) // 2
        self.btn_challenge_tutorial.rect = pygame.Rect(cx, cy + 42, half_w, 30)
        self.btn_difficulty.rect = pygame.Rect(cx + half_w + 8, cy + 42, cw - half_w - 8, 30)
        self.btn_challenge_hint.rect = pygame.Rect(0, 0, 0, 0)
        self.btn_difficulty.text = f"Diff: {self.challenge_difficulty}"
        self.btn_new_campaign.rect = (
            pygame.Rect(cx, cy + 76, cw, 30)
            if self.challenge_unlocked_level > 1 or self.challenge_best_scores
            else pygame.Rect(0, 0, 0, 0)
        )

        # Default rects for modal file management buttons
        self.btn_modal_load.rect = pygame.Rect(0, 0, 10, 10)
        self.btn_modal_samples.rect = pygame.Rect(0, 0, 10, 10)

        # Position elements in Visualization Card
        vx = left_x + 16
        vy = self.card_vis_rect.y + 42
        cb_gap = min(36, max(28, (card_vis_h - 52) // 4))
        for cb in [self.cb_explored, self.cb_path, self.cb_animate, self.cb_heuristic]:
            cb.rect = pygame.Rect(vx, vy, cw, 24)
            vy += cb_gap

        # CENTER COLUMN (Maze Panel)
        self.maze_panel_rect = pygame.Rect(center_x, content_y, center_w, content_h)
        # Reserve an inner viewport; large grids can be zoomed and panned within it.
        pad = 12
        avail_w = center_w - 2 * pad
        avail_h = content_h - 2 * pad
        self.maze_viewport_rect = pygame.Rect(center_x + pad, content_y + pad, avail_w, avail_h)
        self._base_cell_size = max(1, min(avail_w // self.maze.cols, avail_h // self.maze.rows))
        self._update_maze_view()

        # RIGHT COLUMN CARDS
        # 1. Algorithm Info Card
        card_info_h = min(155, max(130, int(content_h * 0.25)))
        self.card_info_rect = pygame.Rect(right_x, content_y, side_col_w, card_info_h)
        # 2. Results Card
        card_results_h = min(186, max(170, int(content_h * 0.30)))
        self.card_results_rect = pygame.Rect(right_x, content_y + card_info_h + gap, side_col_w, card_results_h)
        # 3. Legend Card
        card_legend_h = content_h - card_info_h - card_results_h - 2 * gap
        self.card_legend_rect = pygame.Rect(right_x, content_y + card_info_h + card_results_h + 2 * gap,
                                            side_col_w, card_legend_h)

        # Modal buttons
        self.btn_modal_close.rect = pygame.Rect(self.width // 2 - 75, min(650, self.height - 80), 150, 36)
        self.btn_challenge_play_again.rect = pygame.Rect(self.width // 2 - 170, min(650, self.height - 80), 160, 36)
        self.btn_challenge_menu.rect = pygame.Rect(self.width // 2 + 10, min(650, self.height - 80), 160, 36)

    # --- ACTIONS & LOGIC ---
    def action_solve_or_pause(self):
        """Handle Solve / Pause / Resume toggling without running the algorithm twice."""
        if self.state == "RUNNING":
            self.state = "PAUSED"
            self.btn_solve.text = "Resume"
            self.btn_solve.icon = "play"
            self.status_message = "Search paused."
            return
        elif self.state == "PAUSED":
            self.state = "RUNNING"
            self.btn_solve.text = "Pause"
            self.btn_solve.icon = "pause"
            self.status_message = f"Running {self.selected_algo}..."
            return

        # Fresh Solve Trigger (single execution via generator)
        self.action_reset()
        
        solvers_gen = {"A*": astar_generator, "BFS": bfs_generator, "DFS": dfs_generator}
        self.generator = solvers_gen[self.selected_algo](self.maze)
        self.search_compute_time = 0.0
        self.state = "RUNNING"
        self.btn_solve.text = "Pause"
        self.btn_solve.icon = "pause"
        self.status_message = f"Solving with {self.selected_algo}..."

        # If animation is disabled, safely finish the search immediately
        if not self.animate_search:
            while self.state == "RUNNING" and self.generator:
                self._advance_generator_step()

    def action_step(self):
        """Advance visual search by exactly one step."""
        if self.state in ["IDLE", "FINISHED", "NO_PATH"]:
            self.action_reset()
            solvers_gen = {"A*": astar_generator, "BFS": bfs_generator, "DFS": dfs_generator}
            self.generator = solvers_gen[self.selected_algo](self.maze)
            self.search_compute_time = 0.0
            self.state = "PAUSED"
            self.btn_solve.text = "Resume"
            self.btn_solve.icon = "play"
        
        if self.state == "PAUSED":
            self._advance_generator_step()

    def action_reset(self):
        """Reset search state while keeping maze layout intact."""
        self._invalidate_background_comparison()
        self._reset_maze_view()
        self.generator = None
        self.expanded_cells.clear()
        self.frontier_cells.clear()
        self.discovered_cells.clear()
        self.final_path = None
        self.current_cell = None
        self.nodes_expanded = 0
        self.path_length = 0
        self.execution_time_ms = 0.0
        self.search_compute_time = 0.0
        self.challenge = None
        self.challenge_comparison_results = None
        self.compare_results = None
        self.comparison_error = None
        self.challenge_selected_view_path = None
        self.challenge_comparison_attempted = False
        self.challenge_level = 0
        self.challenge_original_maze = None
        self.challenge_level_scores = {}
        self.challenge_optimal_moves = None
        self.challenge_move_limit = None
        self.challenge_feedback_kind = None
        self.challenge_feedback_until = 0.0
        self._reset_challenge_hint_state()
        self.state = "IDLE"
        self.btn_solve.text = "Solve Maze"
        self.btn_solve.icon = "play"
        self.status_message = "Ready to solve."

    def action_generate_maze(self):
        """Procedurally generate a new random solvable maze."""
        self.action_reset()
        try:
            self.maze.generate_random_maze()
            self.status_message = "New random maze generated."
        except ValueError as e:
            self.status_message = str(e)

    def action_load_sample_maze(self):
        """Load next sample maze from mazes/ folder."""
        self.action_reset()
        filename = self.sample_mazes[self.sample_index]
        self.sample_index = (self.sample_index + 1) % len(self.sample_mazes)
        filepath = os.path.join(os.path.dirname(__file__), "mazes", filename)
        if os.path.exists(filepath):
            try:
                self.maze.load_from_file(filepath)
                self.status_message = f"Loaded sample: {filename}"
                self._layout_ui()
            except Exception as e:
                self.status_message = f"Sample error: {e}"

    def action_load_custom_file(self):
        """Open system file picker to load custom maze file."""
        self.action_reset()
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            initial_dir = os.path.join(os.path.dirname(__file__), "mazes")
            filepath = filedialog.askopenfilename(
                initialdir=initial_dir if os.path.exists(initial_dir) else ".",
                title="Select Maze Text File",
                filetypes=[("Text Files (*.txt)", "*.txt"), ("All Files (*.*)", "*.*")]
            )
            root.destroy()
            if filepath:
                self.maze.load_from_file(filepath)
                self.status_message = f"Loaded file: {os.path.basename(filepath)}"
                self._layout_ui()
        except Exception as e:
            self.status_message = f"File dialog error: {e}"

    def action_export_maze(self) -> None:
        """Export the current maze as a portable text file that can be loaded elsewhere."""
        root = None
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            filename = filedialog.asksaveasfilename(
                title="Save Maze for Sharing",
                initialdir=os.path.join(os.path.dirname(__file__), "mazes"),
                initialfile=f"maze_{self.maze.cols}x{self.maze.rows}.txt",
                defaultextension=".txt",
                filetypes=[("Maze text files", "*.txt"), ("All files", "*.*")],
            )
            if filename:
                self.maze.save_to_file(filename)
                self.maze_share_status = f"Saved {os.path.basename(filename)}. Share it; the recipient can load it with Load File."
        except Exception as exc:
            self.maze_share_status = f"Could not save maze: {exc}"
        finally:
            if root is not None:
                try:
                    root.destroy()
                except Exception:
                    pass

    def _reset_challenge_hint_state(self) -> None:
        self.challenge_hint_text = None
        self.challenge_hint_until = 0.0
        self.challenge_last_progress_at = time.perf_counter()
        self.challenge_blocked_attempts = 0
        self.challenge_hint_auto_shown = False

    def action_show_challenge_hint(self, automatic: bool = False) -> Optional[str]:
        """Show one non-spoiling next step along a shortest route from the player."""
        if not self.challenge or self.state != "CHALLENGE_PLAYING":
            return None
        if automatic and self.challenge_hint_auto_shown:
            return self.challenge_hint_text
        hint_maze = self.maze.clone()
        if not hint_maze.set_start(*self.challenge.player_pos):
            return None
        result = bfs_solve(hint_maze)
        path = result.get("path", []) if result.get("found") else []
        if len(path) >= 2:
            dr = path[1][0] - path[0][0]
            dc = path[1][1] - path[0][1]
            direction = {(-1, 0): "up", (1, 0): "down", (0, -1): "left", (0, 1): "right"}.get((dr, dc))
            hint = f"Try moving {direction} next; it stays on a shortest route to the Goal." if direction else "Follow the open corridor toward the Goal."
        else:
            hint = "No route was found from here. Backtrack to the last junction or restart this level."
        self.challenge_hint_text = hint
        self.challenge_hint_until = time.perf_counter() + 8.0
        self.challenge_last_progress_at = time.perf_counter()
        self.challenge_hint_auto_shown = automatic
        self.challenge_blocked_attempts = 0
        return hint

    def _record_blocked_challenge_move(self) -> None:
        self.challenge_blocked_attempts += 1
        if self.challenge_blocked_attempts >= 3 and not self.challenge_hint_auto_shown:
            self.action_show_challenge_hint(automatic=True)

    @staticmethod
    def _compute_algorithm_comparison(maze: Maze) -> List[Dict[str, Any]]:
        """Compare all solvers against the same immutable maze snapshot."""
        results = []
        for name, solver in [("BFS", bfs_solve), ("DFS", dfs_solve), ("A*", astar_solve)]:
            res = solver(maze.clone())
            p_len = len(res['path']) - 1 if len(res['path']) > 1 else 0
            results.append({
                "name": name,
                "nodes": res["nodes_expanded"],
                "path_len": p_len,
                "time_ms": res["time_ms"],
                "found": res["found"]
            })
        return results

    def _invalidate_background_comparison(self) -> None:
        self.comparison_worker.cancel()

    def _poll_background_comparison(self) -> None:
        result = self.comparison_worker.poll()
        if result is None:
            return
        mode, results, error = result
        if mode == "solver":
            self.comparison_error = error
            self.compare_results = results if results is not None else []
        elif mode == "challenge":
            self._complete_challenge_victory(results, error)

    def action_compare_algorithms(self):
        """Trigger the solver comparison modal, using a worker for large mazes."""
        self.compare_results = None
        self.comparison_error = None
        self.state = "COMPARING"
        if self.maze.rows * self.maze.cols >= ASYNC_COMPARISON_CELL_THRESHOLD:
            maze_snapshot = self.maze.clone()
            self.comparison_worker.start(
                "solver", lambda: self._compute_algorithm_comparison(maze_snapshot)
            )
            return
        try:
            self.compare_results = self._compute_algorithm_comparison(self.maze)
        except Exception as exc:
            self.comparison_error = f"{type(exc).__name__}: {exc}"
            self.compare_results = []

    def action_increase_speed(self):
        """Increase animation speed level."""
        if self.speed_index < len(self.speed_options) - 1:
            self.speed_index += 1
            self.speed_level = self.speed_options[self.speed_index]

    def action_decrease_speed(self):
        """Decrease animation speed level."""
        if self.speed_index > 0:
            self.speed_index -= 1
            self.speed_level = self.speed_options[self.speed_index]

    def action_pause_resume(self):
        """Toggle pause and resume during active search."""
        self.action_solve_or_pause()

    def close_comparison(self):
        """Close comparison modal."""
        self.close_modal()

    def close_modal(self):
        """Exit any active modal overlay."""
        self._invalidate_background_comparison()
        self.state = "IDLE"
        self.compare_results = None
        self.comparison_error = None

    def action_start_challenge(self):
        """Start Human vs AI challenge on the current maze snapshot."""
        self.action_reset()
        if self.challenge_campaign_completed:
            self.challenge_campaign_completed = False
            self.challenge_unlocked_level = 1
        resume_level = max(1, min(self.challenge_level_count, self.challenge_unlocked_level))
        if resume_level > 1 and self._saved_campaign_base is not None:
            original_maze = self._maze_from_progress_record(self._saved_campaign_base) or self.maze.clone()
            self.maze = self._build_challenge_level_maze(original_maze, resume_level)
            self._layout_ui()
        else:
            original_maze = self.maze.clone()
        self.challenge_original_maze = original_maze
        self.challenge_level = resume_level
        self._reset_maze_view()
        self.challenge_level_scores = {
            level: score for level, score in self.challenge_best_scores.items()
            if level < resume_level
        }
        self._configure_challenge_move_limit()
        self.challenge = HumanChallenge(self.maze)
        self.challenge_comparison_results = None
        self.challenge_selected_view_path = "Human"
        self.challenge_comparison_attempted = False
        self.challenge.start()
        if self.challenge.is_won:
            self._on_challenge_victory()
        else:
            self.state = "CHALLENGE_PLAYING"
            self.status_message = "Challenge active! Use Arrow keys or WASD to reach the goal."

    def action_challenge_play_again(self):
        """Restart the challenge on the identical maze."""
        original_maze = self.challenge_original_maze
        level = self.challenge_level
        completed_scores = {k: v for k, v in self.challenge_level_scores.items() if k < level}
        self.action_reset()
        self.challenge_original_maze = original_maze
        self.challenge_level = level
        self.challenge_level_scores = completed_scores
        self._configure_challenge_move_limit()
        self.challenge = HumanChallenge(self.maze)
        self.challenge_comparison_results = None
        self.challenge_selected_view_path = "Human"
        self.challenge_comparison_attempted = False
        self.challenge.start()
        if self.challenge.is_won:
            self._on_challenge_victory()
        else:
            self.state = "CHALLENGE_PLAYING"
            self.status_message = "Challenge restarted! Reach the goal."

    @staticmethod
    def _odd_capped_dimension(base: int, multiplier: float, minimum: int) -> int:
        """Grow a level dimension to an odd generator-friendly size, capped at 100."""
        value = max(minimum, int(math.ceil(base * multiplier)))
        if value % 2 == 0 and value < 100:
            value += 1
        return min(100, value)

    def _build_challenge_level_maze(self, base_maze: Maze, level: int) -> Maze:
        if level <= 1:
            return base_maze.clone()
        settings = {
            "Easy": ((1.10, 1.10), (25, 25), (35, 27)),
            "Medium": ((1.25, 1.60), (25, 25), (40, 30)),
            "Hard": ((1.50, 1.50), (31, 31), (50, 38)),
        }
        multipliers, level2_min, level3_min = settings[self.challenge_difficulty]
        multiplier = multipliers[level - 2]
        min_rows, min_cols = level2_min if level == 2 else level3_min
        rows = self._odd_capped_dimension(base_maze.rows, multiplier, min_rows)
        cols = self._odd_capped_dimension(base_maze.cols, multiplier, min_cols)
        maze = Maze(rows, cols)
        maze.generate_random_maze(seed=202600 + level * 1000 + rows * 100 + cols)
        return maze

    def _configure_challenge_move_limit(self) -> None:
        """Set a progressively tighter move budget after the untimed warm-up level."""
        self.challenge_optimal_moves = None
        self.challenge_move_limit = None
        if self.challenge_level < 2:
            return
        result = bfs_solve(self.maze.clone())
        if not result.get("found"):
            return
        self.challenge_optimal_moves = max(0, len(result.get("path", [])) - 1)
        factors = {
            "Easy": (1.80, 1.55),
            "Medium": (1.60, 1.25),
            "Hard": (1.35, 1.10),
        }
        factor = factors[self.challenge_difficulty][self.challenge_level - 2]
        self.challenge_move_limit = max(
            self.challenge_optimal_moves,
            int(math.ceil(self.challenge_optimal_moves * factor)),
        )

    def action_challenge_next_level(self):
        """Advance to a larger generated maze while retaining the original maze for exit."""
        if self.state != "CHALLENGE_RESULTS" or self.challenge_level >= self.challenge_level_count:
            return
        original_maze = self.challenge_original_maze or self.maze.clone()
        run_scores = dict(self.challenge_level_scores)
        next_level = self.challenge_level + 1
        self.action_reset()
        self.challenge_original_maze = original_maze
        self.challenge_level = next_level
        self.maze = self._build_challenge_level_maze(original_maze, next_level)
        self._reset_maze_view()
        self.challenge_level_scores = run_scores
        self._layout_ui()
        self._configure_challenge_move_limit()
        self.challenge = HumanChallenge(self.maze)
        self.challenge.start()
        self.challenge_selected_view_path = "Human"
        self.state = "CHALLENGE_PLAYING"
        self.status_message = f"Level {next_level} of {self.challenge_level_count}: reach the goal!"

    def action_challenge_return_to_menu(self):
        """Exit challenge and return to standard IDLE solver interface."""
        original_maze = self.challenge_original_maze
        self.action_reset()
        if original_maze is not None:
            self.maze = original_maze
            self._layout_ui()
        self.state = "IDLE"
        self.status_message = "Ready to solve."

    def _on_challenge_victory(self):
        """Start one AI comparison after victory, off-thread for large mazes."""
        if not self.challenge or not self.challenge.is_won:
            return
        if self.challenge_comparison_attempted:
            return
        self.challenge_comparison_attempted = True
        self._set_gameplay_feedback("win")

        if self.maze.rows * self.maze.cols >= ASYNC_COMPARISON_CELL_THRESHOLD:
            challenge = self.challenge
            self.state = "CHALLENGE_COMPARING"
            self.comparison_worker.start(
                "challenge", challenge.compare_with_ai
            )
            return

        try:
            results = self.challenge.compare_with_ai()
            error = None
        except Exception as e:
            results = None
            error = str(e)
        self._complete_challenge_victory(results, error)

    def _challenge_comparison_fallback(self, error: str) -> Dict[str, Any]:
        challenge = self.challenge
        if challenge is None:
            return {"human": {}, "ai": {}, "optimality_ratio": None, "error": error}
        return {
            "human": {
                "path_length": challenge.move_count,
                "human_path_length": challenge.human_path_length,
                "move_count": challenge.move_count,
                "unique_cells_visited": challenge.unique_cells_visited,
                "elapsed_time": challenge.elapsed_time,
                "elapsed_time_s": challenge.elapsed_time,
                "path": list(challenge.path)
            },
            "ai": {},
            "optimality_ratio": None,
            "error": error
        }

    def _complete_challenge_victory(self, results, error: Optional[str]) -> None:
        if error:
            self.challenge_comparison_results = self._challenge_comparison_fallback(error)
        else:
            self.challenge_comparison_results = results
        self.challenge_selected_view_path = "Human"
        self.state = "CHALLENGE_RESULTS"
        score = self._calculate_level_score(self.challenge_comparison_results or {})
        self.challenge_level_scores[self.challenge_level] = score
        self.challenge_best_scores[self.challenge_level] = max(
            score, self.challenge_best_scores.get(self.challenge_level, 0)
        )
        if self.challenge_level < self.challenge_level_count:
            self.challenge_unlocked_level = max(self.challenge_unlocked_level, self.challenge_level + 1)
            self.challenge_campaign_completed = False
        else:
            self.challenge_unlocked_level = self.challenge_level_count
            self.challenge_campaign_completed = True
        self._save_challenge_progress()
        if self.challenge_unlocked_level > 1 and not self.challenge_campaign_completed:
            self.btn_challenge.text = f"Continue Level {self.challenge_unlocked_level}/{self.challenge_level_count}"
        else:
            self.btn_challenge.text = "Human vs AI Challenge"
        self._layout_ui()
        self.status_message = "Goal reached! Challenge completed."

    def _advance_generator_step(self):
        """Advance one generator step, accumulating pure algorithmic compute time."""
        if not self.generator:
            return
        try:
            t0 = time.perf_counter()
            state = next(self.generator)
            t_elapsed = time.perf_counter() - t0
            self.search_compute_time += t_elapsed
            self.execution_time_ms = self.search_compute_time * 1000.0

            self.current_cell = state['current']
            self.expanded_cells = state.get('expanded', state.get('visited', set()))
            self.frontier_cells = state.get('frontier', set())
            self.discovered_cells = state.get('discovered', self.expanded_cells | self.frontier_cells)
            self.nodes_expanded = state['nodes_expanded']
            
            if state['is_complete']:
                if state['found']:
                    self.final_path = state['path']
                    self.path_length = len(self.final_path) - 1 if len(self.final_path) > 1 else 0
                    self.state = "FINISHED"
                    self.btn_solve.text = "Solve Maze"
                    self.btn_solve.icon = "play"
                    self.status_message = "Path found successfully!"
                else:
                    self.state = "NO_PATH"
                    self.btn_solve.text = "Solve Maze"
                    self.btn_solve.icon = "play"
                    self.status_message = "No path exists between Start and Goal."
                self.generator = None
        except StopIteration:
            self.state = "FINISHED"
            self.btn_solve.text = "Solve Maze"
            self.btn_solve.icon = "play"
            self.generator = None

    # --- COORDINATE TRANSFORMS ---
    def _update_maze_view(self) -> None:
        """Recompute an integer-pixel grid origin and clamp its pan to the viewport."""
        cell_size = max(self._base_cell_size, int(round(self._base_cell_size * self.maze_zoom)))
        self.maze_cell_size = cell_size
        view = self.maze_viewport_rect
        grid_w, grid_h = self.maze.cols * cell_size, self.maze.rows * cell_size
        visible_cols = max(1, view.width // cell_size)
        visible_rows = max(1, view.height // cell_size)
        if grid_w <= view.width:
            self.maze_pan_x = 0
            grid_x = view.x + (view.width - grid_w) // 2
        else:
            self.maze_pan_x = max(0, min(self.maze.cols - visible_cols, int(self.maze_pan_x)))
            grid_x = view.x - self.maze_pan_x * cell_size
        if grid_h <= view.height:
            self.maze_pan_y = 0
            grid_y = view.y + (view.height - grid_h) // 2
        else:
            self.maze_pan_y = max(0, min(self.maze.rows - visible_rows, int(self.maze_pan_y)))
            grid_y = view.y - self.maze_pan_y * cell_size
        self.grid_area = pygame.Rect(grid_x, grid_y, grid_w, grid_h)

    def _reset_maze_view(self) -> None:
        self.maze_zoom = 1.0
        self.maze_pan_x = self.maze_pan_y = 0
        self._update_maze_view()

    def _zoom_maze_at(self, pos: Tuple[int, int], direction: int) -> bool:
        if not self.maze_viewport_rect.collidepoint(pos):
            return False
        levels = (1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0)
        old_index = min(range(len(levels)), key=lambda i: abs(levels[i] - self.maze_zoom))
        new_index = max(0, min(len(levels) - 1, old_index + (1 if direction > 0 else -1)))
        if new_index == old_index:
            return True
        old_cell = self.maze_cell_size
        cell_col = (pos[0] - self.grid_area.x) // old_cell
        cell_row = (pos[1] - self.grid_area.y) // old_cell
        old_zoom = self.maze_zoom
        self.maze_zoom = levels[new_index]
        new_cell = max(self._base_cell_size, int(round(self._base_cell_size * self.maze_zoom)))
        self.maze_pan_x = int(round((self.maze_viewport_rect.x + cell_col * new_cell - pos[0]) / new_cell))
        self.maze_pan_y = int(round((self.maze_viewport_rect.y + cell_row * new_cell - pos[1]) / new_cell))
        self._update_maze_view()
        return old_zoom != self.maze_zoom

    def _pan_maze_by(self, dx: int, dy: int) -> None:
        if self.maze_cell_size <= self._base_cell_size:
            return
        self.maze_pan_x -= int(round(dx / self.maze_cell_size))
        self.maze_pan_y -= int(round(dy / self.maze_cell_size))
        self._update_maze_view()

    def _get_cell_rect(self, r: int, c: int) -> pygame.Rect:
        cell_size = self.maze_cell_size
        x = self.grid_area.x + c * cell_size
        y = self.grid_area.y + r * cell_size
        return pygame.Rect(x, y, cell_size, cell_size)

    def _pos_to_cell(self, pos: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        px, py = pos
        if not self.maze_viewport_rect.collidepoint(px, py) or not self.grid_area.collidepoint(px, py):
            return None
        cell_size = self.maze_cell_size
        c = (px - self.grid_area.x) // cell_size
        r = (py - self.grid_area.y) // cell_size
        if 0 <= r < self.maze.rows and 0 <= c < self.maze.cols:
            return (r, c)
        return None

    # --- EVENT HANDLING ---
    def handle_events(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            # Responsive window resize
            if event.type == pygame.VIDEORESIZE:
                self.width = max(800, event.w)
                self.height = max(560, event.h)
                self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                self._init_fonts()
                self._layout_ui()
                continue

            if self.comparison_worker.pending:
                continue

            # View navigation uses integer-cell zoom and never changes maze coordinates.
            if self.state not in ["COMPARING", "MODAL_INFO", "MODAL_SETTINGS", "CHALLENGE_RESULTS", "CHALLENGE_PAUSED", "CHALLENGE_FAILED", "CHALLENGE_TUTORIAL", "CHALLENGE_RESET_CONFIRM"]:
                if event.type == pygame.MOUSEWHEEL:
                    pos = getattr(event, "pos", pygame.mouse.get_pos())
                    if self._zoom_maze_at(pos, event.y):
                        return True
                if event.type == pygame.MOUSEBUTTONDOWN and event.button in (2, 3) and self.maze_viewport_rect.collidepoint(event.pos):
                    self._maze_pan_drag = True
                    self._maze_pan_last_pos = event.pos
                    return True
                if event.type == pygame.MOUSEBUTTONUP and event.button in (2, 3):
                    self._maze_pan_drag = False
                    self._maze_pan_last_pos = None
                    continue
                if event.type == pygame.MOUSEMOTION and self._maze_pan_drag and self._maze_pan_last_pos:
                    dx = event.pos[0] - self._maze_pan_last_pos[0]
                    dy = event.pos[1] - self._maze_pan_last_pos[1]
                    self._pan_maze_by(dx, dy)
                    self._maze_pan_last_pos = event.pos
                    return True
                if event.type == pygame.KEYDOWN and event.key == pygame.K_0:
                    self._reset_maze_view()
                    return True

            # Active Modal Overlay Event Handling
            if self.state in ["COMPARING", "MODAL_INFO", "MODAL_SETTINGS", "CHALLENGE_RESULTS", "CHALLENGE_PAUSED", "CHALLENGE_FAILED", "CHALLENGE_TUTORIAL", "CHALLENGE_RESET_CONFIRM"]:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    if self.state == "CHALLENGE_RESULTS":
                        self.action_challenge_return_to_menu()
                    elif self.state == "CHALLENGE_PAUSED":
                        self.action_resume_challenge()
                    elif self.state == "CHALLENGE_FAILED":
                        self.action_challenge_return_to_menu()
                    elif self.state == "CHALLENGE_TUTORIAL":
                        self.action_close_challenge_tutorial()
                    elif self.state == "CHALLENGE_RESET_CONFIRM":
                        self.action_close_new_campaign_confirmation()
                    else:
                        self.close_modal()
                    return True
                if self.state == "CHALLENGE_PAUSED":
                    if event.type == pygame.KEYDOWN and event.key in (pygame.K_p, pygame.K_SPACE):
                        self.action_resume_challenge()
                        return True
                    if self.btn_challenge_resume.handle_event(event):
                        return True
                    if self.btn_challenge_retry.handle_event(event):
                        return True
                    if self.btn_challenge_menu.handle_event(event):
                        return True
                    continue
                if self.state == "CHALLENGE_FAILED":
                    if self.btn_challenge_retry.handle_event(event):
                        return True
                    if self.btn_challenge_menu.handle_event(event):
                        return True
                    continue
                if self.state == "CHALLENGE_TUTORIAL":
                    if self.btn_tutorial_start.handle_event(event):
                        return True
                    if self.btn_tutorial_close.handle_event(event):
                        return True
                    continue
                if self.state == "CHALLENGE_RESET_CONFIRM":
                    if self.btn_confirm_new_campaign.handle_event(event):
                        return True
                    if self.btn_cancel_new_campaign.handle_event(event):
                        return True
                    continue
                if self.state == "CHALLENGE_RESULTS":
                    if self.challenge_level < self.challenge_level_count:
                        if self.btn_challenge_next_level.handle_event(event):
                            return True
                    elif self.btn_challenge_play_again.handle_event(event):
                        return True
                    if self.btn_challenge_menu.handle_event(event):
                        return True
                    if self.btn_view_human.handle_event(event):
                        return True
                    if self.btn_view_bfs.handle_event(event):
                        return True
                    if self.btn_view_dfs.handle_event(event):
                        return True
                    if self.btn_view_astar.handle_event(event):
                        return True
                    continue
                if self.btn_modal_close.handle_event(event):
                    return True
                if self.state == "MODAL_SETTINGS":
                    if self.btn_modal_load.handle_event(event):
                        return True
                    if self.btn_modal_samples.handle_event(event):
                        return True
                    if self.btn_maze_export.handle_event(event):
                        return True
                    if self.btn_audio_toggle.handle_event(event):
                        return True
                    if self.btn_volume_down.handle_event(event):
                        return True
                    if self.btn_volume_up.handle_event(event):
                        return True
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_l:
                            self.action_load_custom_file()
                            return True
                        elif event.key == pygame.K_m:
                            self.action_load_sample_maze()
                            return True
                continue

            # Dedicated Challenge Mode Gameplay Event Handling
            if self.state == "CHALLENGE_PLAYING":
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_p, pygame.K_SPACE):
                        self.action_pause_challenge()
                        return True
                    if event.key == pygame.K_h:
                        self.action_show_challenge_hint()
                        return True
                    dr, dc = 0, 0
                    if event.key in (pygame.K_UP, pygame.K_w):
                        dr, dc = -1, 0
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        dr, dc = 1, 0
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        dr, dc = 0, -1
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        dr, dc = 0, 1

                    if dr != 0 or dc != 0:
                        if self.challenge:
                            next_cell = (self.challenge.player_pos[0] + dr, self.challenge.player_pos[1] + dc)
                            if (self.challenge_move_limit is not None and
                                    self.challenge.move_count >= self.challenge_move_limit and
                                    self.maze.is_walkable(*next_cell)):
                                self.challenge.fail()
                                self.state = "CHALLENGE_FAILED"
                                self._set_gameplay_feedback("fail")
                                return True
                            moved = self.challenge.move(dr, dc)
                            if moved:
                                self.challenge_last_progress_at = time.perf_counter()
                                self.challenge_blocked_attempts = 0
                                self.challenge_hint_auto_shown = False
                                self.challenge_hint_text = None
                                self.challenge_hint_until = 0.0
                                if self.challenge.is_won:
                                    self._on_challenge_victory()
                                else:
                                    self._set_gameplay_feedback("move")
                            else:
                                self._record_blocked_challenge_move()
                                self._set_gameplay_feedback("wall")
                        return True

                # Allow clicking Reset or Home to quit challenge
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.btn_challenge_hint.rect.collidepoint(event.pos):
                        self.action_show_challenge_hint()
                        return True
                    if self.btn_reset.rect.collidepoint(event.pos):
                        self.action_challenge_retry()
                        return True
                    for bname, rect in self.header_buttons.items():
                        if rect.collidepoint(event.pos) and bname == "home":
                            self.action_challenge_return_to_menu()
                            return True
                continue

            # Header Icon Buttons
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for bname, rect in self.header_buttons.items():
                    if rect.collidepoint(event.pos):
                        if bname == "home":
                            self.action_reset()
                            self.state = "IDLE"
                        elif bname == "stats":
                            self.action_compare_algorithms()
                        elif bname == "settings":
                            self.state = "MODAL_SETTINGS"
                        elif bname == "info":
                            self.state = "MODAL_INFO"
                        return True

            # Dropdown Event Handling (Top priority so open lists receive clicks)
            if self.dropdown_algo.handle_event(event):
                return True
            if self.dropdown_size.handle_event(event):
                return True

            # Checkbox Event Handling
            for cb in [self.cb_explored, self.cb_path, self.cb_animate, self.cb_heuristic]:
                if cb.handle_event(event):
                    return True

            # Control Buttons
            for btn in self.all_buttons:
                if btn.handle_event(event):
                    return True

            # Keyboard Shortcuts
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.action_solve_or_pause()
                elif event.key == pygame.K_r:
                    self.action_reset()
                elif event.key == pygame.K_n:
                    self.action_generate_maze()
                elif event.key == pygame.K_1:
                    self.dropdown_algo.selected_idx = 1
                    self.select_algorithm("BFS")
                elif event.key == pygame.K_2:
                    self.dropdown_algo.selected_idx = 2
                    self.select_algorithm("DFS")
                elif event.key == pygame.K_3:
                    self.dropdown_algo.selected_idx = 0
                    self.select_algorithm("A*")
                elif event.key == pygame.K_c:
                    self.action_compare_algorithms()
                elif event.key == pygame.K_l:
                    self.action_load_custom_file()
                elif event.key == pygame.K_m:
                    self.action_load_sample_maze()
                elif event.key == pygame.K_UP:
                    if self.speed_index < len(self.speed_options) - 1:
                        self.speed_index += 1
                        self.speed_level = self.speed_options[self.speed_index]
                elif event.key == pygame.K_DOWN:
                    if self.speed_index > 0:
                        self.speed_index -= 1
                        self.speed_level = self.speed_options[self.speed_index]

            # Interactive Mouse Editing on Grid (Allowed when NOT running)
            if self.state in ["IDLE", "FINISHED", "NO_PATH"]:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    cell = self._pos_to_cell(event.pos)
                    if cell:
                        if cell == self.maze.start:
                            self.dragging_start = True
                        elif cell == self.maze.goal:
                            self.dragging_goal = True
                        else:
                            is_wall = self.maze.is_wall(cell[0], cell[1])
                            self.drawing_wall_mode = not is_wall
                            self.maze.set_wall(cell[0], cell[1], self.drawing_wall_mode)
                            self.action_reset()

                elif event.type == pygame.MOUSEMOTION:
                    cell = self._pos_to_cell(event.pos)
                    if cell:
                        if self.dragging_start:
                            if cell != self.maze.goal and not self.maze.is_wall(cell[0], cell[1]):
                                self.maze.set_start(cell[0], cell[1])
                                self.action_reset()
                        elif self.dragging_goal:
                            if cell != self.maze.start and not self.maze.is_wall(cell[0], cell[1]):
                                self.maze.set_goal(cell[0], cell[1])
                                self.action_reset()
                        elif self.drawing_wall_mode is not None:
                            if cell != self.maze.start and cell != self.maze.goal:
                                self.maze.set_wall(cell[0], cell[1], self.drawing_wall_mode)
                                self.action_reset()

                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.dragging_start = False
                    self.dragging_goal = False
                    self.drawing_wall_mode = None

        return True

    # --- UPDATE LOOP ---
    def update(self):
        """Advance animated search based on selected speed, or complete immediately if animation disabled."""
        self._poll_background_comparison()
        if self.state == "RUNNING":
            if self.animate_search:
                for _ in range(self.speed_level):
                    self._advance_generator_step()
                    if self.state != "RUNNING":
                        break
            else:
                # If animation is disabled while RUNNING, finish search immediately without getting stuck
                while self.state == "RUNNING" and self.generator:
                    self._advance_generator_step()
        if (self.state == "CHALLENGE_PLAYING" and self.challenge and
                not self.challenge_hint_auto_shown and
                time.perf_counter() - self.challenge_last_progress_at >= 25.0):
            self.action_show_challenge_hint(automatic=True)

    # --- DRAWING ROUTINES ---





    # --- MODAL WINDOW OVERLAYS ---









    def run(self):
        """Main Pygame execution loop."""
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)

        pygame.quit()
