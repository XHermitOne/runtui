#!/usr/bin/env python3
"""Render the demo app to a buffer and output an ANSI screenshot."""

import sys
import os
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from runtui.core.types import Attrs, Color, Rect, BorderStyle, attrs_sequence
from runtui.core.unicode import string_width, truncate_to_width
from runtui.rendering.buffer import CellBuffer
from runtui.rendering.painter import Painter
from runtui.themes.engine import ThemeEngine
from runtui.themes.turbo_vision import turbo_vision_theme
from runtui.themes.dark import dark_theme
from runtui.themes.nord import nord_theme
from runtui.widgets.base import Widget
from runtui.widgets.container import Container
from runtui.widgets.label import Label
from runtui.widgets.button import Button
from runtui.widgets.input import TextInput
from runtui.widgets.password import PasswordInput
from runtui.widgets.checkbox import Checkbox
from runtui.widgets.radio import RadioButton, RadioGroup
from runtui.widgets.textarea import TextArea
from runtui.widgets.listbox import ListBox
from runtui.widgets.dropdown import DropDownList
from runtui.widgets.calendar import Calendar
from runtui.widgets.color_picker import ColorPicker
from runtui.widgets.progressbar import ProgressBar
from runtui.widgets.scrollbar import VScrollbar
from runtui.widgets.menu import MenuBar, Menu, MenuItem
from runtui.windows.window import Window
from runtui.windows.window_manager import WindowManager
from runtui.windows.taskbar import TaskBar
from runtui.mouse.cursor import MouseCursor
from runtui.layout.absolute import AbsoluteLayout

WIDTH = 100
HEIGHT = 40


def build_scene(theme_name: str = "turbo_vision"):
    """Build the full demo scene and return a painted CellBuffer."""
    # Set up theme
    engine = ThemeEngine()
    engine.register(turbo_vision_theme)
    engine.register(dark_theme)
    engine.register(nord_theme)
    engine.set_theme(theme_name)

    buf = CellBuffer(WIDTH, HEIGHT)
    painter = Painter(buf, Rect(0, 0, WIDTH, HEIGHT))

    theme = engine

    def tc(slot, fallback=Color.DEFAULT):
        return theme.get_color(slot, fallback)

    def tg(slot, fallback=""):
        return theme.get_glyph(slot, fallback)

    # === DESKTOP BACKGROUND ===
    desktop_bg = tc("desktop.bg", Color.BLUE)
    desktop_fg = tc("desktop.fg", Color.CYAN)
    for row in range(1, HEIGHT - 1):
        for col in range(WIDTH):
            ch = "░" if (row + col) % 2 == 0 else " "
            buf.put_char(col, row, ch, desktop_fg, desktop_bg)

    # === MENU BAR ===
    menu_bg = tc("menu.bg", Color.CYAN)
    menu_fg = tc("menu.fg", Color.BLACK)
    sel_bg = tc("menu.selected.bg", Color.GREEN)
    sel_fg = tc("menu.selected.fg", Color.BLACK)
    hotkey_fg = tc("menu.hotkey", Color.RED)

    buf.fill_rect(Rect(0, 0, WIDTH, 1), " ", menu_fg, menu_bg)
    x = 1
    for i, title in enumerate([" File ", " Windows ", " Theme ", " Help "]):
        if i == 0:
            buf.put_str(x, 0, title, sel_fg, sel_bg, Attrs.BOLD)
        else:
            buf.put_str(x, 0, title, menu_fg, menu_bg)
        x += string_width(title)

    # File menu dropdown (open)
    dm_x = 1
    dm_y = 1
    dm_w = 24
    dm_items = [
        ("New Window", "Ctrl+N"),
        ("Open...", "Ctrl+O"),
        ("Save As...", "Ctrl+S"),
        None,  # separator
        ("Exit", "Ctrl+Q"),
    ]
    dm_h = len(dm_items) + 2
    # Draw border
    painter.draw_border(dm_x, dm_y, dm_w, dm_h, BorderStyle.SINGLE, menu_fg, menu_bg)
    for row, item in enumerate(dm_items):
        iy = dm_y + 1 + row
        if item is None:
            buf.put_char(dm_x, iy, "├", menu_fg, menu_bg)
            for c in range(1, dm_w - 1):
                buf.put_char(dm_x + c, iy, "─", menu_fg, menu_bg)
            buf.put_char(dm_x + dm_w - 1, iy, "┤", menu_fg, menu_bg)
        else:
            label, shortcut = item
            is_sel = row == 0
            ibg = sel_bg if is_sel else menu_bg
            ifg = sel_fg if is_sel else menu_fg
            for c in range(1, dm_w - 1):
                buf.put_char(dm_x + c, iy, " ", ifg, ibg)
            buf.put_str(dm_x + 2, iy, label, ifg, ibg, Attrs.BOLD if is_sel else Attrs.NONE)
            buf.put_str(dm_x + dm_w - 2 - len(shortcut), iy, shortcut, hotkey_fg if not is_sel else ifg, ibg)
    # Shadow
    shadow = tc("window.shadow", Color.BRIGHT_BLACK)
    for r in range(1, dm_h + 1):
        buf.put_char(dm_x + dm_w, dm_y + r, " ", shadow, shadow)
        buf.put_char(dm_x + dm_w + 1, dm_y + r, " ", shadow, shadow)
    for c in range(2, dm_w + 2):
        buf.put_char(dm_x + c, dm_y + dm_h, " ", shadow, shadow)

    # === WINDOW 1: Input Widgets ===
    def draw_window(wx, wy, ww, wh, title, active=False, border=BorderStyle.SINGLE):
        wbg = tc("window.bg", Color.CYAN)
        wfg = tc("window.fg", Color.BLACK)
        if active:
            bfg = tc("window.active.border", Color.WHITE)
            tfg = tc("window.active.title", Color.WHITE)
            tbg = tc("window.active.title.bg", Color.CYAN)
            bstyle = BorderStyle.DOUBLE
        else:
            bfg = tc("window.border", Color.BLACK)
            tfg = tc("window.title", Color.BLACK)
            tbg = tc("window.title.bg", Color.CYAN)
            bstyle = border

        buf.fill_rect(Rect(wx, wy, ww, wh), " ", wfg, wbg)
        painter.draw_border(wx, wy, ww, wh, bstyle, bfg, wbg)

        # Title bar
        for c in range(1, ww - 1):
            buf.put_char(wx + c, wy, " ", tfg, tbg)

        # Buttons
        btn_fg = tc("window.button", tfg)
        close_g = tg("window.close", "[x]")
        min_g = tg("window.minimize", "[_]")
        max_g = tg("window.maximize", "[^]")
        bx = wx + 1
        buf.put_str(bx, wy, close_g, btn_fg, tbg)
        bx += len(close_g)
        buf.put_str(bx, wy, min_g, btn_fg, tbg)
        bx += len(min_g)
        buf.put_str(bx, wy, max_g, btn_fg, tbg)
        bx += len(max_g)

        # Title centered
        title_space = ww - (bx - wx) - 1
        tw = string_width(title)
        toff = max(0, (title_space - tw) // 2)
        buf.put_str(bx + toff, wy, title, tfg, tbg, Attrs.BOLD if active else Attrs.NONE)

        # Shadow
        for r in range(1, wh + 1):
            buf.put_char(wx + ww, wy + r, " ", shadow, shadow)
            buf.put_char(wx + ww + 1, wy + r, " ", shadow, shadow)
        for c in range(2, ww + 2):
            buf.put_char(wx + c, wy + wh, " ", shadow, shadow)

        return Rect(wx + 1, wy + 1, ww - 2, wh - 2)

    # Window 1: Input Widgets (active)
    cr = draw_window(2, 8, 42, 20, "Input Widgets", active=True)
    cx, cy = cr.x, cr.y
    wbg = tc("window.bg", Color.CYAN)
    wfg = tc("window.fg", Color.BLACK)
    ifg = tc("input.focused.fg", Color.WHITE)
    ibg = tc("input.focused.bg", Color.BLUE)
    nifg = tc("input.fg", Color.BLACK)
    nibg = tc("input.bg", Color.CYAN)

    # Name field
    buf.put_str(cx + 1, cy, "Name:", wfg, wbg, Attrs.BOLD)
    buf.fill_rect(Rect(cx + 11, cy, 26, 1), " ", ifg, ibg)
    buf.put_str(cx + 11, cy, "John Doe", ifg, ibg)
    buf.put_char(cx + 19, cy, " ", Color.BLACK, ifg, Attrs.REVERSE)  # cursor

    # Password
    buf.put_str(cx + 1, cy + 2, "Password:", wfg, wbg, Attrs.BOLD)
    buf.fill_rect(Rect(cx + 11, cy + 2, 26, 1), " ", nifg, nibg)
    buf.put_str(cx + 11, cy + 2, "●●●●●●●●", nifg, nibg)

    # Checkboxes
    cb_fg = tc("checkbox.fg", Color.BLACK)
    cb_bg = tc("checkbox.bg", Color.CYAN)
    cb_checked = tg("checkbox.checked", "[X]")
    cb_unchecked = tg("checkbox.unchecked", "[ ]")
    buf.put_str(cx + 1, cy + 4, f"{cb_checked} Bold", cb_fg, cb_bg, Attrs.BOLD)
    buf.put_str(cx + 17, cy + 4, f"{cb_unchecked} Italic", cb_fg, cb_bg)

    # Radio buttons
    r_sel = tg("radio.selected", "(*)")
    r_unsel = tg("radio.unselected", "( )")
    buf.put_str(cx + 1, cy + 6, f"{r_sel} Option A", cb_fg, cb_bg)
    buf.put_str(cx + 1, cy + 7, f"{r_unsel} Option B", cb_fg, cb_bg)
    buf.put_str(cx + 1, cy + 8, f"{r_unsel} Option C", cb_fg, cb_bg)

    # Dropdown
    buf.put_str(cx + 1, cy + 10, "Color:", wfg, wbg, Attrs.BOLD)
    dd_arrow = tg("dropdown.arrow", "▼")
    buf.fill_rect(Rect(cx + 11, cy + 10, 26, 1), " ", nifg, nibg)
    buf.put_str(cx + 12, cy + 10, "Red", nifg, nibg)
    buf.put_char(cx + 35, cy + 10, dd_arrow, nifg, nibg)

    # Progress bar
    buf.put_str(cx + 1, cy + 12, "Progress:", wfg, wbg, Attrs.BOLD)
    pb_w = 26
    filled = int(pb_w * 0.65)
    for c in range(pb_w):
        if c < filled:
            buf.put_char(cx + 11 + c, cy + 12, "█", Color.GREEN, Color.DEFAULT)
        else:
            buf.put_char(cx + 11 + c, cy + 12, "░", Color.BRIGHT_BLACK, Color.DEFAULT)
    pct = " 65% "
    px = cx + 11 + (pb_w - len(pct)) // 2
    for i, ch in enumerate(pct):
        col = px + i - (cx + 11)
        if col < filled:
            buf.put_char(px + i, cy + 12, ch, Color.BLACK, Color.GREEN, Attrs.BOLD)
        else:
            buf.put_char(px + i, cy + 12, ch, Color.WHITE, Color.DEFAULT, Attrs.BOLD)

    # Buttons
    btn_fg_color = tc("button.fg", Color.BLACK)
    btn_bg_color = tc("button.bg", Color.WHITE)
    btn_focus_fg = tc("button.focused.fg", Color.WHITE)
    btn_focus_bg = tc("button.focused.bg", Color.CYAN)
    buf.fill_rect(Rect(cx + 5, cy + 14, 12, 1), " ", btn_focus_fg, btn_focus_bg)
    buf.put_str(cx + 5, cy + 14, "  [ OK ]    ", btn_focus_fg, btn_focus_bg, Attrs.BOLD)
    buf.fill_rect(Rect(cx + 19, cy + 14, 14, 1), " ", btn_fg_color, btn_bg_color)
    buf.put_str(cx + 19, cy + 14, " [ Cancel ] ", btn_fg_color, btn_bg_color)

    # === WINDOW 2: List Demo ===
    cr2 = draw_window(46, 8, 34, 16, "List Demo", active=False)
    cx2, cy2 = cr2.x, cr2.y
    list_fg = tc("listbox.fg", Color.BLACK)
    list_bg = tc("listbox.bg", Color.CYAN)
    list_sel_fg = tc("listbox.selected.fg", Color.WHITE)
    list_sel_bg = tc("listbox.selected.bg", Color.GREEN)

    items = [
        "Item 1: ★ Sample entry",
        "Item 2: ○ Sample entry",
        "Item 3: ○ Sample entry",
        "Item 4: ★ Sample entry",
        "Item 5: ○ Sample entry",
        "Item 6: ○ Sample entry",
        "Item 7: ★ Sample entry",
        "Item 8: ○ Sample entry",
        "Item 9: ○ Sample entry",
        "Item 10: ★ Sample entry",
        "Item 11: ○ Sample entry",
        "Item 12: ○ Sample entry",
    ]
    for i, item in enumerate(items):
        if i >= 12:
            break
        iy = cy2 + i
        is_sel = i == 0
        ifg_l = list_sel_fg if is_sel else list_fg
        ibg_l = list_sel_bg if is_sel else list_bg
        buf.fill_rect(Rect(cx2, iy, 30, 1), " ", ifg_l, ibg_l)
        buf.put_str(cx2, iy, truncate_to_width(item, 30), ifg_l, ibg_l,
                    Attrs.BOLD if is_sel else Attrs.NONE)

    # Scrollbar
    sb_track = tg("scrollbar.track", "░")
    sb_thumb = tg("scrollbar.thumb", "█")
    sb_up = tg("scrollbar.up", "▲")
    sb_down = tg("scrollbar.down", "▼")
    sb_fg = tc("scrollbar.arrow", Color.WHITE)
    sb_thumb_fg = tc("scrollbar.thumb", Color.WHITE)
    sb_track_fg = tc("scrollbar.track", Color.BRIGHT_BLACK)
    sbx = cx2 + 31
    buf.put_char(sbx, cy2, sb_up, sb_fg, wbg)
    for r in range(1, 11):
        buf.put_char(sbx, cy2 + r, sb_track, sb_track_fg, wbg)
    # Thumb at top
    for r in range(1, 4):
        buf.put_char(sbx, cy2 + r, sb_thumb, sb_thumb_fg, wbg)
    buf.put_char(sbx, cy2 + 11, sb_down, sb_fg, wbg)

    buf.put_str(cx2, cy2 + 13, "  20 items", list_fg, wbg)

    # === WINDOW 3: Calendar ===
    cr3 = draw_window(46, 25, 28, 13, "Calendar", active=False)
    cx3, cy3 = cr3.x, cr3.y
    cal_fg = tc("calendar.fg", Color.BLACK)
    cal_bg = tc("calendar.bg", Color.CYAN)
    cal_header = tc("calendar.header", Color.WHITE)
    cal_today = tc("calendar.today", Color.YELLOW)
    cal_sel = tc("calendar.selected", Color.GREEN)

    import calendar
    today = datetime.date.today()
    month_name = calendar.month_name[today.month]
    title_str = f"{month_name} {today.year}"
    buf.put_str(cx3 + (24 - len(title_str)) // 2, cy3, title_str, cal_header, cal_bg, Attrs.BOLD)
    buf.put_str(cx3, cy3 + 1, "Mo Tu We Th Fr Sa Su", cal_header, cal_bg)

    cal_grid = calendar.monthcalendar(today.year, today.month)
    for wi, week in enumerate(cal_grid):
        for di, day in enumerate(week):
            if day == 0:
                continue
            dx = cx3 + di * 3
            dy = cy3 + 2 + wi
            day_str = f"{day:2d}"
            if day == today.day:
                buf.put_str(dx, dy, day_str, cal_fg, cal_sel, Attrs.BOLD)
            else:
                buf.put_str(dx, dy, day_str, cal_fg, cal_bg)

    buf.put_str(cx3, cy3 + 9, "[<]", cal_fg, cal_bg)
    buf.put_str(cx3 + 8, cy3 + 9, "[Today]", cal_fg, cal_bg)
    buf.put_str(cx3 + 21, cy3 + 9, "[>]", cal_fg, cal_bg)

    # === WINDOW 4: Text Editor ===
    cr4 = draw_window(2, 29, 42, 10, "Text Editor", active=False)
    cx4, cy4 = cr4.x, cr4.y

    editor_lines = [
        "# Welcome to runtui!",
        "",
        "This is a multi-line text editor.",
        "It supports:",
        "  - Arrow key navigation",
        "  - Backspace and Delete",
        "  - Home/End/PgUp/PgDn",
        "  - Undo (Ctrl+Z)",
    ]
    for i, line in enumerate(editor_lines):
        if i >= 8:
            break
        buf.put_str(cx4, cy4 + i, truncate_to_width(line, 38), nifg, nibg)
        # Fill rest of line
        sw = string_width(line)
        for c in range(sw, 38):
            buf.put_char(cx4 + c, cy4 + i, " ", nifg, nibg)

    # === TASKBAR ===
    tb_bg = tc("taskbar.bg", Color.BRIGHT_BLACK)
    tb_fg = tc("taskbar.fg", Color.WHITE)
    tb_active_bg = tc("taskbar.active.bg", Color.BLUE)
    tb_active_fg = tc("taskbar.active.fg", Color.WHITE)

    buf.fill_rect(Rect(0, HEIGHT - 1, WIDTH, 1), " ", tb_fg, tb_bg)

    tx = 1
    windows_info = [
        ("Input Widgets", True),
        ("List Demo", False),
        ("Calendar", False),
        ("Text Editor", False),
    ]
    for name, is_active in windows_info:
        label = f" {name} "
        if is_active:
            buf.put_str(tx, HEIGHT - 1, label, tb_active_fg, tb_active_bg, Attrs.BOLD)
        else:
            buf.put_str(tx, HEIGHT - 1, label, tb_fg, tb_bg)
        tx += string_width(label) + 1

    # Clock
    import time
    clock = time.strftime(" %H:%M ")
    buf.put_str(WIDTH - len(clock), HEIGHT - 1, clock, tb_fg, tb_bg)

    # === MOUSE CURSOR ===
    buf.put_char(25, 15, "▶", Color.WHITE, Color.BLACK, Attrs.BOLD)

    return buf


def render_ansi(buf: CellBuffer) -> str:
    """Convert a CellBuffer to ANSI escape sequence output."""
    output = []
    output.append("\x1b[0m")  # Reset

    for y in range(buf.height):
        last_fg = None
        last_bg = None
        last_attrs = None

        for x in range(buf.width):
            cell = buf.get(x, y)
            if cell.wide:
                continue

            # Update attrs if changed
            if cell.attrs != last_attrs:
                output.append("\x1b[0m")
                if cell.attrs != Attrs.NONE:
                    output.append(attrs_sequence(cell.attrs))
                last_fg = None
                last_bg = None
                last_attrs = cell.attrs

            if cell.fg != last_fg:
                output.append(cell.fg.fg_sequence())
                last_fg = cell.fg

            if cell.bg != last_bg:
                output.append(cell.bg.bg_sequence())
                last_bg = cell.bg

            output.append(cell.char if cell.char else " ")

        output.append("\x1b[0m\n")

    return "".join(output)


if __name__ == "__main__":
    theme = sys.argv[1] if len(sys.argv) > 1 else "turbo_vision"
    buf = build_scene(theme)
    print(render_ansi(buf))
