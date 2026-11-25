"""Reusable Pygame widgets and vector drawing helpers."""

import math
from typing import Optional, Tuple, List

import pygame

from ui_theme import *  # noqa: F401,F403 - palette constants are the public widget colors

# --- REUSABLE DRAWING HELPERS ---
def draw_rounded_rect(surface: pygame.Surface, color, rect: pygame.Rect, radius: int = 8,
                      border_color=None, border_width: int = 1):
    """Draw a smooth rounded rectangle with optional border."""
    pygame.draw.rect(surface, color, rect, border_radius=radius)
    if border_color and border_width > 0:
        pygame.draw.rect(surface, border_color, rect, width=border_width, border_radius=radius)


def draw_icon_maze_logo(surface: pygame.Surface, center: Tuple[int, int], size: int = 36):
    """Draw the modern maze logo icon with graphite styling."""
    cx, cy = center
    r = pygame.Rect(cx - size // 2, cy - size // 2, size, size)
    draw_rounded_rect(surface, COLOR_PANEL_BG, r, radius=8, border_color=COLOR_ELECTRIC_BLUE, border_width=1)
    
    # Concentric maze lines
    col = COLOR_BRIGHT_CYAN
    hw = size // 2
    # Outer ring with gap
    pygame.draw.line(surface, col, (cx - hw + 6, cy - hw + 6), (cx + hw - 6, cy - hw + 6), 2)
    pygame.draw.line(surface, col, (cx + hw - 6, cy - hw + 6), (cx + hw - 6, cy + hw - 6), 2)
    pygame.draw.line(surface, col, (cx + hw - 6, cy + hw - 6), (cx - hw + 6, cy + hw - 6), 2)
    pygame.draw.line(surface, col, (cx - hw + 6, cy + hw - 6), (cx - hw + 6, cy - hw + 12), 2)
    
    # Inner ring
    pygame.draw.line(surface, col, (cx - hw + 12, cy - hw + 12), (cx + hw - 12, cy - hw + 12), 2)
    pygame.draw.line(surface, col, (cx + hw - 12, cy - hw + 12), (cx + hw - 12, cy + hw - 12), 2)
    pygame.draw.line(surface, col, (cx + hw - 18, cy), (cx + hw - 12, cy), 2)
    
    # Center dot
    pygame.draw.circle(surface, COLOR_TEXT_PRIMARY, (cx, cy), 2)


def draw_header_icon(surface: pygame.Surface, icon_type: str, rect: pygame.Rect, hovered: bool = False):
    """Draw top header action icons: 'home', 'stats', 'settings', 'info'."""
    bg_col = COLOR_BTN_SECONDARY_HOVER if hovered else COLOR_CARD_BG
    border_col = COLOR_ELECTRIC_BLUE if hovered else COLOR_CARD_BORDER
    draw_rounded_rect(surface, bg_col, rect, radius=8, border_color=border_col, border_width=1)
    
    cx, cy = rect.center
    col = COLOR_TEXT_PRIMARY if hovered else COLOR_TEXT_SECONDARY
    
    if icon_type == "home":
        # Roof
        pygame.draw.polygon(surface, col, [(cx, cy - 8), (cx - 8, cy - 1), (cx + 8, cy - 1)])
        # House body
        pygame.draw.rect(surface, col, (cx - 6, cy - 1, 12, 9), width=1)
        # Door
        pygame.draw.rect(surface, col, (cx - 2, cy + 2, 4, 6))
    elif icon_type == "stats":
        # 3 vertical bar chart bars
        pygame.draw.rect(surface, col, (cx - 7, cy + 1, 4, 7), border_radius=1)
        pygame.draw.rect(surface, col, (cx - 2, cy - 6, 4, 14), border_radius=1)
        pygame.draw.rect(surface, col, (cx + 3, cy - 2, 4, 10), border_radius=1)
    elif icon_type == "settings":
        # Cog wheel
        pygame.draw.circle(surface, col, (cx, cy), 6, width=2)
        pygame.draw.circle(surface, col, (cx, cy), 2)
        for angle in [0, 45, 90, 135]:
            rad = math.radians(angle)
            dx = int(math.cos(rad) * 8)
            dy = int(math.sin(rad) * 8)
            pygame.draw.line(surface, col, (cx - dx, cy - dy), (cx + dx, cy + dy), 2)
    elif icon_type == "info":
        # Info 'i' inside circle
        pygame.draw.circle(surface, col, (cx, cy), 8, width=2)
        pygame.draw.circle(surface, col, (cx, cy - 4), 1)
        pygame.draw.line(surface, col, (cx, cy - 1), (cx, cy + 4), 2)


# --- UI CONTROLS & WIDGETS ---
class Button:
    """Clickable button with icon and hover effects."""
    def __init__(self, rect: pygame.Rect, text: str, callback=None,
                 is_primary: bool = False, icon: Optional[str] = None):
        self.rect = rect
        self.text = text
        self.callback = callback
        self.is_primary = is_primary
        self.icon = icon
        self.is_hovered = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.callback:
                    self.callback()
                return True
        return False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font):
        if self.is_primary:
            bg_col = COLOR_PRIMARY_HOVER if self.is_hovered else COLOR_ELECTRIC_BLUE
            border_col = COLOR_BRIGHT_CYAN
            radius = self.rect.height // 2
            draw_rounded_rect(surface, bg_col, self.rect, radius=radius, border_color=border_col, border_width=1)
        else:
            bg_col = COLOR_BTN_SECONDARY_HOVER if self.is_hovered else COLOR_BTN_SECONDARY
            border_col = COLOR_ELECTRIC_BLUE if self.is_hovered else COLOR_CARD_BORDER
            radius = 8
            draw_rounded_rect(surface, bg_col, self.rect, radius=radius, border_color=border_col, border_width=1)

        # Draw icon if present
        if self.is_primary:
            text_col = (255, 255, 255)
        else:
            text_col = COLOR_TEXT_PRIMARY if self.is_hovered else COLOR_TEXT_SECONDARY
        text_surf = font.render(self.text, True, text_col)
        cx, cy = self.rect.center
        
        if self.icon == "play":
            # Right arrow / play triangle
            ix = cx - text_surf.get_width() // 2 - 10
            pygame.draw.polygon(surface, (255, 255, 255), [(ix, cy - 6), (ix + 9, cy), (ix, cy + 6)])
            text_rect = text_surf.get_rect(midleft=(ix + 14, cy))
        elif self.icon == "pause":
            ix = cx - text_surf.get_width() // 2 - 10
            pygame.draw.rect(surface, (255, 255, 255), (ix, cy - 6, 3, 12))
            pygame.draw.rect(surface, (255, 255, 255), (ix + 5, cy - 6, 3, 12))
            text_rect = text_surf.get_rect(midleft=(ix + 14, cy))
        elif self.icon == "reload":
            # Circular arrow
            ix = cx - text_surf.get_width() // 2 - 8
            pygame.draw.arc(surface, text_col, (ix - 5, cy - 5, 10, 10), 0.5, 5.8, 2)
            pygame.draw.polygon(surface, text_col, [(ix + 3, cy - 5), (ix + 7, cy - 2), (ix + 1, cy - 2)])
            text_rect = text_surf.get_rect(midleft=(ix + 12, cy))
        elif self.icon in ["sparkle", "dice"]:
            # Dice icon with dots
            ix = cx - text_surf.get_width() // 2 - 8
            dice_rect = pygame.Rect(ix - 6, cy - 6, 12, 12)
            draw_rounded_rect(surface, COLOR_BTN_SECONDARY_HOVER, dice_rect, radius=3,
                              border_color=text_col, border_width=1)
            pygame.draw.circle(surface, COLOR_TEXT_PRIMARY, (ix - 2, cy - 2), 1)
            pygame.draw.circle(surface, COLOR_TEXT_PRIMARY, (ix + 2, cy + 2), 1)
            pygame.draw.circle(surface, COLOR_TEXT_PRIMARY, (ix, cy), 1)
            text_rect = text_surf.get_rect(midleft=(ix + 12, cy))
        else:
            text_rect = text_surf.get_rect(center=self.rect.center)
            
        surface.blit(text_surf, text_rect)


class Dropdown:
    """Modern dropdown selection menu with rounded header, icon, and popup options."""
    def __init__(self, rect: pygame.Rect, options: List[str], selected_idx: int = 0,
                 on_select=None, icon: Optional[str] = None):
        self.rect = rect
        self.options = options
        self.selected_idx = selected_idx
        self.on_select = on_select
        self.icon = icon
        self.is_open = False
        self.hovered_item: Optional[int] = None
        self.is_hovered = False

    @property
    def selected_value(self) -> str:
        return self.options[self.selected_idx]

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
            if self.is_open:
                self.hovered_item = None
                for i in range(len(self.options)):
                    item_rect = pygame.Rect(self.rect.x, self.rect.bottom + i * self.rect.height,
                                            self.rect.width, self.rect.height)
                    if item_rect.collidepoint(event.pos):
                        self.hovered_item = i
                        break

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.is_open = not self.is_open
                return True
            elif self.is_open:
                for i in range(len(self.options)):
                    item_rect = pygame.Rect(self.rect.x, self.rect.bottom + i * self.rect.height,
                                            self.rect.width, self.rect.height)
                    if item_rect.collidepoint(event.pos):
                        self.selected_idx = i
                        self.is_open = False
                        if self.on_select:
                            self.on_select(self.options[i])
                        return True
                self.is_open = False

        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and self.is_open:
            self.is_open = False
            return True

        return False

    def draw_closed(self, surface: pygame.Surface, font: pygame.font.Font):
        """Draw the closed dropdown box."""
        bg_col = COLOR_BTN_SECONDARY if not self.is_hovered else COLOR_BTN_SECONDARY_HOVER
        border_col = COLOR_ELECTRIC_BLUE if (self.is_hovered or self.is_open) else COLOR_CARD_BORDER
        draw_rounded_rect(surface, bg_col, self.rect, radius=6, border_color=border_col, border_width=1)

        # Optional Icon
        offset_x = 14
        if self.icon == "wand":
            # Magic wand / star icon
            wx, wy = self.rect.x + 14, self.rect.centery
            pygame.draw.line(surface, COLOR_ELECTRIC_BLUE, (wx - 4, wy + 4), (wx + 3, wy - 3), 2)
            pygame.draw.circle(surface, COLOR_TEXT_PRIMARY, (wx + 4, wy - 4), 1)
            pygame.draw.circle(surface, COLOR_ELECTRIC_BLUE, (wx + 1, wy - 6), 1)
            pygame.draw.circle(surface, COLOR_ELECTRIC_BLUE, (wx + 6, wy - 1), 1)
            offset_x = 30
        elif self.icon == "grid":
            # 3x3 Mini Grid
            gx, gy = self.rect.x + 10, self.rect.centery - 5
            for row in range(3):
                for col in range(3):
                    pygame.draw.rect(surface, COLOR_ELECTRIC_BLUE, (gx + col * 4, gy + row * 4, 2, 2))
            offset_x = 30

        # Draw selected text
        text_surf = font.render(self.selected_value, True, COLOR_TEXT_PRIMARY)
        text_rect = text_surf.get_rect(midleft=(self.rect.x + offset_x, self.rect.centery))
        surface.blit(text_surf, text_rect)

        # Draw down chevron
        cx = self.rect.right - 16
        cy = self.rect.centery
        col = COLOR_BRIGHT_CYAN if (self.is_hovered or self.is_open) else COLOR_TEXT_SECONDARY
        pygame.draw.lines(surface, col, False, [(cx - 4, cy - 2), (cx, cy + 2), (cx + 4, cy - 2)], 2)

    def draw_popup(self, surface: pygame.Surface, font: pygame.font.Font):
        """Draw the popup list when opened."""
        if not self.is_open:
            return
        popup_h = len(self.options) * self.rect.height
        popup_rect = pygame.Rect(self.rect.x, self.rect.bottom + 2, self.rect.width, popup_h)
        draw_rounded_rect(surface, COLOR_CARD_BG, popup_rect, radius=6, border_color=COLOR_ELECTRIC_BLUE, border_width=1)

        for i, opt in enumerate(self.options):
            item_rect = pygame.Rect(self.rect.x, self.rect.bottom + 2 + i * self.rect.height,
                                    self.rect.width, self.rect.height)
            if i == self.hovered_item:
                pygame.draw.rect(surface, COLOR_BTN_SECONDARY_HOVER, item_rect, border_radius=4)
            elif i == self.selected_idx:
                pygame.draw.rect(surface, COLOR_PRIMARY_BLUE, item_rect, border_radius=4)

            opt_surf = font.render(opt, True, COLOR_TEXT_PRIMARY)
            opt_rect = opt_surf.get_rect(midleft=(item_rect.x + 14, item_rect.centery))
            surface.blit(opt_surf, opt_rect)


class Checkbox:
    """Custom stylized toggle checkbox."""
    def __init__(self, rect: pygame.Rect, label: str, checked: bool = True, on_toggle=None):
        self.rect = rect
        self.label = label
        self.checked = checked
        self.on_toggle = on_toggle
        self.is_hovered = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.checked = not self.checked
                if self.on_toggle:
                    self.on_toggle(self.checked)
                return True
        return False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font):
        box_size = 22
        box_rect = pygame.Rect(self.rect.x, self.rect.centery - box_size // 2, box_size, box_size)
        
        # Draw checkbox box
        if self.checked:
            draw_rounded_rect(surface, COLOR_PRIMARY_BLUE, box_rect, radius=5,
                              border_color=COLOR_BRIGHT_CYAN, border_width=1)
            # Checkmark
            bx, by = box_rect.x, box_rect.y
            pts = [(bx + 5, by + 11), (bx + 9, by + 15), (bx + 17, by + 7)]
            pygame.draw.lines(surface, COLOR_TEXT_PRIMARY, False, pts, 2)
        else:
            bg_col = (26, 29, 35) if not self.is_hovered else COLOR_BTN_SECONDARY
            draw_rounded_rect(surface, bg_col, box_rect, radius=5,
                              border_color=COLOR_CARD_BORDER, border_width=1)

        # Draw label
        lbl_col = COLOR_TEXT_PRIMARY if (self.is_hovered or self.checked) else COLOR_TEXT_SECONDARY
        lbl_surf = font.render(self.label, True, lbl_col)
        surface.blit(lbl_surf, (self.rect.x + box_size + 12, self.rect.centery - lbl_surf.get_height() // 2))


# --- MAIN USER INTERFACE MANAGER ---
