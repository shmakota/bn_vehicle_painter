"""
Canvas widget for vehicle painting and editing.
"""

import tkinter as tk
from math import sqrt, floor
import hashlib
import copy
from tile_editor import TileEditorDialog
# from tileset import TilesetLoader  # Disabled for now


class VehicleCanvas(tk.Canvas):
    """Custom canvas for vehicle painting."""
    
    def __init__(self, parent, vehicle, tool_var, current_palette_char=None, palette=None, char_var=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.vehicle = vehicle
        self.tool_var = tool_var
        self.current_palette_char = current_palette_char
        self.palette = palette
        self.char_var = char_var  # Reference to main app's char_var for UI updates
        self.zoom_callback = None  # Callback for zoom updates (e.g., to update UI label)
        self.coordinate_callback = None  # Callback for coordinate updates (e.g., to update UI label)
        
        # Grid settings
        self.base_grid_size = 16  # Base pixels per grid cell (at 100% zoom) - reduced from 20 for smaller cells
        self.zoom_level = 1.0  # Current zoom level (1.0 = 100%)
        self.min_zoom = 0.5  # Minimum zoom (50%)
        self.max_zoom = 4.0  # Maximum zoom (400%)
        self.grid_size = self.base_grid_size * self.zoom_level  # Current grid size
        self.show_grid = True
        
        # View rotation (in degrees: 0, 90, 180, 270)
        self.rotation = 0
        
        # Infinite scroll settings
        self.base_scroll_region_size = 2500  # Base scroll region size (at 100% zoom)
        # Scroll region size scales with zoom to maintain same logical tile coverage
        self.scroll_region_size = self.base_scroll_region_size  # Initialize to base size
        
        # Drawing state
        self.is_drawing = False
        self.last_x = None
        self.last_y = None
        self.square_start_x = None
        self.square_start_y = None
        
        # Panning state
        self.is_panning = False
        self.pan_start_x = None
        self.pan_start_y = None
        self.pan_scroll_x = None
        self.pan_scroll_y = None
        
        # Tile editor callback
        self.tile_editor_callback = None
        
        # Tooltip for hover
        self.tooltip = None
        self.current_hover_tile = None
        self.tooltip_window = None
        
        # Track mouse position for keyboard hotkeys
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        self.last_mouse_grid = (0, 0)
        
        # Undo/redo system
        self.undo_stack = []  # List of operations to undo
        self.redo_stack = []  # List of operations to redo
        self.max_history = 50  # Maximum number of undo operations
        self.current_operation = None  # Current operation being built (for drag operations)
        
        # Part color mapping for visual distinction
        self.part_colors = {}  # part_name -> color
        
        # Color palette for parts (bright, distinguishable colors)
        self.color_palette = [
            "#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", "#98D8C8",
            "#F7DC6F", "#BB8FCE", "#85C1E2", "#F8B739", "#EC7063",
            "#52BE80", "#5DADE2", "#F1948A", "#85C1E9", "#F5B041",
            "#82E0AA", "#AED6F1", "#F4D03F", "#A569BD", "#48C9B0"
        ]
        
        # Load tileset for vehicle parts (disabled for now)
        # try:
        #     self.tileset_loader = TilesetLoader()
        #     self._image_refs = []  # Store image references to prevent garbage collection
        # except Exception as e:
        #     print(f"Warning: Could not load tileset: {e}")
        #     import traceback
        #     traceback.print_exc()
        #     self.tileset_loader = None
        #     self._image_refs = []
        self.tileset_loader = None
        self._image_refs = []
        
        # Bind events
        self.bind("<Button-1>", self.on_click)
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<ButtonRelease-1>", self.on_release)
        self.bind("<Configure>", self.on_resize)
        self.bind("<Button-2>", self.on_middle_click)  # Middle-click for tile editor
        self.bind("<Button-3>", self.on_right_click)  # Right-click for erase
        self.bind("<B3-Motion>", self.on_right_drag)  # Right-drag for continuous erase
        self.bind("<ButtonRelease-3>", self.on_right_release)  # Right-click release
        self.bind("<Motion>", self.on_motion)  # Mouse motion for tooltip
        self.bind("<Leave>", self.on_leave)  # Hide tooltip when mouse leaves
        
        # Bind scroll events for zooming
        # Regular mouse wheel zooms, Ctrl+mouse wheel also zooms
        self.bind("<MouseWheel>", self.on_zoom_wheel)
        self.bind("<Control-MouseWheel>", self.on_zoom_wheel)
        # Linux button events
        self.bind("<Button-4>", self.on_zoom_wheel)
        self.bind("<Button-5>", self.on_zoom_wheel)
        
        # Bind arrow keys for navigation
        self.bind("<Key>", self.on_key_press)
        # Bind Ctrl+Z and Ctrl+Y for undo/redo
        self.bind("<Control-z>", self.on_undo)
        self.bind("<Control-y>", self.on_redo)
        self.bind("<Control-Z>", self.on_undo)  # Also handle Shift+Ctrl+Z
        self.focus_set()  # Enable keyboard focus
        
        # Initial draw and set infinite scroll region
        self.update_scroll_region()
        self.redraw()
    
    def save_tile_state(self, grid_x, grid_y):
        """Save the current state of a tile (parts and items at that location).
        
        Returns:
            dict: State dictionary with 'x', 'y', 'parts', and 'items' keys
        """
        parts = self.vehicle.get_parts_at(grid_x, grid_y)
        items = self.vehicle.get_items_at(grid_x, grid_y)
        
        # Deep copy to avoid reference issues
        return {
            'x': grid_x,
            'y': grid_y,
            'parts': copy.deepcopy(parts),
            'items': copy.deepcopy(items)
        }
    
    def save_tiles_state(self, tile_coords):
        """Save state for multiple tiles.
        
        Args:
            tile_coords: List of (x, y) tuples
            
        Returns:
            list: List of state dictionaries
        """
        states = []
        for x, y in tile_coords:
            states.append(self.save_tile_state(x, y))
        return states
    
    def restore_tile_state(self, state):
        """Restore a tile to a previous state.
        
        Args:
            state: State dictionary with 'x', 'y', 'parts', and 'items'
        """
        grid_x = state['x']
        grid_y = state['y']
        
        # Remove all current parts at this location
        parts_to_remove = []
        for i, part in enumerate(self.vehicle.parts):
            if part.get('x') == grid_x and part.get('y') == grid_y:
                parts_to_remove.append(i)
        
        for i in reversed(parts_to_remove):
            self.vehicle.remove_part(i)
        
        # Remove all current items at this location
        items_to_remove = []
        for i, item in enumerate(self.vehicle.items):
            if item.get('x') == grid_x and item.get('y') == grid_y:
                items_to_remove.append(i)
        
        for i in reversed(items_to_remove):
            self.vehicle.remove_item(i)
        
        # Add back the saved parts
        for part in state['parts']:
            self.vehicle.add_part(part)
        
        # Add back the saved items
        for item in state['items']:
            self.vehicle.add_item(item)
        
        # Redraw the cell
        self.draw_cell(grid_x, grid_y)
    
    def restore_tiles_state(self, states):
        """Restore multiple tiles to previous states.
        
        Args:
            states: List of state dictionaries
        """
        for state in states:
            self.restore_tile_state(state)
        
        # Redraw grid after restoring
        self.draw_grid()
    
    def push_operation(self, before_states, after_states):
        """Push an operation onto the undo stack.
        
        Args:
            before_states: List of tile states before the operation
            after_states: List of tile states after the operation
        """
        # Create operation entry
        operation = {
            'before': before_states,
            'after': after_states
        }
        
        # Add to undo stack
        self.undo_stack.append(operation)
        
        # Limit stack size
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)
        
        # Clear redo stack when new operation is performed
        self.redo_stack = []
    
    def undo(self):
        """Undo the last operation."""
        if not self.undo_stack:
            return False
        
        # Pop the last operation
        operation = self.undo_stack.pop()
        
        # Restore the 'before' state
        self.restore_tiles_state(operation['before'])
        
        # Push to redo stack
        self.redo_stack.append(operation)
        
        # Update parts count if callback is set
        if self.tile_editor_callback:
            self.tile_editor_callback()
        
        return True
    
    def redo(self):
        """Redo the last undone operation."""
        if not self.redo_stack:
            return False
        
        # Pop the last redo operation
        operation = self.redo_stack.pop()
        
        # Restore the 'after' state
        self.restore_tiles_state(operation['after'])
        
        # Push back to undo stack
        self.undo_stack.append(operation)
        
        # Update parts count if callback is set
        if self.tile_editor_callback:
            self.tile_editor_callback()
        
        return True
    
    def on_undo(self, event=None):
        """Handle undo keyboard shortcut."""
        if self.undo():
            return "break"  # Prevent default handling
        return None
    
    def on_redo(self, event=None):
        """Handle redo keyboard shortcut."""
        if self.redo():
            return "break"  # Prevent default handling
        return None
    
    def clear_history(self):
        """Clear the undo/redo history."""
        self.undo_stack = []
        self.redo_stack = []
        self.current_operation = None
    
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
            self.last_x = grid_x
            self.last_y = grid_y
            self.is_drawing = True
        elif tool == "erase":
            self.erase_cell(grid_x, grid_y)
            self.last_x = grid_x
            self.last_y = grid_y
            self.is_drawing = True
        elif tool == "select":
            # Finalize any ongoing operation before opening editor
            self.finalize_operation()
            # Open tile editor
            self.open_tile_editor(grid_x, grid_y)
        elif tool == "square":
            # Finalize any ongoing operation
            self.finalize_operation()
            # Start square/rectangle drawing
            self.square_start_x = grid_x
            self.square_start_y = grid_y
            self.last_x = grid_x
            self.last_y = grid_y
            self.is_drawing = True
        elif tool == "square_erase":
            # Finalize any ongoing operation
            self.finalize_operation()
            # Start square/rectangle erasing
            self.square_start_x = grid_x
            self.square_start_y = grid_y
            self.last_x = grid_x
            self.last_y = grid_y
            self.is_drawing = True
        elif tool == "pan":
            # Start panning
            self.start_pan(event.x, event.y)
    
    def on_right_click(self, event):
        """Handle right-click - erase tile."""
        # Focus canvas for keyboard input
        self.focus_set()
        
        # Hide tooltip when clicking
        self.hide_tooltip()
        
        x, y = self.canvasx(event.x), self.canvasy(event.y)
        grid_x, grid_y = self.screen_to_grid(x, y)
        
        # Erase the tile
        self.erase_cell(grid_x, grid_y)
        
        self.last_x = grid_x
        self.last_y = grid_y
        self.is_drawing = True
    
    def on_right_drag(self, event):
        """Handle right-click drag - continuous erase."""
        if not self.is_drawing:
            return
        
        # Hide tooltip while dragging
        self.hide_tooltip()
        
        x, y = self.canvasx(event.x), self.canvasy(event.y)
        grid_x, grid_y = self.screen_to_grid(x, y)
        
        # Only erase if moved to a new cell
        if grid_x != self.last_x or grid_y != self.last_y:
            self.erase_cell(grid_x, grid_y)
            
            self.last_x = grid_x
            self.last_y = grid_y
    
    def on_right_release(self, event):
        """Handle right-click release."""
        # Finalize any ongoing operation (for erase drags)
        self.finalize_operation()
        
        self.is_drawing = False
        self.last_x = None
        self.last_y = None
    
    def on_middle_click(self, event):
        """Handle middle-click - open tile editor."""
        x, y = self.canvasx(event.x), self.canvasy(event.y)
        grid_x, grid_y = self.screen_to_grid(x, y)
        self.open_tile_editor(grid_x, grid_y)
    
    def start_pan(self, screen_x, screen_y):
        """Start panning operation."""
        self.is_panning = True
        self.pan_start_x = screen_x
        self.pan_start_y = screen_y
        
        # Store initial scroll position
        self.pan_scroll_x = self.xview()[0]
        self.pan_scroll_y = self.yview()[0]
        
        # Hide tooltip during panning
        self.hide_tooltip()
        
        # Mark as drawing to prevent other operations
        self.is_drawing = True
    
    def do_pan(self, screen_x, screen_y):
        """Perform panning based on mouse movement."""
        if not self.is_panning:
            return
        
        # Calculate mouse movement delta
        delta_x = screen_x - self.pan_start_x
        delta_y = screen_y - self.pan_start_y
        
        # Get scroll region to calculate scroll deltas
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
        
        # Get canvas dimensions
        canvas_width = self.winfo_width()
        canvas_height = self.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            return
        
        # Calculate scroll deltas (inverse of mouse movement - dragging left scrolls right)
        scroll_delta_x = -delta_x / region_width
        scroll_delta_y = -delta_y / region_height
        
        # Update scroll position
        new_scroll_x = self.pan_scroll_x + scroll_delta_x
        new_scroll_y = self.pan_scroll_y + scroll_delta_y
        
        # Clamp to valid range
        new_scroll_x = max(0.0, min(1.0, new_scroll_x))
        new_scroll_y = max(0.0, min(1.0, new_scroll_y))
        
        self.xview_moveto(new_scroll_x)
        self.yview_moveto(new_scroll_y)
        
        # Redraw grid after panning
        self.after_idle(self.draw_grid)
    
    def stop_pan(self):
        """Stop panning operation."""
        self.is_panning = False
        self.pan_start_x = None
        self.pan_start_y = None
        self.pan_scroll_x = None
        self.pan_scroll_y = None
        self.is_drawing = False
    
    
    def on_drag(self, event):
        """Handle mouse drag."""
        if not self.is_drawing:
            return
        
        # Hide tooltip while dragging
        self.hide_tooltip()
        
        x, y = self.canvasx(event.x), self.canvasy(event.y)
        grid_x, grid_y = self.screen_to_grid(x, y)
        
        tool = self.tool_var.get()
        
        if tool == "pan":
            # Handle panning
            self.do_pan(event.x, event.y)
        elif tool == "square" or tool == "square_erase":
            # For square/square_erase tools, just update the end position - we'll fill/erase on release
            self.last_x = grid_x
            self.last_y = grid_y
        elif grid_x != self.last_x or grid_y != self.last_y:
            # Only paint/erase if moved to a new cell
            if tool == "paint":
                self.paint_cell(grid_x, grid_y)
            elif tool == "erase":
                self.erase_cell(grid_x, grid_y)
            
            self.last_x = grid_x
            self.last_y = grid_y
    
    def finalize_operation(self):
        """Finalize the current operation by saving after states and pushing to undo stack."""
        if self.current_operation is None:
            return
        
        # Save after states for all affected tiles
        after_states = []
        for x, y in self.current_operation['affected_tiles']:
            after_states.append(self.save_tile_state(x, y))
        
        # Push operation to undo stack
        if self.current_operation['before_states'] or after_states:
            self.push_operation(
                self.current_operation['before_states'],
                after_states
            )
        
        # Clear current operation
        self.current_operation = None
    
    def on_release(self, event):
        """Handle mouse release."""
        tool = self.tool_var.get()
        
        if tool == "square" and self.square_start_x is not None and self.square_start_y is not None:
            # Fill the rectangle/square area
            x, y = self.canvasx(event.x), self.canvasy(event.y)
            end_x, end_y = self.screen_to_grid(x, y)
            
            self.fill_rectangle(
                self.square_start_x, self.square_start_y,
                end_x, end_y
            )
            
            self.square_start_x = None
            self.square_start_y = None
        elif tool == "square_erase" and self.square_start_x is not None and self.square_start_y is not None:
            # Erase the rectangle/square area
            x, y = self.canvasx(event.x), self.canvasy(event.y)
            end_x, end_y = self.screen_to_grid(x, y)
            
            self.erase_rectangle(
                self.square_start_x, self.square_start_y,
                end_x, end_y
            )
            
            self.square_start_x = None
            self.square_start_y = None
        
        tool = self.tool_var.get()
        
        if tool == "pan":
            # Stop panning
            self.stop_pan()
        else:
            # Finalize any ongoing operation (for paint/erase drags)
            self.finalize_operation()
        
        self.is_drawing = False
        self.last_x = None
        self.last_y = None
    
    def on_motion(self, event):
        """Handle mouse motion - show tooltip with tile information."""
        # Don't show tooltip while dragging or panning
        if self.is_drawing or self.is_panning:
            return
        
        x, y = self.canvasx(event.x), self.canvasy(event.y)
        grid_x, grid_y = self.screen_to_grid(x, y)
        
        # Track mouse position for keyboard hotkeys
        self.last_mouse_x = x
        self.last_mouse_y = y
        self.last_mouse_grid = (grid_x, grid_y)
        
        # Update coordinate display if callback is set
        if self.coordinate_callback:
            self.coordinate_callback(grid_x, grid_y)
        
        # Check if we're hovering over a different tile
        if (grid_x, grid_y) != self.current_hover_tile:
            self.current_hover_tile = (grid_x, grid_y)
            self.show_tooltip(grid_x, grid_y, event.x_root, event.y_root)
    
    def on_leave(self, event):
        """Handle mouse leaving canvas - hide tooltip."""
        self.hide_tooltip()
        self.current_hover_tile = None
        # Clear coordinate display when mouse leaves
        if self.coordinate_callback:
            # Pass None to indicate mouse is outside canvas
            self.coordinate_callback(None, None)
    
    def on_key_press(self, event):
        """Handle keyboard input for arrow key navigation and palette hotkeys."""
        # Handle arrow keys for navigation
        if event.keysym in ['Up', 'Down', 'Left', 'Right']:
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
            return
        
        # Handle palette hotkeys - check if key matches a palette character
        if not self.palette:
            return
        
        # Get the character from the key press
        char = event.char
        if not char or len(char) != 1:
            return
        
        # Check if this character exists in the palette
        if char not in self.palette.vehicle_part and char not in self.palette.items:
            return
        
        # Switch to this palette character and automatically switch to paint mode
        self.current_palette_char = char
        
        # Switch to paint tool automatically
        if self.tool_var:
            self.tool_var.set("paint")
        
        # Update UI if char_var is available
        if self.char_var:
            try:
                self.char_var.set(char)
            except:
                pass
    
    def format_part_for_tooltip(self, part):
        """Format a part for tooltip display."""
        if 'parts' in part:
            # Handle parts list - convert all items to strings
            parts_list = []
            for p in part['parts']:
                if isinstance(p, str):
                    parts_list.append(p)
                elif isinstance(p, dict):
                    # If it's a dict, try to extract meaningful info
                    if 'part' in p:
                        parts_list.append(p['part'])
                    else:
                        parts_list.append(str(p))
                else:
                    parts_list.append(str(p))
            parts_str = ", ".join(parts_list)
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
        if 'items' in item:
            # Handle "items" (plural) field - can be string or list
            if result:
                result += "\n"
            items_value = item['items']
            if isinstance(items_value, list):
                items_str = ", ".join(str(i) for i in items_value)
                result += f"Items: {items_str}"
            else:
                result += f"Items: {items_value}"
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
                # Expand multi-part entries to show each part separately
                if 'parts' in part:
                    # Extract individual part names
                    parts_list = []
                    for p in part['parts']:
                        if isinstance(p, str):
                            parts_list.append(p)
                        elif isinstance(p, dict):
                            if 'part' in p:
                                parts_list.append(p['part'])
                            elif 'parts' in p:
                                # Nested parts - flatten
                                for nested_p in p['parts']:
                                    if isinstance(nested_p, str):
                                        parts_list.append(nested_p)
                                    elif isinstance(nested_p, dict) and 'part' in nested_p:
                                        parts_list.append(nested_p['part'])
                    
                    # Show each part separately
                    for part_name in parts_list:
                        part_line = f"  • Part: {part_name}"
                        if 'fuel' in part:
                            part_line += f" | Fuel: {part['fuel']}"
                        lines.append(part_line)
                elif 'part' in part:
                    part_line = f"  • Part: {part['part']}"
                    if 'fuel' in part:
                        part_line += f" | Fuel: {part['fuel']}"
                    lines.append(part_line)
                else:
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
    
    def rotate_coordinates(self, x, y):
        """Rotate coordinates based on current view rotation.
        
        Args:
            x, y: Original grid coordinates
            
        Returns:
            (rx, ry): Rotated coordinates
        """
        if self.rotation == 0:
            return x, y
        elif self.rotation == 90:
            # 90° clockwise: (x, y) -> (-y, x)
            return -y, x
        elif self.rotation == 180:
            # 180°: (x, y) -> (-x, -y)
            return -x, -y
        elif self.rotation == 270:
            # 270° clockwise (90° CCW): (x, y) -> (y, -x)
            return y, -x
        else:
            return x, y
    
    def unrotate_coordinates(self, rx, ry):
        """Convert rotated coordinates back to original grid coordinates.
        
        Args:
            rx, ry: Rotated coordinates
            
        Returns:
            (x, y): Original grid coordinates
        """
        if self.rotation == 0:
            return rx, ry
        elif self.rotation == 90:
            # Inverse of 90° CW: (-y, x) -> (x, y), so (rx, ry) -> (ry, -rx)
            return ry, -rx
        elif self.rotation == 180:
            # Inverse of 180°: (-x, -y) -> (x, y), so (rx, ry) -> (-rx, -ry)
            return -rx, -ry
        elif self.rotation == 270:
            # Inverse of 270° CW: (y, -x) -> (x, y), so (rx, ry) -> (-ry, rx)
            return -ry, rx
        else:
            return rx, ry
    
    def screen_to_grid(self, x, y):
        """Convert screen coordinates to grid coordinates.
        
        Args:
            x, y: Canvas coordinates (from canvasx/canvasy)
        
        Returns:
            (grid_x, grid_y): Grid coordinates (unrotated, original)
        """
        # Use floor division to handle negative coordinates correctly
        # int() truncates towards zero, but floor() rounds down for negatives
        # This ensures correct grid cell selection for negative coordinates
        screen_grid_x = floor(x / self.grid_size)
        screen_grid_y = floor(y / self.grid_size)
        
        # Convert from screen grid coordinates to actual grid coordinates
        grid_x, grid_y = self.unrotate_coordinates(screen_grid_x, screen_grid_y)
        return grid_x, grid_y
    
    def grid_to_screen(self, grid_x, grid_y):
        """Convert grid coordinates to screen coordinates."""
        # Rotate the grid coordinates first
        rx, ry = self.rotate_coordinates(grid_x, grid_y)
        # Then convert to screen coordinates
        x = rx * self.grid_size
        y = ry * self.grid_size
        return x, y
    
    def rotate_view(self):
        """Rotate the view by 90 degrees clockwise."""
        self.rotation = (self.rotation + 90) % 360
        self.redraw()
        
        # Notify callback if set
        if self.zoom_callback:  # Reusing zoom_callback, could be renamed to view_callback
            self.zoom_callback()
    
    def get_rotation(self):
        """Get current rotation in degrees."""
        return self.rotation
    
    def paint_cell(self, grid_x, grid_y, save_state=True):
        """Paint a cell at the given grid coordinates using palette.
        
        Args:
            grid_x, grid_y: Grid coordinates
            save_state: If True and this is the start of an operation, save state before
        """
        if not self.palette or not self.current_palette_char:
            return
        
        # Start a new operation if not already in one
        if save_state and self.current_operation is None:
            self.current_operation = {
                'before_states': [],
                'affected_tiles': set()
            }
        
        # Add tile to affected set if in an operation
        if self.current_operation is not None:
            if (grid_x, grid_y) not in self.current_operation['affected_tiles']:
                # Save state before first change to this tile
                self.current_operation['before_states'].append(self.save_tile_state(grid_x, grid_y))
                self.current_operation['affected_tiles'].add((grid_x, grid_y))
        
        # Create parts from palette character
        parts = self.palette.create_parts_from_char(self.current_palette_char, grid_x, grid_y)
        for part in parts:
            self.vehicle.add_part(part)
        
        # Create items from palette character
        items = self.palette.create_items_from_char(self.current_palette_char, grid_x, grid_y)
        for item in items:
            self.vehicle.add_item(item)
        
        # Force redraw of this specific cell to update colors
        self.draw_cell(grid_x, grid_y)
        
        # Update tooltip if hovering over this tile
        if self.current_hover_tile == (grid_x, grid_y):
            self.show_tooltip(grid_x, grid_y, 0, 0)  # Position will be updated on next motion
            self.update_idletasks()
    
    def erase_cell(self, grid_x, grid_y, save_state=True):
        """Erase all parts and items at the given grid coordinates.
        
        Args:
            grid_x, grid_y: Grid coordinates
            save_state: If True and this is the start of an operation, save state before
        """
        # Start a new operation if not already in one
        if save_state and self.current_operation is None:
            self.current_operation = {
                'before_states': [],
                'affected_tiles': set()
            }
        
        # Add tile to affected set if in an operation
        if self.current_operation is not None:
            if (grid_x, grid_y) not in self.current_operation['affected_tiles']:
                # Save state before first change to this tile
                self.current_operation['before_states'].append(self.save_tile_state(grid_x, grid_y))
                self.current_operation['affected_tiles'].add((grid_x, grid_y))
        
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
        
        # Force redraw of this specific cell to update colors
        self.draw_cell(grid_x, grid_y)
        
        # Update tooltip if hovering over this tile
        if self.current_hover_tile == (grid_x, grid_y):
            self.show_tooltip(grid_x, grid_y, 0, 0)  # Position will be updated on next motion
            self.update_idletasks()
    
    def fill_rectangle(self, x1, y1, x2, y2):
        """Fill a rectangle area with the current palette entry."""
        # Normalize coordinates (x1,y1 is top-left, x2,y2 is bottom-right)
        min_x = min(x1, x2)
        max_x = max(x1, x2)
        min_y = min(y1, y2)
        max_y = max(y1, y2)
        
        # Save state before operation
        tile_coords = [(x, y) for x in range(min_x, max_x + 1) for y in range(min_y, max_y + 1)]
        before_states = self.save_tiles_state(tile_coords)
        
        # Fill all cells in the rectangle (don't save state individually, we're handling it here)
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                self.paint_cell(x, y, save_state=False)
        
        # Save state after operation
        after_states = self.save_tiles_state(tile_coords)
        
        # Push to undo stack
        self.push_operation(before_states, after_states)
    
    def erase_rectangle(self, x1, y1, x2, y2):
        """Erase all parts and items in a rectangle area."""
        # Normalize coordinates (x1,y1 is top-left, x2,y2 is bottom-right)
        min_x = min(x1, x2)
        max_x = max(x1, x2)
        min_y = min(y1, y2)
        max_y = max(y1, y2)
        
        # Save state before operation
        tile_coords = [(x, y) for x in range(min_x, max_x + 1) for y in range(min_y, max_y + 1)]
        before_states = self.save_tiles_state(tile_coords)
        
        # Erase all cells in the rectangle (don't save state individually, we're handling it here)
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                self.erase_cell(x, y, save_state=False)
        
        # Save state after operation
        after_states = self.save_tiles_state(tile_coords)
        
        # Push to undo stack
        self.push_operation(before_states, after_states)
        
        # Redraw grid to ensure axis lines remain visible
        self.draw_grid()
        # Ensure axis lines stay on top after redraw
        self.tag_raise("axis")
    
    def open_tile_editor(self, grid_x, grid_y):
        """Open the tile editor for the given coordinates."""
        def update_canvas():
            self.redraw()
            if self.tile_editor_callback:
                self.tile_editor_callback()
        
        TileEditorDialog(self.winfo_toplevel(), self.vehicle, grid_x, grid_y, update_canvas, self.palette)
    
    def get_part_color(self, part_name):
        """Get a consistent color for a part type."""
        if part_name not in self.part_colors:
            # Generate consistent color based on part name hash
            hash_obj = hashlib.md5(part_name.encode())
            hash_int = int(hash_obj.hexdigest(), 16)
            color_idx = hash_int % len(self.color_palette)
            self.part_colors[part_name] = self.color_palette[color_idx]
        return self.part_colors[part_name]
    
    def get_primary_part_name(self, part):
        """Get the primary part name from a part definition."""
        if 'part' in part:
            return part['part']
        elif 'parts' in part:
            # For multiple parts, use the first one
            parts_list = part['parts']
            if parts_list:
                if isinstance(parts_list[0], str):
                    return parts_list[0]
                elif isinstance(parts_list[0], dict) and 'part' in parts_list[0]:
                    return parts_list[0]['part']
        return None
    
    def _draw_checkered_fallback(self, x, y, cell_id):
        """Draw a purple/magenta and black checkered pattern as fallback."""
        checker_size = 4  # Size of each checker square
        magenta = "#FF00FF"  # Magenta/purple
        black = "#000000"
        
        # Convert grid_size to integer for range()
        grid_size_int = int(self.grid_size)
        
        # Draw checkered pattern
        for i in range(0, grid_size_int, checker_size):
            for j in range(0, grid_size_int, checker_size):
                # Alternate colors
                color = magenta if ((i // checker_size + j // checker_size) % 2 == 0) else black
                self.create_rectangle(
                    x + i, y + j,
                    x + i + checker_size, y + j + checker_size,
                    fill=color,
                    outline="",
                    tags=(cell_id, "cell")
                )
        
        # Add outline
        self.create_rectangle(
            x, y,
            x + grid_size_int, y + grid_size_int,
            outline="lightgray",
            width=1,
            tags=(cell_id, "cell")
        )
    
    def draw_cell(self, grid_x, grid_y):
        """Draw a single cell based on vehicle parts."""
        # Get screen coordinates for this grid cell
        x, y = self.grid_to_screen(grid_x, grid_y)
        
        # Remove existing cell drawing (delete all items with this cell_id tag)
        cell_id = f"cell_{grid_x}_{grid_y}"
        self.delete(cell_id)
        
        # Determine what to draw based on parts
        parts = self.vehicle.get_parts_at(grid_x, grid_y)
        items = self.vehicle.get_items_at(grid_x, grid_y)
        
        if parts or items:
            # Tileset drawing disabled for now - use checkered pattern
            # if parts and self.tileset_loader:
            #     primary_part = parts[0]
            #     primary_name = self.get_primary_part_name(primary_part)
            #     
            #     if primary_name:
            #         # Get tile image resized to grid size (convert to int for PIL)
            #         grid_size_int = int(self.grid_size)
            #         tile_image = self.tileset_loader.get_tile_image(
            #             primary_name,
            #             target_size=(grid_size_int, grid_size_int)
            #         )
            #         if tile_image:
            #             # Draw the tile image (fill the entire cell)
            #             # x, y are already screen coordinates from grid_to_screen()
            #             # Position at top-left corner of cell, not centered
            #             img_x = x
            #             img_y = y
            #             
            #             img_id = self.create_image(
            #                 img_x,
            #                 img_y,
            #                 image=tile_image,
            #                 anchor=tk.NW,  # Anchor to northwest (top-left) corner
            #                 tags=(cell_id, "cell")
            #             )
            #             # Keep reference to prevent garbage collection
            #             # Store image reference in a way that persists
            #             if not hasattr(self, '_image_refs_dict'):
            #                 self._image_refs_dict = {}
            #             self._image_refs_dict[img_id] = tile_image
            #         else:
            #             # Fallback to checkered pattern if tile not found
            #             self._draw_checkered_fallback(x, y, cell_id)
            #     else:
            #         # Fallback to checkered pattern
            #         self._draw_checkered_fallback(x, y, cell_id)
            # else:
            #     # No tileset or items only - use checkered pattern
            self._draw_checkered_fallback(x, y, cell_id)
        else:
            # Empty cell
            self.create_rectangle(
                x, y,
                x + self.grid_size, y + self.grid_size,
                fill="white",
                outline="lightgray",
                width=1,
                tags=(cell_id, "cell")
            )
        
        # Draw indicators: green plus for items (top-right), orange plus for multiple parts (bottom-right)
        if items:
            # Green plus in top-right corner for items
            plus_x = x + self.grid_size - 6
            plus_y = y + 6
            # Draw outline first (slightly offset in all directions)
            for offset_x, offset_y in [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]:
                self.create_text(
                    plus_x + offset_x, plus_y + offset_y,
                    text="+",
                    fill="#000000",  # Black outline
                    font=("Arial", 10, "bold"),
                    anchor=tk.CENTER,
                    tags=(cell_id, "cell")
                )
            # Draw the green plus on top
            self.create_text(
                plus_x, plus_y,
                text="+",
                fill="#00FF00",  # Green
                font=("Arial", 10, "bold"),
                anchor=tk.CENTER,
                tags=(cell_id, "cell")
            )
        
        # Count total number of individual parts (including parts in "parts" lists)
        total_part_count = 0
        for part in parts:
            if 'parts' in part:
                # Count parts in the list
                parts_list = part['parts']
                for p in parts_list:
                    if isinstance(p, str):
                        total_part_count += 1
                    elif isinstance(p, dict):
                        if 'part' in p:
                            total_part_count += 1
                        elif 'parts' in p:
                            # Nested parts - count them too
                            total_part_count += len([n for n in p['parts'] if isinstance(n, str) or (isinstance(n, dict) and 'part' in n)])
            elif 'part' in part:
                total_part_count += 1
        
        if total_part_count > 1:
            # Orange plus in bottom-right corner for multiple parts
            plus_x = x + self.grid_size - 6
            plus_y = y + self.grid_size - 6
            # Draw outline first (slightly offset in all directions)
            for offset_x, offset_y in [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]:
                self.create_text(
                    plus_x + offset_x, plus_y + offset_y,
                    text="+",
                    fill="#FFFFFF",  # White outline
                    font=("Arial", 10, "bold"),
                    anchor=tk.CENTER,
                    tags=(cell_id, "cell")
                )
            # Draw the orange plus on top
            self.create_text(
                plus_x, plus_y,
                text="+",
                fill="#FFA500",  # Orange
                font=("Arial", 10, "bold"),
                anchor=tk.CENTER,
                tags=(cell_id, "cell")
            )
    
    def draw_grid(self):
        """Draw the grid lines with infinite scrolling and origin markers.
        
        The grid is drawn using the logical grid_size (which scales with zoom)
        so that grid lines always align with tile positions.
        """
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
        
        # Calculate grid bounds using the scaled grid_size (for logical alignment)
        # This ensures grid lines align with tiles at any zoom level
        # These are screen grid coordinates (already rotated)
        screen_grid_x1 = int(view_x1 / self.grid_size) - 1
        screen_grid_y1 = int(view_y1 / self.grid_size) - 1
        screen_grid_x2 = int(view_x2 / self.grid_size) + 1
        screen_grid_y2 = int(view_y2 / self.grid_size) + 1
        
        # Find where logical origin (0, 0) appears in screen coordinates
        origin_screen_x, origin_screen_y = self.grid_to_screen(0, 0)
        
        # Draw vertical grid lines
        for screen_grid_x in range(screen_grid_x1, screen_grid_x2 + 1):
            x = screen_grid_x * self.grid_size
            
            # Check if this is the axis line for logical x=0 or y=0
            # At 0°/180°: logical x=0 appears as vertical line at screen x=0
            # At 90°/270°: logical y=0 appears as vertical line at screen x=0
            is_axis = False
            if screen_grid_x == 0:
                if self.rotation == 0 or self.rotation == 180:
                    # Vertical axis for logical x=0 (vertical line)
                    is_axis = True
                elif self.rotation == 90 or self.rotation == 270:
                    # Logical y=0 appears as vertical line at screen x=0
                    is_axis = True
            
            if is_axis:
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
        for screen_grid_y in range(screen_grid_y1, screen_grid_y2 + 1):
            y = screen_grid_y * self.grid_size
            
            # Check if this is the axis line for logical x=0 or y=0
            # At 0°/180°: logical y=0 appears as horizontal line at screen y=0
            # At 90°/270°: logical x=0 appears as horizontal line at screen y=0
            is_axis = False
            if screen_grid_y == 0:
                if self.rotation == 0 or self.rotation == 180:
                    # Horizontal axis for logical y=0
                    is_axis = True
                elif self.rotation == 90 or self.rotation == 270:
                    # Logical x=0 appears as horizontal line at screen y=0
                    is_axis = True
            
            if is_axis:
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
        
        # Draw origin marker (0,0 intersection) at its rotated position
        origin_x = origin_screen_x
        origin_y = origin_screen_y
        marker_size = 8
        self.create_oval(
            origin_x - marker_size, origin_y - marker_size,
            origin_x + marker_size, origin_y + marker_size,
            fill="#FF6B6B",
            outline="#CC0000",
            width=2,
            tags="axis"
        )
        
        # Ensure axis lines and markers are always on top (above cells)
        self.tag_raise("axis")
    
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
        # Scale scroll region size with zoom level to maintain same logical tile coverage
        # At higher zoom, we need a larger scroll region to see the same number of tiles
        scroll_region_size = self.base_scroll_region_size * self.zoom_level
        
        # Set a large scroll region centered around current view
        # This allows scrolling in all directions
        center = scroll_region_size // 2
        scroll_region = (
            -center, -center,
            center, center
        )
        self.config(scrollregion=scroll_region)
        
        # Store current scroll region size for grid drawing
        self.scroll_region_size = scroll_region_size
        
        # Redraw grid after scroll region changes
        self.after_idle(self.draw_grid)
    
    def on_zoom_wheel(self, event):
        """Handle mouse wheel for zooming."""
        # Zoom in or out based on scroll direction
        # On Linux, button events use num (4 = scroll up, 5 = scroll down)
        # On Windows/Mac, MouseWheel events use delta (positive = scroll up)
        if hasattr(event, 'num') and event.num in [4, 5]:  # Linux button events
            # Linux: 4 = scroll up (zoom in), 5 = scroll down (zoom out)
            if event.num == 4:
                self.zoom_in()
            else:
                self.zoom_out()
        elif hasattr(event, 'delta'):  # Windows/Mac MouseWheel events
            # Windows/Mac: delta > 0 = scroll up = zoom in
            delta = event.delta
            if delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
    
    def zoom_in(self, factor=1.2):
        """Zoom in on the canvas."""
        new_zoom = self.zoom_level * factor
        if new_zoom <= self.max_zoom:
            self.set_zoom(new_zoom)
    
    def zoom_out(self, factor=1.2):
        """Zoom out on the canvas."""
        new_zoom = self.zoom_level / factor
        if new_zoom >= self.min_zoom:
            self.set_zoom(new_zoom)
    
    def reset_zoom(self):
        """Reset zoom to 100%."""
        self.set_zoom(1.0)
    
    def set_zoom(self, zoom_level):
        """Set the zoom level and update the canvas, maintaining view center."""
        # Clamp zoom level
        zoom_level = max(self.min_zoom, min(self.max_zoom, zoom_level))
        
        # Get current view center before zoom (in grid coordinates)
        old_zoom = self.zoom_level
        
        # Get current scroll position and convert to grid coordinates
        scroll_region = self.cget("scrollregion")
        if not scroll_region:
            # No scroll region yet, just update zoom
            self.zoom_level = zoom_level
            self.grid_size = self.base_grid_size * self.zoom_level
            if self.zoom_callback:
                self.zoom_callback()
            self.redraw()
            return
        
        region = scroll_region.split()
        region_min_x = float(region[0])
        region_min_y = float(region[1])
        region_max_x = float(region[2])
        region_max_y = float(region[3])
        region_width = region_max_x - region_min_x
        region_height = region_max_y - region_min_y
        
        # Get current scroll position
        scroll_x = self.xview()[0]
        scroll_y = self.yview()[0]
        
        # Get viewport dimensions
        canvas_width = self.winfo_width()
        canvas_height = self.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            # Canvas not ready yet
            self.zoom_level = zoom_level
            self.grid_size = self.base_grid_size * self.zoom_level
            if self.zoom_callback:
                self.zoom_callback()
            self.redraw()
            return
        
        # Calculate the current view center in canvas coordinates
        # The left edge of viewport is at: region_min_x + scroll_x * region_width
        # The center is at: left_edge + canvas_width / 2
        view_center_x = region_min_x + scroll_x * region_width + canvas_width / 2
        view_center_y = region_min_y + scroll_y * region_height + canvas_height / 2
        
        # Convert view center to grid coordinates using old zoom
        if old_zoom > 0:
            old_grid_size = self.base_grid_size * old_zoom
            grid_x = view_center_x / old_grid_size
            grid_y = view_center_y / old_grid_size
        else:
            grid_x = view_center_x / self.base_grid_size
            grid_y = view_center_y / self.base_grid_size
        
        # Update zoom level
        self.zoom_level = zoom_level
        self.grid_size = self.base_grid_size * self.zoom_level
        
        # Update scroll region FIRST (so it's scaled to new zoom)
        self.update_scroll_region()
        
        # Get the new scroll region
        scroll_region = self.cget("scrollregion")
        if scroll_region:
            region = scroll_region.split()
            region_min_x = float(region[0])
            region_min_y = float(region[1])
            region_max_x = float(region[2])
            region_max_y = float(region[3])
            region_width = region_max_x - region_min_x
            region_height = region_max_y - region_min_y
            
            # Calculate new canvas coordinates for the same grid position
            new_canvas_x = grid_x * self.grid_size
            new_canvas_y = grid_y * self.grid_size
            
            # Calculate new scroll position to keep the same point centered
            # We want: new_canvas_x = region_min_x + new_scroll_x * region_width + canvas_width / 2
            # So: new_scroll_x = (new_canvas_x - region_min_x - canvas_width / 2) / region_width
            new_scroll_x = (new_canvas_x - region_min_x - canvas_width / 2) / region_width
            new_scroll_y = (new_canvas_y - region_min_y - canvas_height / 2) / region_height
            
            # Clamp scroll values
            new_scroll_x = max(0.0, min(1.0, new_scroll_x))
            new_scroll_y = max(0.0, min(1.0, new_scroll_y))
            
            self.xview_moveto(new_scroll_x)
            self.yview_moveto(new_scroll_y)
        
        # Notify callback if set
        if self.zoom_callback:
            self.zoom_callback()
        
        # Redraw everything (skip scroll region update since we already did it)
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
        
        # Don't call update_scroll_region again - we already did it

