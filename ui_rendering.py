"""MazeUI drawing methods, separated from interaction and state logic."""

import time
import pygame

from algorithms.astar import manhattan_distance
from ui_components import draw_header_icon, draw_icon_maze_logo, draw_rounded_rect
from ui_theme import *  # noqa: F401,F403 - drawing methods share the interface palette


class UIRenderingMixin:
    def draw(self):
        """Render complete application display."""
        self.screen.fill(COLOR_MAIN_BG)

        # 1. Top Header
        self._draw_header()

        # 2. Left Column (Controls & Visualization Cards)
        self._draw_left_column()

        # 3. Center Column (Dominant Maze Panel)
        self._draw_maze_panel()

        # 4. Right Column (Algorithm Info, Results & Legend Cards)
        self._draw_right_column()

        # 5. Draw Open Dropdown Popups (Overlaid on top of everything)
        self.dropdown_size.draw_popup(self.screen, self.font_body_bold)
        self.dropdown_algo.draw_popup(self.screen, self.font_body_bold)

        # 6. Active Modals (If opened)
        if self.state == "COMPARING":
            self._draw_comparison_overlay()
        elif self.state == "CHALLENGE_COMPARING":
            self._draw_challenge_comparing_overlay()
        elif self.state == "MODAL_SETTINGS":
            self._draw_settings_modal()
        elif self.state == "MODAL_INFO":
            self._draw_info_modal()
        elif self.state == "CHALLENGE_RESULTS":
            self._draw_challenge_results_modal()
        elif self.state == "CHALLENGE_PAUSED":
            self._draw_challenge_pause_overlay()
        elif self.state == "CHALLENGE_FAILED":
            self._draw_challenge_failed_overlay()
        elif self.state == "CHALLENGE_TUTORIAL":
            self._draw_challenge_tutorial_modal()
        elif self.state == "CHALLENGE_RESET_CONFIRM":
            self._draw_new_campaign_confirmation()

        pygame.display.flip()
    def _draw_header(self):
        """Render the full-width modern top header."""
        pygame.draw.rect(self.screen, COLOR_HEADER_BG, self.header_rect)
        pygame.draw.line(self.screen, COLOR_CARD_BORDER, (0, self.header_rect.bottom),
                         (self.width, self.header_rect.bottom), 1)

        # Logo & App Title (Guaranteed >= 24px left margin)
        logo_x = 24 + 16
        draw_icon_maze_logo(self.screen, (logo_x, self.header_rect.centery), size=32)
        title_surf = self.font_logo.render("Maze Solver", True, COLOR_TEXT_PRIMARY)
        title_x = logo_x + 24
        self.screen.blit(title_surf, (title_x, self.header_rect.centery - title_surf.get_height() // 2))

        sub_surf = self.font_subtitle.render("Find the optimal path using AI search algorithms", True, COLOR_TEXT_SECONDARY)
        sub_x = title_x + title_surf.get_width() + 18
        first_btn_x = min(r.x for r in self.header_buttons.values()) if self.header_buttons else self.width
        if sub_x + sub_surf.get_width() < first_btn_x - 14:
            self.screen.blit(sub_surf, (sub_x, self.header_rect.centery - sub_surf.get_height() // 2))

        # Header Action Buttons (Right)
        mpos = pygame.mouse.get_pos()
        for bname, r in self.header_buttons.items():
            draw_header_icon(self.screen, bname, r, hovered=r.collidepoint(mpos))
    def _draw_left_column(self):
        """Render Left Column Cards: Controls & Visualization with AAA tactical styling."""
        # 1. Controls Card
        draw_rounded_rect(self.screen, COLOR_CARD_BG, self.card_controls_rect, radius=10,
                          border_color=COLOR_CARD_BORDER, border_width=1)
        pygame.draw.line(self.screen, COLOR_BRIGHT_CYAN,
                         (self.card_controls_rect.x + 14, self.card_controls_rect.y),
                         (self.card_controls_rect.x + 55, self.card_controls_rect.y), 2)
        
        # Header with icon
        px = self.card_controls_rect.x + 14
        py = self.card_controls_rect.y + 12
        pygame.draw.circle(self.screen, COLOR_ELECTRIC_BLUE, (px + 6, py + 8), 5, width=2)
        pygame.draw.circle(self.screen, COLOR_BRIGHT_CYAN, (px + 6, py + 8), 2)
        title1 = self.font_section.render("Controls", True, COLOR_TEXT_PRIMARY)
        self.screen.blit(title1, (px + 18, py))

        # Labels
        lbl_algo = self.font_label_bold.render("Algorithm", True, COLOR_BRIGHT_CYAN)
        self.screen.blit(lbl_algo, (px, self.dropdown_algo.rect.y - 19))
        self.dropdown_algo.draw_closed(self.screen, self.font_body_bold)

        lbl_size = self.font_label_bold.render("Maze Size", True, COLOR_BRIGHT_CYAN)
        self.screen.blit(lbl_size, (px, self.dropdown_size.rect.y - 19))
        self.dropdown_size.draw_closed(self.screen, self.font_body_bold)

        # Action Buttons
        self.btn_solve.draw(self.screen, self.font_body_bold)
        self.btn_reset.draw(self.screen, self.font_body_bold)
        self.btn_generate.draw(self.screen, self.font_body_bold)
        self.btn_challenge.draw(self.screen, self.font_body_bold)
        if self.state == "CHALLENGE_PLAYING":
            self.btn_challenge_hint.rect = pygame.Rect(
                self.btn_challenge_tutorial.rect.x, self.btn_challenge_tutorial.rect.y,
                self.btn_challenge_tutorial.rect.width + 8 + self.btn_difficulty.rect.width,
                self.btn_challenge_tutorial.rect.height,
            )
            self.btn_challenge_hint.draw(self.screen, self.font_body_bold)
        else:
            self.btn_challenge_tutorial.draw(self.screen, self.font_body_bold)
            self.btn_difficulty.draw(self.screen, self.font_small)
        if self.btn_new_campaign.rect.width > 0:
            self.btn_new_campaign.draw(self.screen, self.font_body_bold)

        # 2. Visualization Card
        draw_rounded_rect(self.screen, COLOR_CARD_BG, self.card_vis_rect, radius=10,
                          border_color=COLOR_CARD_BORDER, border_width=1)
        pygame.draw.line(self.screen, COLOR_BRIGHT_CYAN,
                         (self.card_vis_rect.x + 14, self.card_vis_rect.y),
                         (self.card_vis_rect.x + 55, self.card_vis_rect.y), 2)
        
        # Header with monitor icon
        vx = self.card_vis_rect.x + 14
        vy = self.card_vis_rect.y + 12
        pygame.draw.rect(self.screen, COLOR_ELECTRIC_BLUE, (vx, vy + 3, 13, 9), width=1)
        pygame.draw.line(self.screen, COLOR_BRIGHT_CYAN, (vx + 4, vy + 12), (vx + 9, vy + 12), 2)
        title2 = self.font_section.render("Visualization", True, COLOR_TEXT_PRIMARY)
        self.screen.blit(title2, (vx + 18, vy))

        # Checkboxes
        self.cb_explored.draw(self.screen, self.font_body_bold)
        self.cb_path.draw(self.screen, self.font_body_bold)
        self.cb_animate.draw(self.screen, self.font_body_bold)
        self.cb_heuristic.draw(self.screen, self.font_body_bold)
    def _draw_maze_panel(self):
        """Render the dominant central maze panel and the interactive grid."""
        draw_rounded_rect(self.screen, COLOR_PANEL_BG, self.maze_panel_rect, radius=14,
                          border_color=COLOR_CARD_BORDER, border_width=1)

        # Inset container behind the maze tiles
        view = self.maze_viewport_rect
        pygame.draw.rect(self.screen, COLOR_GRID_BACKING, view.inflate(14, 14), border_radius=10)
        pygame.draw.rect(self.screen, (62, 68, 80), view.inflate(14, 14), width=1, border_radius=10)

        # Tactical cyber corner brackets around the maze frame
        m_box = view.inflate(18, 18)
        col_bracket = (110, 150, 190)
        bw = 14
        pygame.draw.line(self.screen, col_bracket, (m_box.left, m_box.top), (m_box.left + bw, m_box.top), 2)
        pygame.draw.line(self.screen, col_bracket, (m_box.left, m_box.top), (m_box.left, m_box.top + bw), 2)
        pygame.draw.line(self.screen, col_bracket, (m_box.right, m_box.top), (m_box.right - bw, m_box.top), 2)
        pygame.draw.line(self.screen, col_bracket, (m_box.right, m_box.top), (m_box.right, m_box.top + bw), 2)
        pygame.draw.line(self.screen, col_bracket, (m_box.left, m_box.bottom), (m_box.left + bw, m_box.bottom), 2)
        pygame.draw.line(self.screen, col_bracket, (m_box.left, m_box.bottom), (m_box.left, m_box.bottom - bw), 2)
        pygame.draw.line(self.screen, col_bracket, (m_box.right, m_box.bottom), (m_box.right - bw, m_box.bottom), 2)
        pygame.draw.line(self.screen, col_bracket, (m_box.right, m_box.bottom), (m_box.right, m_box.bottom - bw), 2)

        previous_clip = self.screen.get_clip()
        self.screen.set_clip(view)

        # Pre-calculate set for fast path lookup
        path_set = set(self.final_path) if (self.final_path and self.show_final_path) else set()
        cell_size = self.maze_cell_size
        
        # Keep small cells drawable; reserve rounded insets and wall edges for larger tiles.
        tile_gap, corner_rad, draw_wall_edges = self._tile_style(cell_size)

        # Render Grid Cells as modular rounded tiles
        first_col = max(0, (view.left - self.grid_area.left) // cell_size)
        last_col = min(self.maze.cols, (view.right - 1 - self.grid_area.left) // cell_size + 1)
        first_row = max(0, (view.top - self.grid_area.top) // cell_size)
        last_row = min(self.maze.rows, (view.bottom - 1 - self.grid_area.top) // cell_size + 1)
        for r in range(first_row, last_row):
            for c in range(first_col, last_col):
                rect = self._get_cell_rect(r, c)
                tile = self._tile_rect(rect, tile_gap)
                coord = (r, c)
                is_wall = self.maze.is_wall(r, c)

                # Color resolution by visual priority
                if coord == self.maze.start:
                    color = COLOR_START
                elif coord == self.maze.goal:
                    color = COLOR_GOAL
                elif coord == self.current_cell and self.state == "RUNNING":
                    color = COLOR_CURRENT
                elif coord in self.frontier_cells and self.show_explored_nodes:
                    color = COLOR_FRONTIER
                elif (coord in self.expanded_cells or (coord in path_set and self.show_final_path)) and self.show_explored_nodes:
                    color = COLOR_EXPLORED
                elif is_wall:
                    color = COLOR_WALL
                else:
                    color = COLOR_OPEN

                # Modular tile drawing
                pygame.draw.rect(self.screen, color, tile, border_radius=corner_rad)
                if is_wall and draw_wall_edges:
                    pygame.draw.rect(self.screen, COLOR_WALL_EDGE, tile, width=1, border_radius=corner_rad)

                # Manhattan Heuristic (h) Number Display (if enabled)
                if self.show_heuristic and self.selected_algo == "A*" and cell_size >= 20 and not self.maze.is_wall(r, c) and coord not in (self.maze.start, self.maze.goal):
                    h_val = manhattan_distance(coord, self.maze.goal)
                    h_surf = self.font_small.render(str(h_val), True, (170, 180, 195))
                    self.screen.blit(h_surf, h_surf.get_rect(center=tile.center))

        # Prominent Path Overlay connecting cell centers (drawn before Start and Goal)
        path_to_render = None
        path_color = COLOR_PATH

        if self.state == "CHALLENGE_RESULTS":
            if self.challenge_selected_view_path == "Human" and self.challenge:
                path_to_render = self.challenge.path
                path_color = (0, 245, 255)
            elif self.challenge_comparison_results and "ai" in self.challenge_comparison_results:
                ai_dict = self.challenge_comparison_results["ai"].get(self.challenge_selected_view_path)
                if ai_dict and ai_dict.get("found"):
                    path_to_render = ai_dict.get("path")
                    path_color = COLOR_PATH
        elif self.final_path and self.show_final_path and len(self.final_path) > 1:
            path_to_render = self.final_path
            path_color = COLOR_PATH

        if path_to_render and len(path_to_render) > 1:
            pts = [self._get_cell_rect(r, c).center for r, c in path_to_render]
            line_w = self._path_width(cell_size)
            half = line_w // 2
            for i in range(len(pts) - 1):
                p1, p2 = pts[i], pts[i + 1]
                x1, y1 = min(p1[0], p2[0]), min(p1[1], p2[1])
                x2, y2 = max(p1[0], p2[0]), max(p1[1], p2[1])
                if p1[1] == p2[1]:  # Horizontal segment
                    pygame.draw.rect(self.screen, path_color, (x1 - half, y1 - half, (x2 - x1) + line_w, line_w))
                else:  # Vertical segment
                    pygame.draw.rect(self.screen, path_color, (x1 - half, y1 - half, line_w, (y2 - y1) + line_w))
            for pt in pts:
                pygame.draw.circle(self.screen, path_color, pt, half)

        # Draw Start Marker 'S' cleanly on top
        s_rect = self._tile_rect(self._get_cell_rect(*self.maze.start), tile_gap)
        pygame.draw.rect(self.screen, COLOR_START, s_rect, border_radius=corner_rad)
        marker_font = self._marker_font(cell_size)
        if marker_font is not None:
            lbl_s = marker_font.render("S", True, (255, 255, 255))
            self.screen.blit(lbl_s, lbl_s.get_rect(center=s_rect.center))

        # Draw Goal Marker 'G' cleanly on top
        g_rect = self._tile_rect(self._get_cell_rect(*self.maze.goal), tile_gap)
        pygame.draw.rect(self.screen, COLOR_GOAL, g_rect, border_radius=corner_rad)
        if marker_font is not None:
            lbl_g = marker_font.render("G", True, (255, 255, 255))
            self.screen.blit(lbl_g, lbl_g.get_rect(center=g_rect.center))

        # Challenge Mode Avatar and Breadcrumbs during active play
        if self.state in ("CHALLENGE_PLAYING", "CHALLENGE_PAUSED", "CHALLENGE_FAILED") and self.challenge:
            # Subtle breadcrumbs for visited path
            if len(self.challenge.path) > 1:
                # A player may revisit cells; render one breadcrumb per unique cell.
                breadcrumb_cells = set(self.challenge.path[:-1])
                breadcrumb_size = self._breadcrumb_size(cell_size)
                for r, c in breadcrumb_cells:
                    if (r, c) != self.maze.start and (r, c) != self.maze.goal:
                        c_rect = self._get_cell_rect(r, c)
                        if breadcrumb_size <= 1:
                            crumb_rect = self._centered_rect(c_rect, breadcrumb_size)
                            pygame.draw.rect(self.screen, COLOR_BREADCRUMB, crumb_rect)
                        else:
                            crumb_radius = breadcrumb_size // 2
                            pygame.draw.circle(self.screen, COLOR_BREADCRUMB, c_rect.center, crumb_radius)

            # Tactical player avatar
            pr, pc = self.challenge.player_pos
            p_rect = self._get_cell_rect(pr, pc)
            center = p_rect.center
            avatar_kind, avatar_measure = self._avatar_style(cell_size)
            if avatar_kind == "pixel":
                pygame.draw.rect(self.screen, COLOR_HUMAN_PATH, self._centered_rect(p_rect, avatar_measure))
            elif avatar_kind == "compact":
                avatar_rect = self._centered_rect(p_rect, avatar_measure)
                pygame.draw.rect(self.screen, COLOR_HUMAN_PATH, avatar_rect)
                if avatar_measure >= 3:
                    pygame.draw.rect(self.screen, (255, 255, 255), self._centered_rect(avatar_rect, 1))
            else:
                radius = avatar_measure
                pygame.draw.circle(self.screen, COLOR_HUMAN_PATH, center, radius)
                pygame.draw.circle(self.screen, COLOR_PLAYER_CORE, center, max(1, int(radius * 0.62)))
                pygame.draw.circle(self.screen, (255, 255, 255), center, max(0, int(radius * 0.28)))

            if time.perf_counter() < self.challenge_feedback_until:
                feedback_colors = {
                    "move": COLOR_BRIGHT_CYAN,
                    "wall": COLOR_GOAL,
                    "fail": COLOR_GOAL,
                    "win": COLOR_START,
                }
                feedback_color = feedback_colors.get(self.challenge_feedback_kind)
                if feedback_color:
                    if cell_size >= 4:
                        edge_rect = p_rect.inflate(-2, -2)
                        pygame.draw.rect(self.screen, feedback_color, edge_rect, width=1)
                    else:
                        pygame.draw.rect(
                            self.screen, feedback_color,
                            pygame.Rect(p_rect.right - 1, p_rect.top, 1, 1)
                        )

        self.screen.set_clip(previous_clip)
        if self.maze_zoom > 1.0:
            hint = self.font_tiny.render(
                f"{self.maze.cols}×{self.maze.rows} · {self.maze_zoom:g}x | Wheel zoom | Right-drag pan",
                True, COLOR_TEXT_SECONDARY,
            )
            self.screen.blit(hint, (view.x + 6, view.bottom - hint.get_height() - 5))
    def _draw_right_column(self):
        """Render Right Column: Algorithm Info, Results, and Legend Cards with AAA telemetry."""
        # 1. Algorithm Info Card
        draw_rounded_rect(self.screen, COLOR_CARD_BG, self.card_info_rect, radius=10,
                          border_color=COLOR_CARD_BORDER, border_width=1)
        pygame.draw.line(self.screen, COLOR_BRIGHT_CYAN,
                         (self.card_info_rect.x + 14, self.card_info_rect.y),
                         (self.card_info_rect.x + 55, self.card_info_rect.y), 2)
        
        ix = self.card_info_rect.x + 14
        iy = self.card_info_rect.y + 12
        # Stack layers icon
        pygame.draw.line(self.screen, COLOR_ELECTRIC_BLUE, (ix, iy + 6), (ix + 6, iy + 2), 2)
        pygame.draw.line(self.screen, COLOR_ELECTRIC_BLUE, (ix + 6, iy + 2), (ix + 12, iy + 6), 2)
        pygame.draw.line(self.screen, COLOR_ELECTRIC_BLUE, (ix + 12, iy + 6), (ix + 6, iy + 10), 2)
        pygame.draw.line(self.screen, COLOR_ELECTRIC_BLUE, (ix + 6, iy + 10), (ix, iy + 6), 2)
        title1 = self.font_section.render("Algorithm Info", True, COLOR_TEXT_PRIMARY)
        self.screen.blit(title1, (ix + 18, iy))

        # Dynamic Algorithm Title & Description
        if self.state == "CHALLENGE_PLAYING":
            algo_title = f"Challenge — Level {self.challenge_level}/{self.challenge_level_count}"
            if self.challenge_hint_text and time.perf_counter() < self.challenge_hint_until:
                desc_text = f"Hint: {self.challenge_hint_text}"
            else:
                desc_text = "Arrow keys/WASD move. Press H or click Hint for a one-step route nudge."
                if self.challenge_move_limit is not None:
                    desc_text += f" Move budget: {self.challenge_move_limit}."
        else:
            algo_titles = {
                "A*": "A* (A-Star)",
                "BFS": "BFS (Breadth-First Search)",
                "DFS": "DFS (Depth-First Search)"
            }
            algo_descs = {
                "A*": "An informed search algorithm that uses a heuristic function to find the shortest path efficiently.",
                "BFS": "An uninformed search algorithm exploring level-by-level using a FIFO queue. Guarantees the shortest path.",
                "DFS": "A search algorithm exploring deeply before backtracking using a stack. Does not guarantee the shortest path."
            }
            algo_title = algo_titles.get(self.selected_algo, self.selected_algo)
            desc_text = algo_descs.get(self.selected_algo, "")

        at_surf = self.font_algo_title.render(algo_title, True, COLOR_BRIGHT_CYAN)
        self.screen.blit(at_surf, (ix, iy + 28))

        # Word wrap description
        words = desc_text.split()
        lines = []
        cur_line = ""
        max_w = self.card_info_rect.width - 28
        for w in words:
            test = cur_line + (" " if cur_line else "") + w
            if self.font_desc.size(test)[0] <= max_w:
                cur_line = test
            else:
                lines.append(cur_line)
                cur_line = w
        if cur_line:
            lines.append(cur_line)

        dy = iy + 52
        for line in lines[:4]:
            ls = self.font_desc.render(line, True, COLOR_TEXT_PRIMARY)
            self.screen.blit(ls, (ix, dy))
            dy += 21

        # 2. Results Card
        draw_rounded_rect(self.screen, COLOR_CARD_BG, self.card_results_rect, radius=10,
                          border_color=COLOR_CARD_BORDER, border_width=1)
        pygame.draw.line(self.screen, COLOR_BRIGHT_CYAN,
                         (self.card_results_rect.x + 14, self.card_results_rect.y),
                         (self.card_results_rect.x + 55, self.card_results_rect.y), 2)
        
        rx = self.card_results_rect.x + 14
        ry = self.card_results_rect.y + 12
        # Bar chart icon
        pygame.draw.rect(self.screen, COLOR_ELECTRIC_BLUE, (rx, ry + 6, 3, 6))
        pygame.draw.rect(self.screen, COLOR_ELECTRIC_BLUE, (rx + 5, ry + 2, 3, 10))
        pygame.draw.rect(self.screen, COLOR_ELECTRIC_BLUE, (rx + 10, ry + 4, 3, 8))
        title2 = self.font_section.render("Results", True, COLOR_TEXT_PRIMARY)
        self.screen.blit(title2, (rx + 18, ry))

        # 4 Standard Rows matching reference image
        if self.state == "CHALLENGE_PLAYING" and self.challenge:
            res_rows = [
                ("stopwatch", "Moves (Path):", f"{self.challenge.move_count}"),
                ("grid", "Cells Visited:", f"{self.challenge.unique_cells_visited}"),
                ("clock", "Elapsed Time:", f"{self.challenge.elapsed_time:.1f} s"),
                ("trophy", "Result:", "Playing")
            ]
        else:
            res_rows = [
                ("stopwatch", "Path Length:", f"{self.path_length}" if self.final_path else "--"),
                ("grid", "Nodes Explored:", f"{self.nodes_expanded}"),
                ("clock", "Execution Time:", f"{self.execution_time_ms:.1f} ms" if self.execution_time_ms > 0 else "--"),
                ("trophy", "Result:", self.state)
            ]

        row_y = ry + 32
        for icon_type, label, val in res_rows:
            # Draw vector icon
            cx, cy = rx + 6, row_y + 8
            if icon_type == "stopwatch":
                pygame.draw.circle(self.screen, COLOR_ELECTRIC_BLUE, (cx, cy), 5, width=1)
                pygame.draw.line(self.screen, COLOR_BRIGHT_CYAN, (cx, cy - 5), (cx, cy - 8), 1)
                pygame.draw.line(self.screen, COLOR_BRIGHT_CYAN, (cx, cy), (cx + 2, cy - 2), 1)
            elif icon_type == "grid":
                for gr in range(2):
                    for gc in range(2):
                        pygame.draw.rect(self.screen, COLOR_ELECTRIC_BLUE, (cx - 4 + gc * 5, cy - 4 + gr * 5, 3, 3))
            elif icon_type == "clock":
                pygame.draw.circle(self.screen, COLOR_ELECTRIC_BLUE, (cx, cy), 5, width=1)
                pygame.draw.line(self.screen, COLOR_BRIGHT_CYAN, (cx, cy), (cx, cy - 3), 1)
                pygame.draw.line(self.screen, COLOR_BRIGHT_CYAN, (cx, cy), (cx + 3, cy), 1)
            elif icon_type == "trophy":
                pygame.draw.polygon(self.screen, COLOR_PATH, [(cx - 4, cy - 4), (cx + 4, cy - 4), (cx + 3, cy), (cx - 3, cy)])
                pygame.draw.line(self.screen, COLOR_PATH, (cx, cy), (cx, cy + 3), 1)
                pygame.draw.line(self.screen, COLOR_PATH, (cx - 3, cy + 4), (cx + 3, cy + 4), 1)

            # Label (Clean high-contrast bold text)
            lbl_surf = self.font_body_bold.render(label, True, COLOR_TEXT_SECONDARY)
            self.screen.blit(lbl_surf, (rx + 22, row_y))

            val_x = rx + 22 + lbl_surf.get_width() + 8
            # Value (Bold high-contrast statistics display)
            if label == "Result:":
                if val == "FINISHED":
                    status_text = "Path Found "
                    st_surf = self.font_stat_val.render(status_text, True, COLOR_START)
                    self.screen.blit(st_surf, (val_x, row_y))
                    # Draw vector green checkmark
                    chk_x = val_x + st_surf.get_width()
                    chk_y = row_y + 4
                    pts_chk = [(chk_x, chk_y + 4), (chk_x + 3, chk_y + 7), (chk_x + 8, chk_y)]
                    pygame.draw.lines(self.screen, COLOR_START, False, pts_chk, 2)
                elif val == "NO_PATH":
                    st_surf = self.font_stat_val.render("No Path Found ", True, COLOR_GOAL)
                    self.screen.blit(st_surf, (val_x, row_y))
                    chk_x = val_x + st_surf.get_width()
                    chk_y = row_y + 4
                    pygame.draw.line(self.screen, COLOR_GOAL, (chk_x, chk_y), (chk_x + 6, chk_y + 6), 2)
                    pygame.draw.line(self.screen, COLOR_GOAL, (chk_x + 6, chk_y), (chk_x, chk_y + 6), 2)
                elif val == "RUNNING":
                    st_surf = self.font_stat_val.render("Searching...", True, COLOR_FRONTIER)
                    self.screen.blit(st_surf, (val_x, row_y))
                elif val == "PAUSED":
                    st_surf = self.font_stat_val.render("Paused", True, COLOR_ELECTRIC_BLUE)
                    self.screen.blit(st_surf, (val_x, row_y))
                elif val == "Playing":
                    st_surf = self.font_stat_val.render("Playing...", True, COLOR_BRIGHT_CYAN)
                    self.screen.blit(st_surf, (val_x, row_y))
                else:
                    st_surf = self.font_stat_val.render("Ready", True, COLOR_BRIGHT_CYAN)
                    self.screen.blit(st_surf, (val_x, row_y))
            else:
                val_surf = self.font_stat_val.render(val, True, COLOR_TEXT_PRIMARY)
                self.screen.blit(val_surf, (val_x, row_y))

            row_y += 31

        # 3. Legend Card
        draw_rounded_rect(self.screen, COLOR_CARD_BG, self.card_legend_rect, radius=10,
                          border_color=COLOR_CARD_BORDER, border_width=1)
        pygame.draw.line(self.screen, COLOR_BRIGHT_CYAN,
                         (self.card_legend_rect.x + 14, self.card_legend_rect.y),
                         (self.card_legend_rect.x + 55, self.card_legend_rect.y), 2)
        
        lx = self.card_legend_rect.x + 14
        ly = self.card_legend_rect.y + 10
        # List icon
        pygame.draw.line(self.screen, COLOR_ELECTRIC_BLUE, (lx, ly + 4), (lx + 4, ly + 4), 2)
        pygame.draw.line(self.screen, COLOR_ELECTRIC_BLUE, (lx + 6, ly + 4), (lx + 13, ly + 4), 2)
        pygame.draw.line(self.screen, COLOR_ELECTRIC_BLUE, (lx, ly + 9), (lx + 4, ly + 9), 2)
        pygame.draw.line(self.screen, COLOR_ELECTRIC_BLUE, (lx + 6, ly + 9), (lx + 13, ly + 9), 2)
        title3 = self.font_section.render("Legend", True, COLOR_TEXT_PRIMARY)
        self.screen.blit(title3, (lx + 18, ly))

        legend_items = [
            (COLOR_START, "Start (Source)", False),
            (COLOR_GOAL, "Goal (Destination)", False),
            (COLOR_WALL, "Wall (Blocked)", True),
            (COLOR_OPEN, "Open Cell (Walkable)", True),
            (COLOR_EXPLORED, "Explored Node (Visited)", False),
            (COLOR_PATH, "Final Path (Solution)", "pill")
        ]

        item_y = ly + 28
        item_gap = max(21, min(26, (self.card_legend_rect.height - 38) // len(legend_items)))
        for col, text, is_border in legend_items:
            if is_border == "pill":
                pygame.draw.rect(self.screen, col, pygame.Rect(lx + 2, item_y + 4, 18, 7), border_radius=3)
            else:
                sq_rect = pygame.Rect(lx + 2, item_y, 16, 16)
                draw_rounded_rect(self.screen, col, sq_rect, radius=4,
                                  border_color=COLOR_CARD_BORDER if is_border else None, border_width=1)
            
            ls = self.font_body_bold.render(text, True, COLOR_TEXT_PRIMARY)
            self.screen.blit(ls, (lx + 28, item_y - 1))
            item_y += item_gap
    def _draw_comparison_overlay(self):
        """Render Algorithm Comparison Mode modal."""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((12, 13, 16, 225))
        self.screen.blit(overlay, (0, 0))

        cx = self.width // 2
        card_w = min(820, self.width - 60)
        card_h = min(540, self.height - 80)
        card_rect = pygame.Rect(cx - card_w // 2, (self.height - card_h) // 2, card_w, card_h)
        draw_rounded_rect(self.screen, COLOR_CARD_BG, card_rect, radius=12,
                          border_color=COLOR_ELECTRIC_BLUE, border_width=2)

        # Title
        t_surf = self.font_logo.render("Algorithm Comparison Suite", True, COLOR_TEXT_PRIMARY)
        self.screen.blit(t_surf, t_surf.get_rect(center=(cx, card_rect.y + 35)))

        sub = self.font_small.render("Benchmarking BFS, DFS, and A* on the identical maze snapshot", True, COLOR_TEXT_SECONDARY)
        self.screen.blit(sub, sub.get_rect(center=(cx, card_rect.y + 60)))

        # Comparison Table
        table_y = card_rect.y + 85
        cols = [("Algorithm", 140), ("Nodes Expanded", 170), ("Path Length", 160), ("Time (ms)", 130), ("Status", 120)]
        
        # Table Header
        hx = card_rect.x + 30
        for name, w in cols:
            hs = self.font_small.render(name, True, COLOR_ELECTRIC_BLUE)
            self.screen.blit(hs, (hx, table_y))
            hx += w
        pygame.draw.line(self.screen, COLOR_CARD_BORDER, (card_rect.x + 25, table_y + 24), (card_rect.right - 25, table_y + 24), 1)

        # Table Rows
        if self.comparison_worker.pending:
            waiting = self.font_body_bold.render("Comparing algorithms...", True, COLOR_BRIGHT_CYAN)
            self.screen.blit(waiting, waiting.get_rect(center=(cx, table_y + 70)))
        elif self.comparison_error:
            failed = self.font_body_bold.render("Comparison could not be completed.", True, COLOR_GOAL)
            self.screen.blit(failed, failed.get_rect(center=(cx, table_y + 70)))
        elif self.compare_results:
            min_path = min([r['path_len'] for r in self.compare_results if r['found']] or [0])
            ry = table_y + 36
            for r in self.compare_results:
                rx = card_rect.x + 30
                is_opt = (r['found'] and r['path_len'] == min_path)
                status_txt = "Optimal" if is_opt else ("Longer" if r['found'] else "No Path")
                status_col = COLOR_START if is_opt else (COLOR_FRONTIER if r['found'] else COLOR_GOAL)
                
                vals = [
                    (r['name'], cols[0][1], COLOR_TEXT_PRIMARY),
                    (str(r['nodes']), cols[1][1], COLOR_TEXT_PRIMARY),
                    (f"{r['path_len']} moves" if r['found'] else "--", cols[2][1], COLOR_TEXT_PRIMARY),
                    (f"{r['time_ms']:.3f} ms", cols[3][1], COLOR_TEXT_PRIMARY),
                    (status_txt, cols[4][1], status_col),
                ]
                for text, w, col in vals:
                    vs = self.font_body.render(text, True, col)
                    self.screen.blit(vs, (rx, ry))
                    rx += w
                ry += 32

        # Explanation Box
        ey = card_rect.y + 240
        exp_rect = pygame.Rect(card_rect.x + 25, ey, card_rect.width - 50, 110)
        draw_rounded_rect(self.screen, (28, 31, 37), exp_rect, radius=8, border_color=COLOR_CARD_BORDER, border_width=1)
        
        exps = [
            "1. Optimality: BFS and A* guarantee identical shortest path length on unweighted grids.",
            "2. Efficiency: A* expands fewer nodes in branching mazes by directing search using Manhattan distance.",
            "3. DFS Suboptimality: DFS explores deep dead-ends, producing erratic and non-optimal paths."
        ]
        ey_text = ey + 14
        for line in exps:
            ls = self.font_small.render(line, True, COLOR_TEXT_SECONDARY)
            self.screen.blit(ls, (exp_rect.x + 16, ey_text))
            ey_text += 26

        self.btn_modal_close.rect.y = card_rect.bottom - 50
        self.btn_modal_close.draw(self.screen, self.font_body_bold)
    def _draw_challenge_comparing_overlay(self) -> None:
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((12, 13, 16, 220))
        self.screen.blit(overlay, (0, 0))
        card = pygame.Rect(0, 0, min(540, self.width - 48), 150)
        card.center = (self.width // 2, self.height // 2)
        draw_rounded_rect(self.screen, COLOR_CARD_BG, card, radius=12,
                          border_color=COLOR_ELECTRIC_BLUE, border_width=2)
        title = self.font_section.render("Challenge complete", True, COLOR_TEXT_PRIMARY)
        self.screen.blit(title, title.get_rect(center=(card.centerx, card.y + 48)))
        detail = self.font_body.render("Comparing your result with BFS, DFS, and A*...", True, COLOR_BRIGHT_CYAN)
        self.screen.blit(detail, detail.get_rect(center=(card.centerx, card.y + 92)))
    def _draw_settings_modal(self):
        """Render Settings modal for animation speed, visualization options, and maze file management."""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((12, 13, 16, 225))
        self.screen.blit(overlay, (0, 0))

        cx = self.width // 2
        card_w = min(560, self.width - 60)
        card_h = min(460, self.height - 24)
        card_rect = pygame.Rect(cx - card_w // 2, (self.height - card_h) // 2, card_w, card_h)
        draw_rounded_rect(self.screen, COLOR_CARD_BG, card_rect, radius=12,
                          border_color=COLOR_ELECTRIC_BLUE, border_width=2)

        t_surf = self.font_logo.render("Visualization & Maze Settings", True, COLOR_TEXT_PRIMARY)
        self.screen.blit(t_surf, t_surf.get_rect(center=(cx, card_rect.y + 35)))

        sy = card_rect.y + 70
        # Speed display
        s_lbl = self.font_section.render(f"Animation Speed: {self.speed_level}x", True, COLOR_TEXT_PRIMARY)
        self.screen.blit(s_lbl, (card_rect.x + 40, sy))
        
        # Tips
        tip1 = self.font_small.render("Use Up/Down Arrow keys on keyboard to increase or decrease speed.", True, COLOR_TEXT_SECONDARY)
        self.screen.blit(tip1, (card_rect.x + 40, sy + 28))
        
        tip2 = self.font_small.render("Uncheck 'Animate Search' in the left panel for instant synchronous solution.", True, COLOR_TEXT_SECONDARY)
        self.screen.blit(tip2, (card_rect.x + 40, sy + 50))

        # Gameplay sound controls
        audio_y = sy + 82
        audio_label = self.font_body_bold.render("Gameplay Feedback", True, COLOR_TEXT_PRIMARY)
        self.screen.blit(audio_label, (card_rect.x + 40, audio_y + 3))
        self.btn_audio_toggle.text = "Sound: Off" if self.audio_muted else "Sound: On"
        self.btn_audio_toggle.rect = pygame.Rect(card_rect.x + 220, audio_y - 4, 104, 30)
        self.btn_volume_down.rect = pygame.Rect(card_rect.x + 336, audio_y - 4, 32, 30)
        self.btn_volume_up.rect = pygame.Rect(card_rect.right - 72, audio_y - 4, 32, 30)
        volume_label = self.font_small.render(f"{int(self.audio_volume * 100)}%", True, COLOR_TEXT_SECONDARY)
        self.screen.blit(volume_label, volume_label.get_rect(center=(card_rect.x + 397, audio_y + 11)))
        self.btn_audio_toggle.draw(self.screen, self.font_small)
        self.btn_volume_down.draw(self.screen, self.font_body_bold)
        self.btn_volume_up.draw(self.screen, self.font_body_bold)

        # Divider line
        pygame.draw.line(self.screen, COLOR_CARD_BORDER,
                         (card_rect.x + 30, sy + 120), (card_rect.right - 30, sy + 120), 1)

        # File Management Section
        my = sy + 134
        m_lbl = self.font_section.render("Maze File Management", True, COLOR_BRIGHT_CYAN)
        self.screen.blit(m_lbl, (card_rect.x + 40, my))

        m_desc = self.font_small.render("Load custom .txt maze files or cycle built-in sample mazes:", True, COLOR_TEXT_SECONDARY)
        self.screen.blit(m_desc, (card_rect.x + 40, my + 24))

        # Position and draw buttons
        btn_y = my + 50
        btn_w = (card_w - 90) // 2
        self.btn_modal_load.rect = pygame.Rect(card_rect.x + 40, btn_y, btn_w, 36)
        self.btn_modal_samples.rect = pygame.Rect(card_rect.x + 40 + btn_w + 10, btn_y, btn_w, 36)

        self.btn_modal_load.draw(self.screen, self.font_body_bold)
        self.btn_modal_samples.draw(self.screen, self.font_body_bold)

        self.btn_maze_export.rect = pygame.Rect(card_rect.x + 40, btn_y + 42, card_w - 80, 36)
        self.btn_maze_export.draw(self.screen, self.font_body_bold)
        share_text = self.maze_share_status or "Share the exported TXT file; others can open it with Load File."
        share_color = COLOR_BRIGHT_CYAN if self.maze_share_status else COLOR_TEXT_SECONDARY
        share_surf = self.font_small.render(share_text, True, share_color)
        self.screen.blit(share_surf, (card_rect.x + 40, btn_y + 84))

        self.btn_modal_close.rect.y = card_rect.bottom - 48
        self.btn_modal_close.draw(self.screen, self.font_body_bold)
    def _draw_info_modal(self):
        """Render Information modal with academic project details."""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((12, 13, 16, 225))
        self.screen.blit(overlay, (0, 0))

        cx = self.width // 2
        card_w = min(680, self.width - 60)
        card_h = 420
        card_rect = pygame.Rect(cx - card_w // 2, (self.height - card_h) // 2, card_w, card_h)
        draw_rounded_rect(self.screen, COLOR_CARD_BG, card_rect, radius=12,
                          border_color=COLOR_ELECTRIC_BLUE, border_width=2)

        t_surf = self.font_logo.render("About AI Maze Solver", True, COLOR_TEXT_PRIMARY)
        self.screen.blit(t_surf, t_surf.get_rect(center=(cx, card_rect.y + 35)))

        info_lines = [
            ("Course:", "Second-Year Computer Science — Artificial Intelligence"),
            ("Search Space:", "2D Discrete 4-Connected Grid Graph G = (V, E)"),
            ("Algorithms:", "BFS (FIFO Queue), DFS (LIFO Stack), A* (Priority Queue + Manhattan)"),
            ("Heuristic:", "Manhattan Distance: h(n) = |dr| + |dc| (Admissible & Dominating)"),
            ("Time Complexity:", "BFS: O(V), DFS: O(V), A*: O(V log V) on Grid Graphs"),
            ("Shortcuts:", "Space=Run/Pause, R=Reset, N=New, L=Load, M=Sample, 1/2/3=Algos, C=Compare")
        ]

        iy = card_rect.y + 80
        for k, v in info_lines:
            ks = self.font_section.render(k, True, COLOR_ELECTRIC_BLUE)
            vs = self.font_body.render(v, True, COLOR_TEXT_PRIMARY)
            self.screen.blit(ks, (card_rect.x + 40, iy))
            self.screen.blit(vs, (card_rect.x + 180, iy))
            iy += 32

        self.btn_modal_close.rect.y = card_rect.bottom - 50
        self.btn_modal_close.draw(self.screen, self.font_body_bold)
    def _draw_challenge_failed_overlay(self):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((12, 13, 16, 225))
        self.screen.blit(overlay, (0, 0))
        card = pygame.Rect(0, 0, min(520, self.width - 32), 220)
        card.center = (self.width // 2, self.height // 2)
        draw_rounded_rect(self.screen, COLOR_CARD_BG, card, radius=12,
                          border_color=COLOR_GOAL, border_width=2)
        title = self.font_logo.render("Move Budget Reached", True, COLOR_TEXT_PRIMARY)
        self.screen.blit(title, title.get_rect(center=(card.centerx, card.y + 54)))
        detail = f"Level {self.challenge_level}: limit was {self.challenge_move_limit} moves. Retry to try again."
        hint = self.font_body.render(detail, True, COLOR_TEXT_SECONDARY)
        self.screen.blit(hint, hint.get_rect(center=(card.centerx, card.y + 101)))
        btn_w, btn_h, gap = 160, 36, 14
        left = card.centerx - btn_w - gap // 2
        y = card.bottom - 58
        self.btn_challenge_retry.rect = pygame.Rect(left, y, btn_w, btn_h)
        self.btn_challenge_menu.rect = pygame.Rect(left + btn_w + gap, y, btn_w, btn_h)
        self.btn_challenge_retry.draw(self.screen, self.font_body_bold)
        self.btn_challenge_menu.draw(self.screen, self.font_body_bold)
    def _draw_new_campaign_confirmation(self):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((12, 13, 16, 225))
        self.screen.blit(overlay, (0, 0))
        card = pygame.Rect(0, 0, min(540, self.width - 32), 230)
        card.center = (self.width // 2, self.height // 2)
        draw_rounded_rect(self.screen, COLOR_CARD_BG, card, radius=12,
                          border_color=COLOR_ELECTRIC_BLUE, border_width=2)
        title = self.font_logo.render("Start a New Campaign?", True, COLOR_TEXT_PRIMARY)
        self.screen.blit(title, title.get_rect(center=(card.centerx, card.y + 54)))
        detail = self.font_body.render("This clears saved unlocks and best scores, then starts at Level 1.", True, COLOR_TEXT_SECONDARY)
        self.screen.blit(detail, detail.get_rect(center=(card.centerx, card.y + 102)))
        self.btn_confirm_new_campaign.rect = pygame.Rect(card.centerx - 170, card.bottom - 58, 180, 36)
        self.btn_cancel_new_campaign.rect = pygame.Rect(card.centerx + 20, card.bottom - 58, 150, 36)
        self.btn_confirm_new_campaign.draw(self.screen, self.font_body_bold)
        self.btn_cancel_new_campaign.draw(self.screen, self.font_body_bold)
    def _draw_challenge_tutorial_modal(self):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((12, 13, 16, 220))
        self.screen.blit(overlay, (0, 0))
        card = pygame.Rect(0, 0, min(640, self.width - 32), min(460, self.height - 24))
        card.center = (self.width // 2, self.height // 2)
        draw_rounded_rect(self.screen, COLOR_CARD_BG, card, radius=12,
                          border_color=COLOR_ELECTRIC_BLUE, border_width=2)
        title = self.font_logo.render("How to Play Human Challenge", True, COLOR_TEXT_PRIMARY)
        self.screen.blit(title, title.get_rect(center=(card.centerx, card.y + 38)))
        instructions = [
            f"Selected difficulty: {self.challenge_difficulty}. Change it with Diff before starting.",
            "Reach the red Goal from the green Start without crossing walls.",
            "Move with the arrow keys or W, A, S, D.",
            "Press P, Space, or Esc to pause. The timer pauses too.",
            "Easy: smaller maze growth with a generous move budget.",
            "Medium: balanced maze growth and move limits.",
            "Hard: larger mazes with tighter move limits.",
            "Later level limits are measured against the BFS shortest route.",
            "Press H or use Hint for one next step if you get stuck.",
            "After a win, review your score and choose Next Level.",
            "Unlocked levels and best scores are saved on this computer.",
        ]
        y = card.y + 80
        for line in instructions:
            rendered = self.font_small.render(line, True, COLOR_TEXT_SECONDARY)
            self.screen.blit(rendered, rendered.get_rect(center=(card.centerx, y)))
            y += 27
        self.btn_tutorial_start.rect = pygame.Rect(card.centerx - 170, card.bottom - 54, 190, 36)
        self.btn_tutorial_close.rect = pygame.Rect(card.centerx + 30, card.bottom - 54, 120, 36)
        self.btn_tutorial_start.draw(self.screen, self.font_body_bold)
        self.btn_tutorial_close.draw(self.screen, self.font_body_bold)
    def _draw_challenge_pause_overlay(self):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((12, 13, 16, 220))
        self.screen.blit(overlay, (0, 0))
        card = pygame.Rect(0, 0, min(520, self.width - 32), 220)
        card.center = (self.width // 2, self.height // 2)
        draw_rounded_rect(self.screen, COLOR_CARD_BG, card, radius=12,
                          border_color=COLOR_ELECTRIC_BLUE, border_width=2)
        title = self.font_logo.render("Challenge Paused", True, COLOR_TEXT_PRIMARY)
        self.screen.blit(title, title.get_rect(center=(card.centerx, card.y + 54)))
        hint = self.font_body.render("Your timer is paused. Resume, retry this level, or return to the menu.", True, COLOR_TEXT_SECONDARY)
        self.screen.blit(hint, hint.get_rect(center=(card.centerx, card.y + 100)))
        btn_w, btn_h, gap = 142, 36, 10
        total = btn_w * 3 + gap * 2
        left = card.centerx - total // 2
        y = card.bottom - 58
        self.btn_challenge_resume.rect = pygame.Rect(left, y, btn_w, btn_h)
        self.btn_challenge_retry.rect = pygame.Rect(left + btn_w + gap, y, btn_w, btn_h)
        self.btn_challenge_menu.rect = pygame.Rect(left + (btn_w + gap) * 2, y, btn_w, btn_h)
        self.btn_challenge_resume.draw(self.screen, self.font_body_bold)
        self.btn_challenge_retry.draw(self.screen, self.font_body_bold)
        self.btn_challenge_menu.draw(self.screen, self.font_body_bold)
    def _draw_challenge_results_modal(self):
        """Render Human vs AI Challenge Mode results dashboard."""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((12, 13, 16, 230))
        self.screen.blit(overlay, (0, 0))

        cx = self.width // 2
        card_w = min(880, self.width - 24)
        card_h = min(580, self.height - 20)
        card_rect = pygame.Rect(cx - card_w // 2, (self.height - card_h) // 2, card_w, card_h)
        draw_rounded_rect(self.screen, COLOR_CARD_BG, card_rect, radius=12,
                          border_color=COLOR_ELECTRIC_BLUE, border_width=2)

        # Header Title & Subtitle
        level_title = f"Level {self.challenge_level}/{self.challenge_level_count} — " if self.challenge_level else ""
        t_surf = self.font_logo.render(f"Human vs AI Challenge — {level_title}Results", True, COLOR_TEXT_PRIMARY)
        self.screen.blit(t_surf, t_surf.get_rect(center=(cx, card_rect.y + 26)))

        score = self.challenge_level_scores.get(self.challenge_level, 0)
        run_total = sum(self.challenge_level_scores.values())
        campaign_best = sum(self.challenge_best_scores.values())
        sub_text = (
            f"Level score: {score}/100  ·  Campaign: {run_total}/{self.challenge_level_count * 100}"
            f"  ·  Best: {campaign_best}/{self.challenge_level_count * 100}"
        )
        sub = self.font_small.render(sub_text, True, COLOR_TEXT_SECONDARY)
        self.screen.blit(sub, sub.get_rect(center=(cx, card_rect.y + 50)))

        res = self.challenge_comparison_results or {}
        human_data = res.get("human", {})
        ai_data = res.get("ai", {})
        has_error = bool(res.get("error"))

        # Authoritative BFS optimality reference (BFS is the sole ground truth)
        bfs_data = ai_data.get("BFS", {})
        bfs_found = bfs_data.get("found", False)
        bfs_opt_len = bfs_data.get("path_length") if bfs_found else None

        opt_ratio = res.get("optimality_ratio")

        # 1. KPI Metric Chips (4 cards horizontally)
        chip_y = card_rect.y + 68
        avail_chip_w = card_w - 48
        chip_spacing = 8
        chip_w = (avail_chip_w - (chip_spacing * 3)) // 4
        chip_h = 56

        # Format optimality ratio value:
        if opt_ratio is None or bfs_opt_len is None:
            opt_ratio_val = "N/A"
            opt_ratio_col = COLOR_TEXT_SECONDARY
        else:
            opt_ratio_val = f"{min(999.0, opt_ratio):.1f}%"
            opt_ratio_col = COLOR_START if opt_ratio >= 99.9 else COLOR_PATH

        chips = [
            ("Human Moves", f"{human_data.get('path_length', 0)}", COLOR_BRIGHT_CYAN),
            ("Completion Time", f"{human_data.get('elapsed_time_s', 0.0):.2f} s", COLOR_ELECTRIC_BLUE),
            ("Level Score", f"{score}/100", (160, 210, 255)),
            ("Optimality Ratio", opt_ratio_val, opt_ratio_col)
        ]

        for i, (label, val, col) in enumerate(chips):
            ch_rect = pygame.Rect(card_rect.x + 24 + i * (chip_w + chip_spacing), chip_y, chip_w, chip_h)
            draw_rounded_rect(self.screen, (22, 25, 30), ch_rect, radius=8, border_color=COLOR_CARD_BORDER, border_width=1)
            ls = self.font_small.render(label, True, COLOR_TEXT_SECONDARY)
            self.screen.blit(ls, ls.get_rect(center=(ch_rect.centerx, ch_rect.y + 15)))
            vs = self.font_stat_val.render(val, True, col)
            self.screen.blit(vs, vs.get_rect(center=(ch_rect.centerx, ch_rect.y + 37)))

        # 2. Comparison Table
        table_y = chip_y + 68
        avail_tw = card_w - 48
        
        # Responsive dynamic column widths
        col_comp = int(avail_tw * 0.18)
        col_path = int(avail_tw * 0.18)
        col_exp = int(avail_tw * 0.25)
        col_time = int(avail_tw * 0.23)
        col_opt = avail_tw - (col_comp + col_path + col_exp + col_time)

        cols = [
            ("Competitor", col_comp),
            ("Path (Moves)", col_path),
            ("Exploration Metric", col_exp),
            ("Elapsed / Compute Time", col_time),
            ("Optimality", col_opt)
        ]

        # Header
        hx = card_rect.x + 24
        for name, w in cols:
            hs = self.font_section.render(name, True, COLOR_ELECTRIC_BLUE)
            self.screen.blit(hs, (hx + 4, table_y))
            hx += w
        pygame.draw.line(self.screen, COLOR_CARD_BORDER, (card_rect.x + 24, table_y + 24), (card_rect.right - 24, table_y + 24), 1)

        # Table Rows: Human, BFS, DFS, A*
        rows_data = []

        # Human Row
        h_len = human_data.get("path_length", 0)
        if bfs_opt_len is not None:
            if h_len <= bfs_opt_len:
                h_opt_txt = "Optimal"
                h_opt_col = COLOR_START
            else:
                diff = h_len - bfs_opt_len
                h_opt_txt = f"+{diff} moves"
                h_opt_col = COLOR_FRONTIER
        else:
            h_opt_txt = "N/A"
            h_opt_col = COLOR_TEXT_SECONDARY

        rows_data.append((
            "Human Player",
            f"{h_len} transitions",
            f"{human_data.get('unique_cells_visited', 0)} visited cells",
            f"{human_data.get('elapsed_time_s', 0.0):.2f} s (real-time)",
            h_opt_txt,
            h_opt_col
        ))

        # AI Rows
        for algo_name in ["BFS", "DFS", "A*"]:
            if has_error or algo_name not in ai_data:
                rows_data.append((
                    algo_name,
                    "--",
                    "N/A",
                    "--",
                    "Unavailable",
                    COLOR_TEXT_SECONDARY
                ))
                continue

            adata = ai_data.get(algo_name, {})
            found = adata.get("found", False)
            a_len = adata.get("path_length", 0)
            a_time_ms = adata.get("compute_time_ms", adata.get("time_ms", 0.0))
            nodes = adata.get("nodes_expanded", 0)

            if found:
                p_str = f"{a_len} transitions"
                if algo_name == "BFS":
                    opt_txt = "Optimal"
                    opt_col = COLOR_START
                elif bfs_opt_len is not None:
                    if a_len == bfs_opt_len:
                        opt_txt = "Optimal"
                        opt_col = COLOR_START
                    else:
                        diff = a_len - bfs_opt_len
                        opt_txt = f"+{diff} moves"
                        opt_col = COLOR_FRONTIER
                else:
                    opt_txt = "N/A"
                    opt_col = COLOR_TEXT_SECONDARY
            else:
                p_str = "--"
                opt_txt = "No Path"
                opt_col = COLOR_GOAL

            rows_data.append((
                algo_name,
                p_str,
                f"{nodes} nodes expanded",
                f"{a_time_ms:.3f} ms (CPU)",
                opt_txt,
                opt_col
            ))

        ry = table_y + 30
        for cname, plen, exp_metric, t_str, opt_lbl, opt_col in rows_data:
            rx = card_rect.x + 24
            vals = [
                (cname, cols[0][1], COLOR_BRIGHT_CYAN if cname == "Human Player" else COLOR_TEXT_PRIMARY),
                (plen, cols[1][1], COLOR_TEXT_PRIMARY),
                (exp_metric, cols[2][1], (180, 195, 215)),
                (t_str, cols[3][1], COLOR_TEXT_PRIMARY),
                (opt_lbl, cols[4][1], opt_col)
            ]
            for text, w, col in vals:
                vs = self.font_body.render(text, True, col)
                self.screen.blit(vs, (rx + 4, ry))
                rx += w
            ry += 24

        # 3. Explanatory Notes or Error Banner Box
        ny = ry + 8
        note_rect = pygame.Rect(card_rect.x + 24, ny, card_rect.width - 48, 70)

        if has_error:
            draw_rounded_rect(self.screen, (45, 20, 24), note_rect, radius=8, border_color=(200, 60, 60), border_width=1)
            err_title = self.font_body_bold.render("⚠️ AI Comparison Benchmark Unavailable", True, (255, 120, 120))
            self.screen.blit(err_title, (note_rect.x + 14, ny + 8))
            err_detail = f"Reason: {res.get('error', 'Unknown error')} (Human performance preserved; AI benchmark aborted)"
            err_sub = self.font_small.render(err_detail, True, (255, 200, 200))
            self.screen.blit(err_sub, (note_rect.x + 14, ny + 30))
        else:
            draw_rounded_rect(self.screen, (22, 25, 30), note_rect, radius=8, border_color=COLOR_CARD_BORDER, border_width=1)
            n_lines = [
                "• Exploration Metric: Human counts unique cells visited; AI algorithms count search tree nodes expanded.",
                "• Time Metric: Human time includes play; AI time measures CPU graph traversal compute.",
                f"• Level detail: {self.maze.rows}×{self.maze.cols} · Difficulty {self.challenge_difficulty} · "
                f"{human_data.get('unique_cells_visited', 0)} unique cells visited · "
                f"Level best {self.challenge_best_scores.get(self.challenge_level, score)}/100"
            ]
            ny_text = ny + 8
            for line in n_lines:
                ls = self.font_small.render(line, True, COLOR_TEXT_SECONDARY)
                self.screen.blit(ls, (note_rect.x + 14, ny_text))
                ny_text += 18

        # 4. Path Viewer Selection Bar
        pv_y = ny + 78
        pv_lbl = self.font_section.render("Inspect Path on Maze:", True, COLOR_TEXT_PRIMARY)
        self.screen.blit(pv_lbl, (card_rect.x + 28, pv_y + 4))

        view_btns = [
            ("Human", self.btn_view_human),
            ("BFS", self.btn_view_bfs),
            ("DFS", self.btn_view_dfs),
            ("A*", self.btn_view_astar)
        ]
        btn_vw = min(105, max(75, (card_w - 280) // 4))
        btn_vx = card_rect.x + 230
        for name, btn in view_btns:
            btn.rect = pygame.Rect(btn_vx, pv_y, btn_vw, 28)
            btn.is_primary = (self.challenge_selected_view_path == name)
            btn.draw(self.screen, self.font_small)
            btn_vx += btn_vw + 10

        # 5. Bottom Action Buttons (Next Level / Play Again, Main Menu)
        btn_w = 160
        btn_h = 36
        by = card_rect.bottom - 46
        self.btn_challenge_menu.rect = pygame.Rect(card_rect.centerx + 10, by, btn_w, btn_h)
        if self.challenge_level < self.challenge_level_count:
            self.btn_challenge_next_level.rect = pygame.Rect(card_rect.centerx - btn_w - 10, by, btn_w, btn_h)
            self.btn_challenge_next_level.draw(self.screen, self.font_body_bold)
        else:
            self.btn_challenge_play_again.rect = pygame.Rect(card_rect.centerx - btn_w - 10, by, btn_w, btn_h)
            self.btn_challenge_play_again.draw(self.screen, self.font_body_bold)
        self.btn_challenge_menu.draw(self.screen, self.font_body_bold)
