"""
Maze representation and generation module.

Handles:
- Grid creation and representation
- Recursive Backtracker maze generation
- File loading and validation
- Start and Goal management
- Wall toggling and neighbor discovery
"""

import random
from collections import deque
from typing import List, Tuple, Optional, Set


class Maze:
    """
    Represents a 2D grid maze for pathfinding algorithms.
    
    Symbols:
        '#' : Wall
        '.' : Open / walkable cell
        'S' : Start position
        'G' : Goal position
    """

    WALL = '#'
    OPEN = '.'
    START = 'S'
    GOAL = 'G'

    def __init__(self, rows: int = 25, cols: int = 25):
        """
        Initialize a maze with given dimensions.
        Defaults to 25x25 grid. Minimum supported dimension is 2x2.
        """
        if rows < 2 or cols < 2:
            raise ValueError(f"Maze dimensions must be at least 2x2. Received: {rows}x{cols}")
        
        self.rows = rows
        self.cols = cols
        self.grid: List[List[str]] = [[self.OPEN for _ in range(cols)] for _ in range(rows)]
        
        # Position start and goal such that start != goal for any grid size
        if rows >= 5 and cols >= 5:
            self.start = (1, 1)
            self.goal = (rows - 2, cols - 2)
        else:
            self.start = (0, 0)
            self.goal = (rows - 1, cols - 1)
        
        # Ensure default positions are marked correctly
        self.grid[self.start[0]][self.start[1]] = self.START
        self.grid[self.goal[0]][self.goal[1]] = self.GOAL

    def is_valid(self, row: int, col: int) -> bool:
        """Check if coordinates lie within grid boundaries."""
        return 0 <= row < self.rows and 0 <= col < self.cols

    def is_wall(self, row: int, col: int) -> bool:
        """Check if cell at (row, col) is a wall or out-of-bounds boundary."""
        if not self.is_valid(row, col):
            return True
        return self.grid[row][col] == self.WALL

    def is_walkable(self, row: int, col: int) -> bool:
        """Check if cell is within bounds and not a wall."""
        if not self.is_valid(row, col):
            return False
        return self.grid[row][col] != self.WALL

    def get_neighbors(self, row: int, col: int) -> List[Tuple[int, int]]:
        """
        Return walkable orthogonal neighbors in standard order:
        Up, Down, Left, Right.
        """
        neighbors = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Up, Down, Left, Right
        for dr, dc in directions:
            nr, nc = row + dr, col + dc
            if self.is_walkable(nr, nc):
                neighbors.append((nr, nc))
        return neighbors

    def set_wall(self, row: int, col: int, is_wall: bool) -> bool:
        """
        Set or unset a wall at (row, col).
        Returns True if modified, False if position is invalid or protected (Start/Goal).
        """
        if not self.is_valid(row, col):
            return False
        if (row, col) == self.start or (row, col) == self.goal:
            return False  # Protect start and goal
        
        self.grid[row][col] = self.WALL if is_wall else self.OPEN
        return True

    def toggle_wall(self, row: int, col: int) -> bool:
        """
        Toggle wall state at (row, col).
        Returns True if toggled, False if cell is Start or Goal or out of bounds.
        """
        if not self.is_valid(row, col):
            return False
        if (row, col) == self.start or (row, col) == self.goal:
            return False
        
        if self.grid[row][col] == self.WALL:
            self.grid[row][col] = self.OPEN
        else:
            self.grid[row][col] = self.WALL
        return True

    def set_start(self, row: int, col: int) -> bool:
        """
        Set new start position.
        Must be within bounds and not equal to goal.
        """
        if not self.is_valid(row, col):
            return False
        if (row, col) == self.goal:
            return False
        
        # Clear old start
        old_r, old_c = self.start
        self.grid[old_r][old_c] = self.OPEN
        
        # Assign new start
        self.start = (row, col)
        self.grid[row][col] = self.START
        return True

    def set_goal(self, row: int, col: int) -> bool:
        """
        Set new goal position.
        Must be within bounds and not equal to start.
        """
        if not self.is_valid(row, col):
            return False
        if (row, col) == self.start:
            return False
        
        # Clear old goal
        old_r, old_c = self.goal
        self.grid[old_r][old_c] = self.OPEN
        
        # Assign new goal
        self.goal = (row, col)
        self.grid[row][col] = self.GOAL
        return True

    def clear(self):
        """Reset all cells to open, keeping start and goal."""
        self.grid = [[self.OPEN for _ in range(self.cols)] for _ in range(self.rows)]
        self.grid[self.start[0]][self.start[1]] = self.START
        self.grid[self.goal[0]][self.goal[1]] = self.GOAL

    def clone(self) -> 'Maze':
        """Create a deep copy of the maze."""
        new_maze = Maze(self.rows, self.cols)
        new_maze.grid = [row[:] for row in self.grid]
        new_maze.start = self.start
        new_maze.goal = self.goal
        return new_maze

    def has_solution(self) -> bool:
        """Quick BFS check to verify if a path exists between start and goal."""
        if not self.is_walkable(self.start[0], self.start[1]):
            return False
        if not self.is_walkable(self.goal[0], self.goal[1]):
            return False
        
        visited: Set[Tuple[int, int]] = {self.start}
        queue = deque([self.start])
        
        while queue:
            curr = queue.popleft()
            if curr == self.goal:
                return True
            for neighbor in self.get_neighbors(curr[0], curr[1]):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        return False

    def generate_random_maze(self, seed: Optional[int] = None):
        """
        Generate a random maze using the Recursive Backtracker algorithm.
        Guarantees that a path exists between Start and Goal.
        Requires dimensions of at least 5x5.
        Uses an isolated random.Random instance to prevent mutating global state.
        """
        if self.rows < 5 or self.cols < 5:
            raise ValueError(
                f"Procedural maze generation requires dimensions of at least 5x5. "
                f"Current dimensions: {self.rows}x{self.cols}. "
                "For smaller grids, please draw walls interactively or load a custom file."
            )

        rng = random.Random(seed)
        
        # Fill the entire grid with walls
        self.grid = [[self.WALL for _ in range(self.cols)] for _ in range(self.rows)]
        
        # Position start at (1, 1) and goal at (rows-2, cols-2)
        start_r = 1
        start_c = 1
        goal_r = self.rows - 2
        goal_c = self.cols - 2
        
        # Ensure coordinates are odd if possible for standard backtracker grid alignment
        if start_r % 2 == 0 and start_r + 1 < self.rows - 1:
            start_r += 1
        if start_c % 2 == 0 and start_c + 1 < self.cols - 1:
            start_c += 1
        if goal_r % 2 == 0 and goal_r - 1 > 0:
            goal_r -= 1
        if goal_c % 2 == 0 and goal_c - 1 > 0:
            goal_c -= 1
            
        self.start = (start_r, start_c)
        self.goal = (goal_r, goal_c)
        
        # Stack-based iterative Recursive Backtracker to handle any size without recursion limit
        stack = [(start_r, start_c)]
        visited_cells = {(start_r, start_c)}
        self.grid[start_r][start_c] = self.OPEN
        
        directions = [(-2, 0), (2, 0), (0, -2), (0, 2)]
        
        while stack:
            cr, cc = stack[-1]
            unvisited_neighbors = []
            
            for dr, dc in directions:
                nr, nc = cr + dr, cc + dc
                if 0 < nr < self.rows - 1 and 0 < nc < self.cols - 1:
                    if (nr, nc) not in visited_cells:
                        unvisited_neighbors.append((nr, nc, dr, dc))
            
            if unvisited_neighbors:
                nr, nc, dr, dc = rng.choice(unvisited_neighbors)
                # Carve wall between current and chosen neighbor
                self.grid[cr + dr // 2][cc + dc // 2] = self.OPEN
                # Carve chosen neighbor
                self.grid[nr][nc] = self.OPEN
                visited_cells.add((nr, nc))
                stack.append((nr, nc))
            else:
                stack.pop()
        
        # Carve goal cell and guarantee connection
        self.grid[self.goal[0]][self.goal[1]] = self.OPEN
        
        # If goal is not connected or isolated, connect it to the closest carved open cell
        if not self.has_solution():
            self._connect_cells(self.start, self.goal)
        
        # Add a few random openings (braiding) to create occasional alternative paths
        extra_openings = max(1, (self.rows * self.cols) // 60)
        for _ in range(extra_openings):
            rr = rng.randint(1, self.rows - 2)
            rc = rng.randint(1, self.cols - 2)
            if self.grid[rr][rc] == self.WALL:
                # Open cell if it connects two corridors
                horiz = (self.grid[rr][rc - 1] == self.OPEN and self.grid[rr][rc + 1] == self.OPEN)
                vert = (self.grid[rr - 1][rc] == self.OPEN and self.grid[rr + 1][rc] == self.OPEN)
                if horiz or vert:
                    self.grid[rr][rc] = self.OPEN
        
        # Restore Start and Goal symbols
        self.grid[self.start[0]][self.start[1]] = self.START
        self.grid[self.goal[0]][self.goal[1]] = self.GOAL

    def _connect_cells(self, src: Tuple[int, int], dst: Tuple[int, int]):
        """Carve a simple L-shaped or direct path to guarantee connectivity."""
        r, c = src
        gr, gc = dst
        # Carve row path
        step_r = 1 if gr >= r else -1
        for cr in range(r, gr + step_r, step_r):
            self.grid[cr][c] = self.OPEN
        # Carve column path
        step_c = 1 if gc >= c else -1
        for cc in range(c, gc + step_c, step_c):
            self.grid[gr][cc] = self.OPEN

    def load_from_file(self, filepath: str):
        """
        Load maze from a text file.
        
        Validation rules:
        - Non-empty file
        - Dimensions at least 2x2
        - All rows must have equal length
        - Only valid characters: '#', '.', 'S', 'G'
        - Exactly one 'S' (Start)
        - Exactly one 'G' (Goal)
        
        Raises ValueError with a clear explanation if invalid.
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = [line.rstrip('\r\n') for line in f if line.strip() != '']
        except Exception as e:
            raise ValueError(f"Could not read file '{filepath}': {e}")
        
        if not lines:
            raise ValueError("Maze file is empty.")
        
        num_rows = len(lines)
        num_cols = len(lines[0])
        
        if num_rows < 2 or num_cols < 2:
            raise ValueError(f"Maze dimensions must be at least 2x2. Found: {num_rows}x{num_cols}.")
        
        start_count = 0
        goal_count = 0
        start_pos = None
        goal_pos = None
        valid_chars = {self.WALL, self.OPEN, self.START, self.GOAL}
        
        new_grid = []
        for r, line in enumerate(lines):
            if len(line) != num_cols:
                raise ValueError(
                    f"Row {r + 1} has length {len(line)}, expected {num_cols}. "
                    "All maze rows must have equal length."
                )
            row_chars = []
            for c, char in enumerate(line):
                if char not in valid_chars:
                    raise ValueError(
                        f"Invalid character '{char}' at row {r + 1}, column {c + 1}. "
                        "Allowed characters are '#', '.', 'S', 'G'."
                    )
                if char == self.START:
                    start_count += 1
                    start_pos = (r, c)
                elif char == self.GOAL:
                    goal_count += 1
                    goal_pos = (r, c)
                row_chars.append(char)
            new_grid.append(row_chars)
        
        if start_count != 1:
            raise ValueError(f"Maze must contain exactly one Start ('S'). Found: {start_count}.")
        if goal_count != 1:
            raise ValueError(f"Maze must contain exactly one Goal ('G'). Found: {goal_count}.")
        
        self.rows = num_rows
        self.cols = num_cols
        self.grid = new_grid
        self.start = start_pos  # type: ignore
        self.goal = goal_pos    # type: ignore

    def save_to_file(self, filepath: str):
        """Save the maze grid to a text file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            for row in self.grid:
                f.write(''.join(row) + '\n')

    def __repr__(self) -> str:
        return f"Maze({self.rows}x{self.cols}, start={self.start}, goal={self.goal})"
