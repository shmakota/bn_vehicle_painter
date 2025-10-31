"""
Canvas widget for vehicle painting and editing.
"""

import tkinter as tk
from math import sqrt, floor
from tile_editor import TileEditorDialog


class VehicleCanvas(tk.Canvas):
    """Custom canvas for vehicle painting."""
    
    def __init__(self, parent, vehicle, tool_var, current_palette_char=None, palette=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.vehicle = vehicle
        self.tool_var = tool_var
        self.current_palette_char = current_palette_char
        self.palette = palette
        
        # Grid settings
        self.grid_size = 20  # Pixels per grid cell
        self.show_grid = True
        
        # Infinite scroll settings
        self.scroll_region_size = 100000  # Large scroll region for infinite scrolling
        
        # Drawing state
        self.is_drawing = False
        self.last_x = None
        self.last_y = None
        
        # Tile editor callback
        self.tile_editor_callback = None
        
        # Tooltip for hover
        self.tooltip = None
        self.current_hover_tile = None
        self.tooltip_window = None
        
        # Bind events
        self.bind("<Button-1>", self.on_click)
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<ButtonRelease-1>", self.on_release)
        self.bind("<Configure>", self.on_resize)
        self.bind("<Button-3>", self.on_right_click)  # Right-click for tile editor
        self.bind("<Motion>", self.on_motion)  # Mouse motion for tooltip
        self.bind("<Leave>", self.on_leave)  # Hide tooltip when mouse leaves
        
        # Bind scroll events to redraw grid
        self.bind("<MouseWheel>", lambda e: self.after_idle(self.draw_grid))
        
        # Bind arrow keys for navigation
        self.bind("<Key>", self.on_key_press)
        self.focus_set()  # Enable keyboard focus
        
        # Initial draw and set infinite scroll region
        self.update_scroll_region()
        self.redraw()
    
    def on_click(self, event):
        """Handle mouse click."""
        # Focus canvas for keyboard input
        self.focus_set()
        
        # Hide tooltip when clicking
        self.hide_tooltip()
        
        x, y = self.canvasx(event.x), self.canvasy(event.y)
        grid_x, grid_y = self.screen_to_grid(x, y)
        
        tool = self.tool_var.get()
        
        if tool == "paint":
            self.paint_cell(grid_x, grid_y)
        elif tool == "erase":
            self.erase_cell(grid_x, grid_y)
        elif tool == "select":
            # Open tile editor
            self.open_tile_editor(grid_x, grid_y)
        
        self.last_x = grid_x
        self.last_y = grid_y
        self.is_drawing = True
    
    def on_right_click(self, event):
        """Handle right-click - open tile editor."""
        x, y = self.canvasx(event.x), self.canvasy(event.y)
        grid_x, grid_y = self.screen_to_grid(x, y)
        self.open_tile_editor(grid_x, grid_y)
    
    def on_drag(self, event):
        """Handle mouse drag."""
        if not self.is_drawing:
            return
        
        # Hide tooltip while dragging
        self.hide_tooltip()
        
        x, y = self.canvasx(event.x), self.canvasy(event.y)
        grid_x, grid_y = self.screen_to_grid(x, y)
        
        # Only paint if moved to a new cell
        if grid_x != self.last_x or grid_y != self.last_y:
            tool = self.tool_var.get()
            
            if tool == "paint":
                self.paint_cell(grid_x, grid_y)
            elif tool == "erase":
                self.erase_cell(grid_x, grid_y)
            
            self.last_x = grid_x
            self.last_y = grid_y
    
    def on_release(self, event):
        """Handle mouse release."""
        self.is_drawing = False
        self.last_x = None
        self.last_y = None
    
    def on_motion(self, event):
        """Handle mouse motion - show tooltip with tile information."""
        # Don't show tooltip while dragging
        if self.is_drawing:
            return
        
        x, y = self.canvasx(event.x), self.canvasy(event.y)
        grid_x, grid_y = self.screen_to_grid(x, y)
        
        # Check if we're hovering over a different tile
        if (grid_x, grid_y) != self.current_hover_tile:
            self.current_hover_tile = (grid_x, grid_y)
            self.show_tooltip(grid_x, grid_y, event.x_root, event.y_root)
    
    def on_leave(self, event):
        """Handle mouse leaving canvas - hide tooltip."""
        self.hide_tooltip()
        self.current_hover_tile = None
    
    def on_key_press(self, event):
        """Handle keyboard input for arrow key navigation."""
        # Only handle arrow keys
        if event.keysym not in ['Up', 'Down', 'Left', 'Right']:
            return
        
        # Get current scroll position
        scroll_x = self.xview()[0]  # Returns (left, right) fraction
        scroll_y = self.yview()[0]
        
        # Get scroll region
        scroll_region = self.cget("scrollregion")
        if not scroll_region:
            return
        
        region = scroll_region.split()
        region_min_x = float(region[0])
        region_min_y = float(region[1])
        region_max_x = float(region[2])
        region_max_y = float(region[3])
        region_width = region_max_x - region_min_x
        region_height = region_max_y - region_min_y
        
        # Calculate one grid cell in scroll coordinates
        # One grid cell = grid_size pixels
        cell_scroll_x = (self.grid_size / region_width)
        cell_scroll_y = (self.grid_size / region_height)
        
        # Update scroll position based on arrow key
        if event.keysym == 'Up':
            new_y = max(0.0, scroll_y - cell_scroll_y)
            self.yview_moveto(new_y)
        elif event.keysym == 'Down':
            new_y = min(1.0, scroll_y + cell_scroll_y)
            self.yview_moveto(new_y)
        elif event.keysym == 'Left':
            new_x = max(0.0, scroll_x - cell_scroll_x)
            self.xview_moveto(new_x)
        elif event.keysym == 'Right':
            new_x = min(1.0, scroll_x + cell_scroll_x)
            self.xview_moveto(new_x)
        
        # Redraw grid after scrolling
        self.after_idle(self.draw_grid)
    
    def format_part_for_tooltip(self, part):
        """Format a part for tooltip display."""
        if 'parts' in part:
            parts_str = ", ".join(part['parts'])
            result = f"Parts: {parts_str}"
        elif 'part' in part:
            result = f"Part: {part['part']}"
        else:
            result = "Part: (unknown)"
        
        if 'fuel' in part:
            result += f"\n  Fuel: {part['fuel']}"
        
        return result
    
    def format_item_for_tooltip(self, item):
        """Format an item for tooltip display."""
        result = ""
        if 'item' in item:
            result += f"Item: {item['item']}"
        if 'item_groups' in item:
            if result:
                result += "\n"
            groups_str = ", ".join(item['item_groups'])
            result += f"Groups: {groups_str}"
        if 'chance' in item:
            if result:
                result += "\n"
            result += f"Chance: {item['chance']}%"
        
        return result
    
    def show_tooltip(self, grid_x, grid_y, screen_x, screen_y):
        """Show tooltip with tile information."""
        # Get parts and items at this tile
        parts = self.vehicle.get_parts_at(grid_x, grid_y)
        items = self.vehicle.get_items_at(grid_x, grid_y)
        
        # Hide existing tooltip
        self.hide_tooltip()
        
        # If no parts or items, don't show tooltip
        if not parts and not items:
            return
        
        # Build tooltip text
        lines = [f"Tile ({grid_x}, {grid_y}):"]
        
        if parts:
            lines.append("")
            lines.append("Parts:")
            for part in parts:
                lines.append(f"  • {self.format_part_for_tooltip(part)}")
        
        if items:
            lines.append("")
            lines.append("Items:")
            for item in items:
                item_text = self.format_item_for_tooltip(item)
                if item_text:
                    lines.append(f"  • {item_text}")
        
        # Create tooltip window
        tooltip_text = "\n".join(lines)
        
        self.tooltip_window = tk.Toplevel(self)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{screen_x + 10}+{screen_y + 10}")
        
        # Configure tooltip style
        tooltip_frame = tk.Frame(
            self.tooltip_window,
            bg="#FFFFCC",
            relief=tk.SOLID,
            borderwidth=1
        )
        tooltip_frame.pack(fill=tk.BOTH, expand=True)
        
        tooltip_label = tk.Label(
            tooltip_frame,
            text=tooltip_text,
            bg="#FFFFCC",
            fg="black",
            justify=tk.LEFT,
            font=("TkDefaultFont", 9),
            padx=5,
            pady=3
        )
        tooltip_label.pack()
        
        # Make sure tooltip is on top
        self.tooltip_window.lift()
        self.tooltip_window.attributes('-topmost', True)
    
    def hide_tooltip(self):
        """Hide the tooltip window."""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None
    
    def on_resize(self, event):
        """Handle canvas resize."""
        self.draw_grid()
        # Redraw cells but keep axis markers
        coords = set()
        if hasattr(self.vehicle, 'parts'):
            for part in self.vehicle.parts:
                if 'x' in part and 'y' in part:
                    coords.add((part['x'], part['y']))
        if hasattr(self.vehicle, 'items'):
            for item in self.vehicle.items:
                if 'x' in item and 'y' in item:
                    coords.add((item['x'], item['y']))
        for x, y in coords:
            self.draw_cell(x, y)
    
    def screen_to_grid(self, x, y):
        """Convert screen coordinates to grid coordinates.
        
        Args:
            x, y: Canvas coordinates (from canvasx/canvasy)
        
        Returns:
            (grid_x, grid_y): Grid coordinates
        """
        # Use floor division to handle negative coordinates correctly
        # int() truncates towards zero, but floor() rounds down for negatives
        # This ensures correct grid cell selection for negative coordinates
        grid_x = floor(x / self.grid_size)
        grid_y = floor(y / self.grid_size)
        return grid_x, grid_y
    
    def grid_to_screen(self, grid_x, grid_y):
        """Convert grid coordinates to screen coordinates."""
        x = grid_x * self.grid_size
        y = grid_y * self.grid_size
        return x, y
    
    def paint_cell(self, grid_x, grid_y):
        """Paint a cell at the given grid coordinates using palette."""
        if not self.palette or not self.current_palette_char:
            return
        
        # Create parts from palette character
        parts = self.palette.create_parts_from_char(self.current_palette_char, grid_x, grid_y)
        for part in parts:
            self.vehicle.add_part(part)
        
        # Create items from palette character
        items = self.palette.create_items_from_char(self.current_palette_char, grid_x, grid_y)
        for item in items:
            self.vehicle.add_item(item)
        
        # Update display and tooltip if hovering
        self.redraw()
        if self.current_hover_tile == (grid_x, grid_y):
            # Update tooltip if we're hovering over this tile
            self.update_idletasks()
            # Tooltip will update on next motion event
    
    def erase_cell(self, grid_x, grid_y):
        """Erase all parts and items at the given grid coordinates."""
        # Remove all parts at this location
        parts_to_remove = []
        for i, part in enumerate(self.vehicle.parts):
            if part.get('x') == grid_x and part.get('y') == grid_y:
                parts_to_remove.append(i)
        
        # Remove in reverse order to maintain indices
        for i in reversed(parts_to_remove):
            self.vehicle.remove_part(i)
        
        # Remove all items at this location
        items_to_remove = []
        for i, item in enumerate(self.vehicle.items):
            if item.get('x') == grid_x and item.get('y') == grid_y:
                items_to_remove.append(i)
        
        # Remove in reverse order
        for i in reversed(items_to_remove):
            self.vehicle.remove_item(i)
        
        # Update display and hide tooltip if we're on this tile
        self.redraw()
        if self.current_hover_tile == (grid_x, grid_y):
            self.hide_tooltip()
    
    def open_tile_editor(self, grid_x, grid_y):
        """Open the tile editor for the given coordinates."""
        def update_canvas():
            self.redraw()
            if self.tile_editor_callback:
                self.tile_editor_callback()
        
        TileEditorDialog(self.winfo_toplevel(), self.vehicle, grid_x, grid_y, update_canvas, self.palette)
    
    def draw_cell(self, grid_x, grid_y):
        """Draw a single cell based on vehicle parts."""
        x, y = self.grid_to_screen(grid_x, grid_y)
        
        # Remove existing cell drawing
        cell_id = f"cell_{grid_x}_{grid_y}"
        self.delete(cell_id)
        
        # Determine color based on parts
        parts = self.vehicle.get_parts_at(grid_x, grid_y)
        items = self.vehicle.get_items_at(grid_x, grid_y)
        
        if parts or items:
            # Has content - use light blue
            fill_color = "#ADD8E6"
            outline_color = "#4169E1"
            width = 2
        else:
            # Empty cell
            fill_color = "white"
            outline_color = "lightgray"
            width = 1
        
        # Draw filled rectangle
        self.create_rectangle(
            x, y,
            x + self.grid_size, y + self.grid_size,
            fill=fill_color,
            outline=outline_color,
            width=width,
            tags=(cell_id, "cell")
        )
        
        # Draw indicator if multiple parts
        if len(parts) > 1:
            # Draw a small indicator for multiple parts
            indicator_x = x + self.grid_size - 5
            indicator_y = y + 2
            self.create_oval(
                indicator_x - 3, indicator_y - 3,
                indicator_x + 3, indicator_y + 3,
                fill="orange",
                outline="darkorange",
                tags=(cell_id, "cell")  # Include "cell" tag so it gets deleted on redraw
            )
    
    def draw_grid(self):
        """Draw the grid lines with infinite scrolling and origin markers."""
        if not self.show_grid:
            return
        
        # Get visible area
        bbox = self.bbox(tk.ALL)
        if not bbox:
            # Use canvas size if no content
            width = self.winfo_width() or 800
            height = self.winfo_height() or 600
            view_x1, view_y1 = 0, 0
            view_x2, view_y2 = width, height
        else:
            # Get scroll position
            view_x1 = self.canvasx(0)
            view_y1 = self.canvasy(0)
            view_x2 = self.canvasx(self.winfo_width())
            view_y2 = self.canvasy(self.winfo_height())
        
        # Delete existing grid lines
        self.delete("grid")
        self.delete("axis")
        
        # Calculate grid bounds (with padding for scrolling)
        grid_x1 = int(view_x1 / self.grid_size) - 1
        grid_y1 = int(view_y1 / self.grid_size) - 1
        grid_x2 = int(view_x2 / self.grid_size) + 1
        grid_y2 = int(view_y2 / self.grid_size) + 1
        
        # Draw vertical grid lines
        for grid_x in range(grid_x1, grid_x2 + 1):
            x = grid_x * self.grid_size
            
            # Special handling for x=0 axis line
            if grid_x == 0:
                self.create_line(
                    x, view_y1 - self.scroll_region_size,
                    x, view_y2 + self.scroll_region_size,
                    fill="#FF6B6B",
                    width=2,
                    tags="axis"
                )
            else:
                self.create_line(
                    x, view_y1,
                    x, view_y2,
                    fill="lightgray",
                    width=1,
                    tags="grid"
                )
        
        # Draw horizontal grid lines
        for grid_y in range(grid_y1, grid_y2 + 1):
            y = grid_y * self.grid_size
            
            # Special handling for y=0 axis line
            if grid_y == 0:
                self.create_line(
                    view_x1 - self.scroll_region_size, y,
                    view_x2 + self.scroll_region_size, y,
                    fill="#FF6B6B",
                    width=2,
                    tags="axis"
                )
            else:
                self.create_line(
                    view_x1, y,
                    view_x2, y,
                    fill="lightgray",
                    width=1,
                    tags="grid"
                )
        
        # Draw origin marker (0,0 intersection)
        origin_x = 0
        origin_y = 0
        marker_size = 8
        self.create_oval(
            origin_x - marker_size, origin_y - marker_size,
            origin_x + marker_size, origin_y + marker_size,
            fill="#FF6B6B",
            outline="#CC0000",
            width=2,
            tags="axis"
        )
    
    def redraw(self):
        """Redraw the entire canvas."""
        # Delete only grid and cells, keep axis markers
        self.delete("grid")
        self.delete("cell")
        
        # Draw grid (which includes axis markers)
        self.draw_grid()
        
        # Get all unique coordinates with parts or items
        coords = set()
        if hasattr(self.vehicle, 'parts'):
            for part in self.vehicle.parts:
                if 'x' in part and 'y' in part:
                    coords.add((part['x'], part['y']))
        
        if hasattr(self.vehicle, 'items'):
            for item in self.vehicle.items:
                if 'x' in item and 'y' in item:
                    coords.add((item['x'], item['y']))
        
        # Draw each cell
        for x, y in coords:
            self.draw_cell(x, y)
        
        # Update scroll region for infinite scrolling
        self.update_scroll_region()
    
    def update_scroll_region(self):
        """Update the scroll region for infinite scrolling."""
        # Set a large scroll region centered around current view
        # This allows scrolling in all directions
        center = self.scroll_region_size // 2
        scroll_region = (
            -center, -center,
            center, center
        )
        self.config(scrollregion=scroll_region)
        
        # Redraw grid after scroll region changes
        self.after_idle(self.draw_grid)

