# AI Maze Solver: Search Algorithm Visualization & Human vs AI Challenge

**Course:** Artificial Intelligence (Fall 2026–2027)  
**Institution:** Egyptian E-Learning University (EELU) — Faculty of Computers and Information Technology  
**Supervised By:** Dr. Mahmoud Bassiouni  
**Teaching Assistants:** Eng. George Hany, Eng. Basma Bassem  

An educational desktop application built with Python 3 and Pygame for the Artificial Intelligence course at the Egyptian E-Learning University (EELU). The application provides an interactive platform for graph traversal and heuristic search, supporting both **autonomous AI search algorithms** (BFS, DFS, A\*) with step-by-step visual exploration and a dedicated **Human vs AI Challenge Mode** allowing human players to solve mazes manually and compare their performance against AI benchmarks on identical maze snapshots.

---

## 1. Project Idea & Algorithms Used

Navigating an agent from a Start coordinate (`S`) to a Goal coordinate (`G`) through an obstacle grid is formulated as a four-connected unweighted graph search problem with unit step cost ($c = 1$):

- **Breadth-First Search (BFS)**: Uninformed FIFO queue search (`collections.deque`) performing $O(1)$ amortized operations; explores level by level (wavefront expansion) and mathematically guarantees the shortest-path optimality on unweighted grids. BFS serves as the authoritative ground truth for path optimality across the application.
- **Depth-First Search (DFS)**: Uninformed LIFO stack search (`list`) exploring deeply along individual branches before backtracking; complete on finite graphs with visited state hashing, but does not guarantee an optimal or shortest path.
- **A\* Search**: Informed best-first search using a min-heap priority queue (`heapq`, $O(\log V)$ per `heappush`/`heappop`) ordered by the evaluation function $f(n) = g(n) + h(n)$, where $g(n)$ is the exact step cost from Start and $h(n)$ is the admissible Manhattan distance heuristic ($|r_1 - r_2| + |c_1 - c_2|$). Guarantees shortest-path optimality under admissible heuristics while expanding fewer nodes on open topologies.

---

## 2. Core Features & Architecture

- **Autonomous Search Visualization**: Interactive step-by-step animated wavefront visualization powered by non-blocking Python generators (`yield`), with configurable playback speed ($1\times$ to $50\times$), real-time telemetry, and visual exploration toggles (Explored Nodes, Frontier, Final Path, Manhattan Heuristic numbers).
- **Human vs AI Challenge Mode (`challenge.py`)**: A decoupled domain engine allowing human players to navigate the maze manually using Arrow keys or WASD, with wall/boundary collision rejection, high-resolution monotonic timer tracking, and live telemetry.
- **AI Comparison Dashboard**: Upon reaching the Goal, the challenge engine executes BFS, DFS, and A\* across independent deep clones of the identical maze snapshot. Comparisons on grids of at least 1,600 cells run in the background; results are applied by the Pygame event loop.
- **Multi-Path Maze Inspection**: Post-challenge visual overlay allowing players to toggle and inspect their exact movement path against the BFS optimal path, DFS exploratory trajectory, and A\* heuristic path directly on the grid.
- **Procedural Maze Generation (`maze.py`)**: Iterative Stack-based Recursive Backtracker (Randomized Depth-First Search) guaranteeing solvability, border integrity, and cycle control without recursion limit overflow.
- **Interactive Grid Editing**: Real-time obstacle placement/erasure via mouse click/drag, draggable Start (`S`) and Goal (`G`) markers, and sample maze file loading.
- **Technology Stack (`requirements.txt`)**: Python 3.10+ (verified on 3.11.2 / 3.12.7), `pygame>=2.5.0` (GUI, input, rendering), `pytest>=8.0.0` (automated testing), and standard library modules (`collections.deque`, `heapq`, `random`, `time.perf_counter`, `statistics`, `argparse`).

---

## 3. Human vs AI Challenge Experience

### Gameplay Flow
1. **Select Mode**: Click the prominent **"Human vs AI Challenge"** button on the control panel to enter the challenge arena.
2. **Manual Locomotion**: Navigate from Start (`S`) to Goal (`G`) using **Arrow Keys** or **WASD**.
3. **Collision & Rule Enforcement**: Movement attempts into walls (`#`) or outside boundaries are immediately rejected without penalty or timer arming.
4. **Monotonic Timing**: High-resolution timer (`time.perf_counter`) arms on the first legal move and freezes the instant the player steps onto the Goal.
5. **AI Benchmark Execution**: BFS, DFS, and A\* execute automatically on isolated clones of the identical maze to generate authoritative benchmark data.
6. **Results Dashboard**: Review side-by-side metrics comparing human navigation against AI algorithms in an adaptive, responsive modal.
7. **Inspect Paths**: Toggle between Human, BFS, DFS, and A\* paths on the maze grid to visually analyze route efficiency.
8. **Replay or Exit**: Click **"Play Again"** to retry the identical maze or **"Main Menu"** (or press `ESC`) to return to the solver interface.

### Performance Metrics & Mathematical Definitions

- **Human Path Length ($L_H$)**: Number of valid orthogonal transitions executed from Start to Goal:
  $$L_H = \text{move\_count} = \operatorname{len}(\text{path}) - 1$$
  The initial Start position is not counted as a move. When Start equals Goal, $L_H = 0$.
- **Human Unique Cells Visited ($V_H$)**: Total number of distinct grid coordinates entered:
  $$V_H = |\text{visited\_cells}|$$
- **Human Completion Time ($T_H$)**: Total real-world elapsed gameplay duration measured in seconds via `time.perf_counter()`. Reflects human reaction and physical keyboard navigation.
- **AI Nodes Expanded ($N_{\text{algo}}$)**: Total state graph nodes extracted from the frontier during search.
- **AI Compute Time ($T_{\text{algo}}$)**: Algorithmic CPU execution time measured in milliseconds (ms). Reflects pure graph traversal compute.
- **Human Optimality Ratio ($\Omega_H$)**: Efficiency ratio comparing human moves against the BFS authoritative shortest path length:
  $$\Omega_H = \begin{cases} 100.0\% & \text{if } L_H = 0 \text{ and } L_{\text{BFS}} = 0 \quad (\text{Start equals Goal edge case}) \\ \left(\frac{L_{\text{BFS}}}{L_H}\right) \times 100\% & \text{if } L_H > 0 \text{ and } L_{\text{BFS}} > 0 \quad (\text{Standard completed gameplay}) \\ \text{N/A} & \text{if BFS reference unavailable or comparison failed} \end{cases}$$
  - $L_H$: Human successful movement transitions ($L_H = \operatorname{len}(\text{path}) - 1$). The start cell is not counted as a move.
  - $L_{\text{BFS}}$: BFS optimal path length in valid transitions.
  - **BFS is the sole authoritative optimality reference**; A\* does not replace BFS as the reference.

> **Important Distinction:** Human completion time (seconds of manual gameplay) and AI compute time (milliseconds of CPU graph traversal) represent fundamentally different dimensions of elapsed time and are reported separately. Similarly, human unique cells visited ($V_H$) and AI search nodes expanded ($N_{\text{algo}}$) measure different exploration concepts and are not directly equated.

---

## 4. Controls & Shortcuts

| Context | Input / Key | Action |
| :--- | :--- | :--- |
| **Solver Mode** | `Space` | Start / Pause / Resume search animation |
| **Solver Mode** | `R` | Reset search state, visited overlays, and path |
| **Solver Mode** | `N` | Generate new random solvable maze |
| **Solver Mode** | `1` / `2` / `3` | Select Algorithm: `1` = BFS, `2` = DFS, `3` = A\* |
| **Solver Mode** | `C` | Open Algorithm Comparison modal |
| **Solver Mode** | `L` / `M` | Load custom file (`L`) / Load sample maze (`M`) |
| **Solver Mode** | `Up` / `Down` | Adjust animation speed ($1\times$ to $50\times$) |
| **Solver Mode** | `Mouse Drag` | Draw / erase walls (`#`) or drag Start (`S`) / Goal (`G`) |
| **Challenge Mode** | `Arrow Keys` | Move player: `Up`, `Down`, `Left`, `Right` |
| **Challenge Mode** | `W` / `A` / `S` / `D` | Alternative movement: `W` (Up), `A` (Left), `S` (Down), `D` (Right) |
| **Challenge Mode** | `Esc` | Cancel challenge and return to Main Menu |
| **Results Modal** | `Esc` | Close results modal and return to Main Menu |
| **Results Modal** | Path Buttons | Inspect path on grid: `Human`, `BFS`, `DFS`, `A*` |
| **Results Modal** | Action Buttons | `Play Again` (retry maze) or `Main Menu` (exit) |

---

## 5. Project Directory Tree

```text
maze_solver/
├── challenge.py                      # Human Challenge domain model (independent of Pygame)
├── comparison_worker.py              # Background worker for large-maze comparisons
├── DOCUMENTATION.md                  # Comprehensive academic technical documentation
├── DOCUMENTATION.pdf                 # Compiled academic documentation (PDF)
├── README.md                         # Project overview and quick-start guide
├── PHASE_6_ORAL_EXAM_PREPARATION.md  # Comprehensive bilingual oral defense guide
├── benchmark.py                      # Multi-size empirical benchmark suite
├── main.py                           # CLI entry point and application launcher
├── maze.py                           # Maze representation, validation, and generation
├── requirements.txt                  # Python package dependencies (pygame, pytest)
├── run.bat                           # Windows automated setup and launcher
├── ui.py                             # Pygame graphical interface and challenge UI
├── algorithms/
│   ├── __init__.py                   # Algorithm package exports
│   ├── astar.py                      # A* Search with Manhattan heuristic
│   ├── bfs.py                        # Breadth-First Search (authoritative optimality)
│   └── dfs.py                        # Depth-First Search (deep exploration)
├── mazes/
│   ├── sample1.txt                   # 15x15 standard academic maze
│   ├── sample2.txt                   # 25x25 labyrinth maze
│   └── sample3.txt                   # 21x21 open obstacle maze
└── tests/
    ├── __init__.py                   # Test package marker
    ├── test_algorithms.py            # Core search algorithm correctness tests
    ├── test_challenge_mode.py        # Human Challenge Core lifecycle & metrics tests
    ├── test_challenge_ui.py          # Challenge Pygame UI integration & reliability tests
    ├── test_differential_3000.py     # Differential maze validation
    ├── test_edge_cases.py            # Edge cases, boundaries, and 100x100 stress tests
    ├── test_generation_1000.py       # Deterministic maze generation validation
    ├── test_phase2_regression.py     # CLI and boundary regression tests
    ├── test_ui.py                    # Pygame UI initialization tests
    └── test_ui_interactions.py       # UI state transitions & interaction tests
```

---

## 6. Installation & Execution Guide

### 1. Windows Quick Setup (Automated)
Double-click `run.bat` or run:
```cmd
run.bat
```
*(Automatically creates `.venv`, installs `requirements.txt`, and launches the application.)*

### 2. Manual Virtual Environment Setup (All Platforms)
```bash
# Create and activate virtual environment
python -m venv .venv

# Windows (Command Prompt):
.venv\Scripts\activate.bat
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# Install dependencies
python -m pip install -r requirements.txt
```

### 3. Launching the Application
```bash
# Run interactive Pygame UI with default dimensions (25x25):
python main.py

# Run with custom grid dimensions:
python main.py --rows 31 --cols 31

# Load a specific maze file on startup:
python main.py --maze mazes/sample1.txt
python main.py --maze mazes/sample2.txt
python main.py --maze mazes/sample3.txt

# Run multi-size empirical benchmark suite without launching UI:
python main.py --benchmark
# or directly:
python benchmark.py
```

### 4. Running the Automated Test Suite
```bash
# Standard test execution:
python -m pytest tests -v

# Headless execution with SDL dummy video/audio drivers:
# Windows (CMD):
set SDL_VIDEODRIVER=dummy&& set SDL_AUDIODRIVER=dummy&& python -m pytest tests -v

# Windows (PowerShell):
$env:SDL_VIDEODRIVER="dummy"; $env:SDL_AUDIODRIVER="dummy"; python -m pytest tests -v

# Linux / macOS:
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -m pytest tests -v
```

---

## 7. Verified Testing & Benchmark Summary

### Current Automated Test Result (183 Tests)
The current source passes **183 tests across 9 test modules**, including after adding the background-comparison worker. The suite covers search correctness, challenge rules and metrics, Pygame UI behavior, maze generation, regression cases, and differential comparisons.

The 183/183 result is a test pass rate, not code coverage. Code coverage has not been independently measured.

### AI Comparison Benchmark Results
Pure search compute time of `compare_with_ai()` across representative maze sizes (isolated clones):

| Maze Size | Type / Topology | BFS Time | DFS Time | A\* Time | Previously Recorded Total Compute Time |
| :--- | :--- | ---: | ---: | ---: | ---: |
| **$15 \times 15$** | Standard Academic | 0.096 ms | 0.062 ms | 0.132 ms | **0.435 ms** |
| **$25 \times 25$** | Default Interactive | 0.274 ms | 0.221 ms | 0.320 ms | **0.918 ms** |
| **$30 \times 40$** | Large Aspect Ratio | 0.313 ms | 0.255 ms | 0.329 ms | **1.031 ms** |
| **$100 \times 100$** | Stress Test Grid | 2.785 ms | 2.236 ms | 5.070 ms | **11.596 ms** |

*Note: These are previously recorded benchmark measurements from Windows 11 x86_64, Python 3.12.7, using pure CPU timing (`time.perf_counter`). They are observations, not guaranteed latency or frame-rate limits; performance varies with maze topology, workload, and machine.*

**Independent audit observation:** On Windows 11 build 10.0.26300, Python 3.12.7, and Pygame 2.6.1, three complete Human vs AI comparisons on a 100×100 generated maze (seed 2026; BFS path length 404 transitions) took **21.184 ms, 19.197 ms, and 19.911 ms**. These measurements cover the comparison work, including clone checks and all three solver calls, in the earlier synchronous implementation. The current UI runs comparisons for grids of 1,600 cells or more on a background thread, then applies results on the Pygame main thread. Smaller grids remain synchronous. The background worker improves event-loop responsiveness for large grids, but it does not guarantee 60 FPS; Python execution and machine load can still affect frame timing.

---

## 8. Academic Team & Algorithmic Specializations

| Student Name | University ID | Algorithmic & Technical Domain | Key Implementation Scope |
| :--- | :---: | :--- | :--- |
| **Mohamed Hassan Sayed** | `2401354` | **Uninformed Optimal Search & FIFO Queues** | BFS implementation (`algorithms/bfs.py`), `collections.deque` $O(1)$ operations, authoritative shortest-path reference proofs, and predecessor pointer reconstruction. |
| **Mohamed Ragab Ahmed** | `2401355` | **Informed Search & Heuristic Formulation** | A\* Search implementation (`algorithms/astar.py`), `heapq` min-heap priority queue ($O(\log V)$), Manhattan distance admissibility and consistency proofs ($h \le h^*$), and tie-breaker mechanics. |
| **Moamen Hamouda Gaber** | `2401041` | **State-Space Modeling & Maze Generation** | State-space formulation, procedural maze generation via Iterative Stack-based Recursive Backtracker spanning trees, loop braiding, and solvability verification (`maze.py`). |
| **Abdallah Ashraf Farid** | `2401770` | **DFS Asymptotics & Step-by-Step Generators** | DFS implementation (`algorithms/dfs.py`), LIFO stack mechanics, linear space complexity $O(bm)$ vs $O(b^d)$, non-blocking Python generator pipeline (`yield`), and UI state machines. |
| **Ziad Ahmed AbdelSamee** | `2401040` | **Empirical Benchmarking & Challenge Engine** | Pure search timing (`benchmark.py`), Human Challenge Core lifecycle & clone isolation (`challenge.py`), statistical telemetry, and automated testing oracle across 3,000 mazes (`tests/`). |
