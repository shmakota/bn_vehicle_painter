#!/usr/bin/env python3
"""
Vehicle Painter for Cataclysm: Bright Nights
A tkinter-based tool for painting and customizing vehicles.
"""

import tkinter as tk
from tkinter import ttk, colorchooser, filedialog, messagebox
from canvas import VehicleCanvas
from vehicle import Vehicle
from palette import Palette


class VehiclePainterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Cataclysm: Bright Nights - Vehicle Painter")
        self.root.geometry("1200x900")
        
        self.vehicle = Vehicle()
        self.palette = None
        self.current_palette_char = None
        
        self.setup_ui()
        
        # Recenter view after UI is set up
        self.root.update_idletasks()
        if hasattr(self, 'canvas'):
            self.recenter_view()
        
    def setup_ui(self):
        """Set up the user interface."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=0)  # Left panel doesn't expand
        main_frame.columnconfigure(2, weight=1)   # Canvas expands
        
        # Left panel - Tools and Controls (resizable)
        self.left_panel = ttk.Frame(main_frame, width=250)
        self.left_panel.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.left_panel.grid_propagate(False)  # Prevent widgets from changing panel size
        self.left_panel.columnconfigure(0, weight=1)
        
        # Draggable separator with visible handle
        separator_frame = tk.Frame(main_frame, width=8, bg="lightgray", cursor="sb_h_double_arrow")
        separator_frame.grid(row=0, column=1, sticky=(tk.N, tk.S))
        separator_frame.grid_propagate(False)
        
        # Make separator frame draggable
        separator_frame.bind("<Button-1>", self.on_separator_press)
        separator_frame.bind("<B1-Motion>", self.on_separator_drag)
        separator_frame.bind("<ButtonRelease-1>", self.on_separator_release)
        separator_frame.bind("<Enter>", lambda e: separator_frame.config(bg="#888888"))
        separator_frame.bind("<Leave>", lambda e: separator_frame.config(bg="lightgray"))
        
        self.separator_frame = separator_frame
        self.separator_dragging = False
        self.left_panel_width = 250  # Initial width
        self.separator_start_x = 0
        self.left_panel_min_width = 200
        self.left_panel_max_width = 600
        
        # Palette selector
        palette_frame = ttk.LabelFrame(self.left_panel, text="Palette", padding="10")
        palette_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        palette_frame.columnconfigure(0, weight=1)
        
        # Palette buttons
        palette_btn_frame = ttk.Frame(palette_frame)
        palette_btn_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        palette_btn_frame.columnconfigure(0, weight=1)
        palette_btn_frame.columnconfigure(1, weight=1)
        
        ttk.Button(
            palette_btn_frame,
            text="Load",
            command=self.load_palette
        ).grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(
            palette_btn_frame,
            text="Save",
            command=self.save_palette
        ).grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        self.palette_label = ttk.Label(palette_frame, text="No palette loaded")
        self.palette_label.grid(row=1, column=0, sticky=tk.W)
        
        # Current palette character
        char_frame = ttk.Frame(palette_frame)
        char_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        ttk.Label(char_frame, text="Char:").pack(side=tk.LEFT, padx=(0, 5))
        self.char_var = tk.StringVar()
        self.char_entry = ttk.Entry(char_frame, textvariable=self.char_var, width=5)
        self.char_entry.pack(side=tk.LEFT)
        self.char_var.trace('w', self.on_char_change)
        
        self.char_preview = tk.Label(
            char_frame,
            text="",
            width=3,
            height=1,
            relief=tk.RAISED,
            borderwidth=1,
            font=("Courier", 12, "bold")
        )
        self.char_preview.pack(side=tk.LEFT, padx=(5, 0))
        
        # Search frame
        search_frame = ttk.Frame(palette_frame)
        search_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(10, 5))
        search_frame.columnconfigure(1, weight=1)
        
        ttk.Label(search_frame, text="Search:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.palette_search_var = tk.StringVar()
        self.palette_search_entry = ttk.Entry(search_frame, textvariable=self.palette_search_var, width=15)
        self.palette_search_entry.grid(row=0, column=1, sticky=(tk.W, tk.E))
        self.palette_search_var.trace('w', self.on_palette_search)
        
        # Palette characters list
        ttk.Label(palette_frame, text="Available:").grid(row=4, column=0, sticky=tk.W, pady=(5, 0))
        
        # Listbox with scrollbar for palette entries
        listbox_frame = ttk.Frame(palette_frame)
        listbox_frame.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(5, 5))
        listbox_frame.columnconfigure(0, weight=1)
        
        scrollbar = ttk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.chars_listbox = tk.Listbox(listbox_frame, height=6, yscrollcommand=scrollbar.set)
        self.chars_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.chars_listbox.yview)
        self.chars_listbox.bind('<<ListboxSelect>>', self.on_char_select)
        self.chars_listbox.bind('<Double-Button-1>', self.on_char_double_click)
        
        # Store all palette entries for filtering
        self.all_palette_entries = []
        
        # Edit, Add, Clear buttons frame
        palette_action_frame = ttk.Frame(palette_frame)
        palette_action_frame.grid(row=6, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        palette_action_frame.columnconfigure(0, weight=1)
        palette_action_frame.columnconfigure(1, weight=1)
        palette_action_frame.columnconfigure(2, weight=1)
        
        ttk.Button(
            palette_action_frame,
            text="Edit Selected",
            command=self.edit_palette_entry
        ).grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(
            palette_action_frame,
            text="Add",
            command=self.add_palette_entry
        ).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(
            palette_action_frame,
            text="Clear",
            command=self.clear_palette
        ).grid(row=0, column=2, sticky=(tk.W, tk.E))
        
        # Tools frame
        tools_frame = ttk.LabelFrame(self.left_panel, text="Tools", padding="10")
        tools_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        tools_frame.columnconfigure(0, weight=1)
        
        self.tool_var = tk.StringVar(value="paint")
        ttk.Radiobutton(
            tools_frame,
            text="Paint",
            variable=self.tool_var,
            value="paint"
        ).grid(row=0, column=0, sticky=tk.W)
        
        ttk.Radiobutton(
            tools_frame,
            text="Erase",
            variable=self.tool_var,
            value="erase"
        ).grid(row=1, column=0, sticky=tk.W)
        
        ttk.Radiobutton(
            tools_frame,
            text="Edit Tile",
            variable=self.tool_var,
            value="select"
        ).grid(row=2, column=0, sticky=tk.W)
        
        ttk.Label(
            tools_frame,
            text="Right-click: Edit Tile",
            font=("TkDefaultFont", 7),
            foreground="gray"
        ).grid(row=3, column=0, sticky=tk.W, pady=(5, 0))
        
        # Vehicle info frame
        info_frame = ttk.LabelFrame(self.left_panel, text="Vehicle Info", padding="10")
        info_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        info_frame.columnconfigure(1, weight=1)
        
        ttk.Label(info_frame, text="Name:").grid(row=0, column=0, sticky=tk.W)
        self.vehicle_name_entry = ttk.Entry(info_frame, width=20)
        self.vehicle_name_entry.grid(row=0, column=1, sticky=(tk.W, tk.E))
        self.vehicle_name_entry.insert(0, "Custom Vehicle")
        self.vehicle_name_entry.bind('<KeyRelease>', self.on_vehicle_name_change)
        
        ttk.Label(info_frame, text="ID:").grid(row=1, column=0, sticky=tk.W)
        self.vehicle_id_entry = ttk.Entry(info_frame, width=20)
        self.vehicle_id_entry.grid(row=1, column=1, sticky=(tk.W, tk.E))
        self.vehicle_id_entry.insert(0, "custom_vehicle")
        self.vehicle_id_entry.bind('<KeyRelease>', self.on_vehicle_id_change)
        
        ttk.Label(info_frame, text="Parts:").grid(row=2, column=0, sticky=tk.W)
        self.parts_label = ttk.Label(info_frame, text="0")
        self.parts_label.grid(row=2, column=1, sticky=tk.W)
        
        ttk.Label(info_frame, text="Items:").grid(row=3, column=0, sticky=tk.W)
        self.items_label = ttk.Label(info_frame, text="0")
        self.items_label.grid(row=3, column=1, sticky=tk.W)
        
        # File operations frame
        file_frame = ttk.LabelFrame(self.left_panel, text="File", padding="10")
        file_frame.grid(row=3, column=0, sticky=(tk.W, tk.E))
        file_frame.columnconfigure(0, weight=1)
        
        ttk.Button(
            file_frame,
            text="New Vehicle",
            command=self.new_vehicle
        ).grid(row=0, column=0, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Button(
            file_frame,
            text="Load Vehicle",
            command=self.load_vehicle
        ).grid(row=1, column=0, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Button(
            file_frame,
            text="Save Vehicle",
            command=self.save_vehicle
        ).grid(row=2, column=0, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Button(
            file_frame,
            text="Information Atlas",
            command=self.show_information_atlas
        ).grid(row=3, column=0, sticky=(tk.W, tk.E), pady=2)
        
        # Canvas area - Right side
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.grid(row=0, column=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(2, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # Canvas with scrollbars
        self.canvas = VehicleCanvas(
            canvas_frame,
            vehicle=self.vehicle,
            tool_var=self.tool_var,
            current_palette_char=self.current_palette_char,
            palette=self.palette,
            char_var=self.char_var,  # Pass char_var for keyboard hotkey updates
            width=800,
            height=600,
            bg="white"
        )
        self.canvas.tile_editor_callback = self.update_parts_count
        
        # Add recenter button on canvas frame (bottom right)
        self.recenter_button = ttk.Button(
            canvas_frame,
            text="Recenter",
            command=self.recenter_view
        )
        self.recenter_canvas_frame = canvas_frame
        # Position will be set after canvas is configured
        
        scrollbar_v = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas_scroll_vertical)
        scrollbar_h = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas_scroll_horizontal)
        self.canvas.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)
        
        self.canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar_v.grid(row=0, column=1, sticky=(tk.N, tk.S))
        scrollbar_h.grid(row=1, column=0, sticky=(tk.W, tk.E))
        canvas_frame.columnconfigure(0, weight=1)
        canvas_frame.rowconfigure(0, weight=1)
        
        # Position recenter button in bottom right corner
        self.position_recenter_button()
        
        # Status bar
        self.status_bar = ttk.Label(
            main_frame,
            text="Ready",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_bar.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
    
    def canvas_scroll_vertical(self, *args):
        """Handle vertical scrolling - update scrollbar and redraw grid."""
        self.canvas.yview(*args)
        self.canvas.after_idle(self.canvas.draw_grid)
    
    def canvas_scroll_horizontal(self, *args):
        """Handle horizontal scrolling - update scrollbar and redraw grid."""
        self.canvas.xview(*args)
        self.canvas.after_idle(self.canvas.draw_grid)
    
    def on_separator_press(self, event):
        """Handle separator mouse press."""
        self.separator_dragging = True
        self.separator_start_x = event.x_root
    
    def on_separator_drag(self, event):
        """Handle separator drag."""
        if not self.separator_dragging:
            return
        
        # Calculate new width
        delta_x = event.x_root - self.separator_start_x
        new_width = self.left_panel_width + delta_x
        
        # Limit width using min/max
        new_width = max(self.left_panel_min_width, min(self.left_panel_max_width, new_width))
        
        # Update panel width
        self.left_panel.config(width=int(new_width))
        self.left_panel.grid_propagate(False)  # Ensure width is respected
        self.left_panel_width = new_width
        self.separator_start_x = event.x_root
    
    def on_separator_release(self, event):
        """Handle separator mouse release."""
        self.separator_dragging = False
        
    def position_recenter_button(self):
        """Position the recenter button in the bottom right corner of the canvas."""
        def update_position():
            # Get canvas frame dimensions (not canvas widget, but the frame containing it)
            frame_width = self.recenter_canvas_frame.winfo_width()
            frame_height = self.recenter_canvas_frame.winfo_height()
            if frame_width > 1 and frame_height > 1:
                # Get button dimensions
                self.recenter_button.update_idletasks()
                btn_width = self.recenter_button.winfo_width() or 80
                btn_height = self.recenter_button.winfo_height() or 25
                
                # Position in bottom right with some padding (account for scrollbar)
                # Scrollbar is 17px wide, so subtract that from available width
                x = frame_width - btn_width - 25  # Extra padding for scrollbar area
                y = frame_height - btn_height - 25  # Padding from bottom
                
                self.recenter_button.place(x=x, y=y)
        
        # Update position after canvas is configured
        self.root.after_idle(update_position)
        # Also update when canvas frame resizes
        self.recenter_canvas_frame.bind("<Configure>", lambda e: update_position())
    
    def recenter_view(self):
        """Recenter the canvas view on the vehicle or origin, properly centered in viewport."""
        self.canvas.update_idletasks()
        
        # Get visible canvas dimensions
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            return
        
        if self.vehicle.parts or self.vehicle.items:
            # Center on vehicle
            bounds = self.vehicle.get_bounds()
            if bounds and len(bounds) == 4:
                min_x, min_y, max_x, max_y = bounds
                center_x = (min_x + max_x) / 2.0
                center_y = (min_y + max_y) / 2.0
                
                # Convert grid coordinates to canvas coordinates
                target_canvas_x = center_x * self.canvas.grid_size
                target_canvas_y = center_y * self.canvas.grid_size
                
                # We want this point to be in the center of the viewport
                # The viewport center should show target_canvas_x, target_canvas_y
                # Current viewport shows from (view_x1, view_y1) to (view_x2, view_y2)
                # We want: (view_x1 + view_x2)/2 = target_canvas_x
                # And: (view_y1 + view_y2)/2 = target_canvas_y
                
                # Get scroll region
                scroll_region = self.canvas.cget("scrollregion")
                if scroll_region:
                    region = scroll_region.split()
                    region_min_x = float(region[0])
                    region_min_y = float(region[1])
                    region_max_x = float(region[2])
                    region_max_y = float(region[3])
                    region_width = region_max_x - region_min_x
                    region_height = region_max_y - region_min_y
                    
                    # Calculate scroll position to center the target point
                    # Scroll position is a fraction (0.0 to 1.0) of the scrollable area
                    # We want: target_x - canvas_width/2 = region_min_x + scroll_x * region_width
                    scroll_x = (target_canvas_x - canvas_width / 2 - region_min_x) / region_width
                    scroll_y = (target_canvas_y - canvas_height / 2 - region_min_y) / region_height
                    
                    # Clamp to valid range
                    scroll_x = max(0.0, min(1.0, scroll_x))
                    scroll_y = max(0.0, min(1.0, scroll_y))
                    
                    self.canvas.xview_moveto(scroll_x)
                    self.canvas.yview_moveto(scroll_y)
                    self.update_status(f"Recentered on vehicle (center: {center_x:.1f}, {center_y:.1f})")
                else:
                    # Fallback: center at middle
                    self.canvas.xview_moveto(0.5)
                    self.canvas.yview_moveto(0.5)
                    self.update_status("Recentered on vehicle")
        else:
            # Center on origin (0, 0)
            # Origin is at (0, 0) in canvas coordinates
            scroll_region = self.canvas.cget("scrollregion")
            if scroll_region:
                region = scroll_region.split()
                region_min_x = float(region[0])
                region_min_y = float(region[1])
                region_max_x = float(region[2])
                region_max_y = float(region[3])
                region_width = region_max_x - region_min_x
                region_height = region_max_y - region_min_y
                
                # Center origin (0, 0) in viewport
                scroll_x = (0 - canvas_width / 2 - region_min_x) / region_width
                scroll_y = (0 - canvas_height / 2 - region_min_y) / region_height
                
                scroll_x = max(0.0, min(1.0, scroll_x))
                scroll_y = max(0.0, min(1.0, scroll_y))
                
                self.canvas.xview_moveto(scroll_x)
                self.canvas.yview_moveto(scroll_y)
            else:
                self.canvas.xview_moveto(0.5)
                self.canvas.yview_moveto(0.5)
            self.update_status("Recentered on origin (0, 0)")
        
        # Redraw grid after recentering
        self.canvas.update_idletasks()
        self.canvas.after_idle(self.canvas.draw_grid)
        # Reposition button after view changes
        self.canvas.after_idle(self.position_recenter_button)
        
    def format_palette_entry(self, char):
        """Format a palette character for display with its definition."""
        part_def = self.palette.get_part_definition(char) if self.palette else None
        item_def = self.palette.get_item_definition(char) if self.palette else None
        
        description = ""
        
        if part_def:
            if isinstance(part_def, str):
                description = f"Part: {part_def}"
            elif isinstance(part_def, dict):
                if 'part' in part_def:
                    desc = f"Part: {part_def['part']}"
                    if 'fuel' in part_def:
                        desc += f" (fuel: {part_def['fuel']})"
                    description = desc
                elif 'parts' in part_def:
                    parts_str = ", ".join(part_def['parts'])
                    desc = f"Parts: {parts_str}"
                    if 'fuel' in part_def:
                        desc += f" (fuel: {part_def['fuel']})"
                    description = desc
        
        if item_def:
            if description:
                description += " | "
            if isinstance(item_def, list) and item_def:
                item_desc = []
                for item in item_def:
                    if 'item' in item:
                        item_desc.append(f"Item: {item['item']}")
                    if 'item_groups' in item:
                        item_desc.append(f"Groups: {', '.join(item['item_groups'])}")
                description += " | ".join(item_desc)
            else:
                description += "Items"
        
        if not description:
            description = "(empty)"
        
        return f"{char} - {description}"
    
    def load_palette(self):
        """Load a palette from file."""
        filename = filedialog.askopenfilename(
            title="Load Palette",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir="palettes"
        )
        if filename:
            try:
                self.palette = Palette.load_from_file(filename)
                self.canvas.palette = self.palette
                
                # Update palette label
                palette_name = self.palette.palette_id or "Unknown"
                self.palette_label.config(text=f"Palette: {palette_name}")
                
                # Update characters list with formatted entries
                self.update_palette_display()
                
                self.update_status(f"Loaded palette: {palette_name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load palette:\n{e}")
    
    def save_palette(self):
        """Save the current palette to file."""
        if not self.palette:
            messagebox.showwarning("No Palette", "No palette loaded to save.")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Save Palette",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir="palettes"
        )
        if filename:
            try:
                self.palette.save_to_file(filename)
                self.update_status(f"Saved palette to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save palette:\n{e}")
    
    def clear_palette(self):
        """Clear the current palette."""
        if not self.palette:
            messagebox.showwarning("No Palette", "No palette loaded to clear.")
            return
        
        if messagebox.askyesno("Clear Palette", "Are you sure you want to clear the entire palette? This cannot be undone."):
            self.palette.vehicle_part = {}
            self.palette.items = {}
            self.canvas.palette = self.palette
            self.update_palette_display()
            self.char_var.set("")
            self.current_palette_char = None
            self.canvas.current_palette_char = None
            self.update_status("Palette cleared")
    
    def add_palette_entry(self):
        """Add a new palette entry."""
        # Create a new empty palette if none exists
        if not self.palette:
            self.palette = Palette()
            self.canvas.palette = self.palette
            self.palette_label.config(text="Palette: New")
        
        # Find an available character (skip ones already in use)
        available_chars = []
        # Start from 'A' for better readability, fall back to other chars if needed
        search_order = [chr(i) for i in range(ord('A'), ord('Z') + 1)] + \
                      [chr(i) for i in range(ord('a'), ord('z') + 1)] + \
                      [chr(i) for i in range(ord('0'), ord('9') + 1)] + \
                      [chr(i) for i in range(ord('!'), ord('~') + 1) if chr(i) not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789']
        
        for char in search_order:
            # Check if character is already used
            if char not in self.palette.vehicle_part and char not in self.palette.items:
                available_chars.append(char)
                if len(available_chars) >= 10:
                    break
        
        if not available_chars:
            messagebox.showerror("Error", "No available characters. Clear some palette entries first.")
            return
        
        new_char = available_chars[0]
        
        # Use the existing edit dialog but with no existing definitions
        self.edit_palette_entry_dialog(new_char, None, None)
    
    def update_palette_display(self):
        """Update the palette listbox display."""
        # Store all entries
        self.all_palette_entries = []
        if self.palette:
            for char in self.palette.get_available_characters():
                formatted = self.format_palette_entry(char)
                self.all_palette_entries.append((char, formatted))
        
        # Apply search filter
        self.filter_palette_display()
    
    def filter_palette_display(self):
        """Filter the palette display based on search text."""
        search_text = self.palette_search_var.get().lower() if hasattr(self, 'palette_search_var') else ""
        
        self.chars_listbox.delete(0, tk.END)
        for char, formatted in self.all_palette_entries:
            if not search_text or search_text in formatted.lower():
                self.chars_listbox.insert(tk.END, formatted)
    
    def on_palette_search(self, *args):
        """Handle palette search text change."""
        self.filter_palette_display()
    
    def on_char_double_click(self, event):
        """Handle double-click on palette character - edit it."""
        self.edit_palette_entry()
    
    def edit_palette_entry(self):
        """Edit the selected palette entry."""
        if not self.palette:
            messagebox.showwarning("No Palette", "No palette loaded to edit.")
            return
        
        selection = self.chars_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a palette entry to edit.")
            return
        
        # Extract character from formatted display
        formatted = self.chars_listbox.get(selection[0])
        char = formatted.split(' - ')[0] if ' - ' in formatted else formatted.strip()
        
        # Get current definitions
        part_def = self.palette.get_part_definition(char)
        item_def = self.palette.get_item_definition(char)
        
        # Show edit dialog
        self.edit_palette_entry_dialog(char, part_def, item_def)
    
    def edit_palette_entry_dialog(self, char, part_def, item_def):
        """Show dialog to edit or add a palette entry."""
        is_new = part_def is None and item_def is None
        # Create edit dialog
        edit_dialog = tk.Toplevel(self.root)
        edit_dialog.title(f"{'Add' if is_new else 'Edit'} Palette Entry" + (f": {char}" if not is_new else ""))
        edit_dialog.transient(self.root)
        edit_dialog.geometry("500x500")
        
        main_frame = ttk.Frame(edit_dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Character selection (can change character)
        char_frame = ttk.LabelFrame(main_frame, text="Character", padding="10")
        char_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(char_frame, text="Character:").pack(side=tk.LEFT, padx=(0, 5))
        new_char_var = tk.StringVar(value=char)
        char_entry = ttk.Entry(char_frame, textvariable=new_char_var, width=5)
        char_entry.pack(side=tk.LEFT)
        
        # Part definition
        part_frame = ttk.LabelFrame(main_frame, text="Vehicle Part", padding="10")
        part_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        part_type_var = tk.StringVar(value="single" if part_def else "none")
        ttk.Radiobutton(part_frame, text="None", variable=part_type_var, value="none").pack(anchor=tk.W)
        ttk.Radiobutton(part_frame, text="Single Part", variable=part_type_var, value="single").pack(anchor=tk.W)
        ttk.Radiobutton(part_frame, text="Multiple Parts", variable=part_type_var, value="multiple").pack(anchor=tk.W)
        
        part_entry_frame = ttk.Frame(part_frame)
        part_entry_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(part_entry_frame, text="Part(s) (comma-separated for multiple):").pack(anchor=tk.W)
        part_var = tk.StringVar()
        if part_def:
            if isinstance(part_def, str):
                part_var.set(part_def)
            elif isinstance(part_def, dict):
                if 'part' in part_def:
                    part_var.set(part_def['part'])
                elif 'parts' in part_def:
                    part_var.set(", ".join(part_def['parts']))
        
        part_entry = ttk.Entry(part_entry_frame, textvariable=part_var, width=40)
        part_entry.pack(fill=tk.X, pady=(5, 0))
        
        fuel_frame = ttk.Frame(part_frame)
        fuel_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(fuel_frame, text="Fuel (optional):").pack(side=tk.LEFT, padx=(0, 5))
        fuel_var = tk.StringVar()
        if part_def and isinstance(part_def, dict) and 'fuel' in part_def:
            fuel_var.set(part_def['fuel'])
        fuel_entry = ttk.Entry(fuel_frame, textvariable=fuel_var, width=20)
        fuel_entry.pack(side=tk.LEFT)
        
        # Item definition
        item_frame = ttk.LabelFrame(main_frame, text="Items / Item Groups", padding="10")
        item_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        item_type_var = tk.StringVar(value="none" if not item_def else "item")
        ttk.Radiobutton(item_frame, text="None", variable=item_type_var, value="none").pack(anchor=tk.W)
        ttk.Radiobutton(item_frame, text="Item", variable=item_type_var, value="item").pack(anchor=tk.W)
        ttk.Radiobutton(item_frame, text="Item Groups", variable=item_type_var, value="groups").pack(anchor=tk.W)
        
        item_entry_frame = ttk.Frame(item_frame)
        item_entry_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(item_entry_frame, text="Item / Groups:").pack(anchor=tk.W)
        item_var = tk.StringVar()
        if item_def and isinstance(item_def, list) and item_def:
            item_strs = []
            for item in item_def:
                if 'item' in item:
                    item_strs.append(f"item:{item['item']}")
                if 'item_groups' in item:
                    item_strs.append(f"groups:{','.join(item['item_groups'])}")
            item_var.set(" | ".join(item_strs))
        
        item_entry = ttk.Entry(item_entry_frame, textvariable=item_var, width=40)
        item_entry.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(item_entry_frame, text="(Format: item:name | groups:group1,group2)", 
                 font=("TkDefaultFont", 8), foreground="gray").pack(anchor=tk.W)
        
        def save_changes():
            new_char = new_char_var.get().strip()
            if not new_char or len(new_char) != 1:
                messagebox.showwarning("Invalid Input", "Character must be a single character.")
                return
            
            # Remove old character entry if changing character
            if not is_new and char != new_char:
                if char in self.palette.vehicle_part:
                    del self.palette.vehicle_part[char]
                if char in self.palette.items:
                    del self.palette.items[char]
            
            # Check if new character already exists
            if new_char in self.palette.vehicle_part or new_char in self.palette.items:
                if not messagebox.askyesno("Overwrite", f"Character '{new_char}' already exists. Overwrite?"):
                    return
                # Remove old entries
                if new_char in self.palette.vehicle_part:
                    del self.palette.vehicle_part[new_char]
                if new_char in self.palette.items:
                    del self.palette.items[new_char]
            
            # Validate that at least one definition is provided
            part_name = part_var.get().strip() if part_type_var.get() != "none" else ""
            parts_str = part_var.get().strip() if part_type_var.get() == "multiple" else ""
            item_str = item_var.get().strip() if item_type_var.get() != "none" else ""
            
            if part_type_var.get() == "none" and item_type_var.get() == "none":
                messagebox.showwarning("Empty Entry", "You must provide at least a part definition or item definition.")
                return
            
            # Update part definition
            if part_type_var.get() == "none":
                if new_char in self.palette.vehicle_part:
                    del self.palette.vehicle_part[new_char]
            elif part_type_var.get() == "single":
                if part_name:
                    fuel = fuel_var.get().strip()
                    if fuel:
                        self.palette.vehicle_part[new_char] = {'part': part_name, 'fuel': fuel}
                    else:
                        self.palette.vehicle_part[new_char] = part_name
                else:
                    messagebox.showwarning("Invalid Input", "Part name is required for single part.")
                    return
            elif part_type_var.get() == "multiple":
                if parts_str:
                    parts_list = [p.strip() for p in parts_str.split(',') if p.strip()]
                    if not parts_list:
                        messagebox.showwarning("Invalid Input", "At least one part name is required.")
                        return
                    fuel = fuel_var.get().strip()
                    if fuel:
                        self.palette.vehicle_part[new_char] = {'parts': parts_list, 'fuel': fuel}
                    else:
                        self.palette.vehicle_part[new_char] = {'parts': parts_list}
                else:
                    messagebox.showwarning("Invalid Input", "Part names are required for multiple parts.")
                    return
            
            # Update item definition
            if item_type_var.get() == "none":
                if new_char in self.palette.items:
                    del self.palette.items[new_char]
            else:
                if item_str:
                    items_list = []
                    for part in item_str.split('|'):
                        part = part.strip()
                        if not part:
                            continue
                        item_entry = {}
                        if part.startswith('item:'):
                            item_name = part[5:].strip()
                            if item_name:
                                item_entry['item'] = item_name
                        elif part.startswith('groups:'):
                            groups_str = part[7:].strip()
                            if groups_str:
                                groups = [g.strip() for g in groups_str.split(',') if g.strip()]
                                if groups:
                                    item_entry['item_groups'] = groups
                        if item_entry:
                            items_list.append(item_entry)
                    if items_list:
                        self.palette.items[new_char] = items_list
                    else:
                        messagebox.showwarning("Invalid Input", "Valid item or item group definitions are required.")
                        return
                else:
                    messagebox.showwarning("Invalid Input", "Item definition is required when item type is selected.")
                    return
            
            # Update canvas palette
            self.canvas.palette = self.palette
            
            # Refresh display
            self.update_palette_display()
            self.char_var.set(new_char)
            self.current_palette_char = new_char
            self.canvas.current_palette_char = new_char
            
            edit_dialog.destroy()
            self.update_status(f"{'Added' if is_new else 'Updated'} palette entry: {new_char}")
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=(10, 0))
        ttk.Button(button_frame, text="Save", command=save_changes).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Cancel", command=edit_dialog.destroy).pack(side=tk.LEFT)
        
        # Grab focus
        edit_dialog.update_idletasks()
        try:
            edit_dialog.grab_set()
        except tk.TclError:
            pass
    
    def on_char_change(self, *args):
        """Handle palette character change."""
        char = self.char_var.get().strip()
        if len(char) == 1:
            self.current_palette_char = char
            self.canvas.current_palette_char = char
            self.char_preview.config(text=char)
        elif len(char) == 0:
            self.current_palette_char = None
            self.canvas.current_palette_char = None
            self.char_preview.config(text="")
        else:
            # Take first character
            self.char_var.set(char[0])
    
    def on_char_select(self, event):
        """Handle character selection from listbox."""
        selection = self.chars_listbox.curselection()
        if selection:
            # Extract character from formatted display (format is "char - description")
            formatted = self.chars_listbox.get(selection[0])
            char = formatted.split(' - ')[0] if ' - ' in formatted else formatted.strip()
            self.char_var.set(char)
    
    def on_vehicle_name_change(self, event):
        """Update vehicle name."""
        self.vehicle.name = self.vehicle_name_entry.get()
    
    def on_vehicle_id_change(self, event):
        """Update vehicle ID."""
        self.vehicle.id = self.vehicle_id_entry.get()
    
    def new_vehicle(self):
        """Create a new vehicle."""
        if messagebox.askyesno("New Vehicle", "Create a new vehicle? Unsaved changes will be lost."):
            self.vehicle = Vehicle()
            self.canvas.vehicle = self.vehicle
            self.canvas.redraw()
            self.canvas.update_idletasks()
            self.recenter_view()
            self.vehicle_name_entry.delete(0, tk.END)
            self.vehicle_name_entry.insert(0, "Custom Vehicle")
            self.vehicle_id_entry.delete(0, tk.END)
            self.vehicle_id_entry.insert(0, "custom_vehicle")
            self.update_parts_count()
            self.update_status("New vehicle created")
    
    def load_vehicle(self):
        """Load a vehicle from file."""
        filename = filedialog.askopenfilename(
            title="Load Vehicle",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir="vehicles"
        )
        if filename:
            try:
                # Try to load and check if there are multiple vehicles
                vehicles = self._load_vehicles_from_file(filename)
                
                if len(vehicles) == 0:
                    messagebox.showerror("Error", "No valid vehicles found in file.")
                    return
                elif len(vehicles) == 1:
                    # Single vehicle - load directly
                    selected_vehicle = vehicles[0]
                else:
                    # Multiple vehicles - show selection dialog
                    selected_vehicle = self._select_vehicle(vehicles, filename)
                    if not selected_vehicle:
                        return  # User cancelled
                
                self.vehicle = selected_vehicle
                # Vehicle coordinates are normalized automatically in from_dict
                self.canvas.vehicle = self.vehicle
                
                # Generate palette automatically from vehicle
                # Ask user if they want to separate multi-part tiles
                separate_parts = messagebox.askyesno(
                    "Palette Generation",
                    "Separate multi-part tiles into individual parts?\n\n"
                    "Yes: Each part gets its own palette entry\n"
                    "No: Multi-part tiles stay combined"
                )
                
                try:
                    auto_palette = Palette.generate_from_vehicle(
                        self.vehicle, 
                        f"{self.vehicle.id}_palette",
                        separate_parts=separate_parts
                    )
                    self.palette = auto_palette
                    self.canvas.palette = auto_palette
                    
                    # Update palette UI
                    palette_name = auto_palette.palette_id or "Auto-generated"
                    self.palette_label.config(text=f"Palette: {palette_name} (auto)")
                    
                    # Update characters list with formatted entries
                    self.update_palette_display()
                    
                    if auto_palette.get_available_characters():
                        # Set first character as default
                        first_char = auto_palette.get_available_characters()[0]
                        self.char_var.set(first_char)
                    
                    self.update_status(f"Loaded vehicle and generated palette with {len(auto_palette.get_available_characters())} characters")
                except Exception as e:
                    self.update_status(f"Loaded vehicle (palette generation failed: {e})")
                
                # Update UI
                self.vehicle_name_entry.delete(0, tk.END)
                self.vehicle_name_entry.insert(0, self.vehicle.name)
                self.vehicle_id_entry.delete(0, tk.END)
                self.vehicle_id_entry.insert(0, self.vehicle.id)
                self.update_parts_count()
                
                # Redraw canvas (this will center and show the vehicle)
                self.canvas.redraw()
                # Scroll to show the vehicle - use recenter_view to properly center
                self.canvas.update_idletasks()
                self.recenter_view()
                
                self.update_status(f"Loaded vehicle from {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load vehicle:\n{e}")
    
    def save_vehicle(self):
        """Save the current vehicle."""
        filename = filedialog.asksaveasfilename(
            title="Save Vehicle",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir="vehicles"
        )
        if filename:
            try:
                self.vehicle.save_to_file(filename)
                self.update_status(f"Saved vehicle to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save vehicle:\n{e}")
    
    def update_parts_count(self):
        """Update the parts and items count labels."""
        parts_count = len(self.vehicle.parts) if hasattr(self.vehicle, 'parts') else 0
        items_count = len(self.vehicle.items) if hasattr(self.vehicle, 'items') else 0
        self.parts_label.config(text=str(parts_count))
        self.items_label.config(text=str(items_count))
    
    def update_status(self, message):
        """Update the status bar."""
        self.status_bar.config(text=message)
    
    def show_information_atlas(self):
        """Show an information dialog explaining UI elements and features."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Information Atlas")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        
        # Label
        label = ttk.Label(dialog, text="Vehicle Painter - Information Atlas", font=("TkDefaultFont", 12, "bold"))
        label.pack(pady=10)
        
        # Text widget with scrollbar
        text_frame = ttk.Frame(dialog)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_widget = tk.Text(
            text_frame,
            yscrollcommand=scrollbar.set,
            wrap=tk.WORD,
            padx=10,
            pady=10,
            font=("TkDefaultFont", 10)
        )
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_widget.yview)
        
        # Information content
        info_text = """VEHICLE PAINTER INFORMATION ATLAS

=== VISUAL INDICATORS ===

ORANGE DOTS:
  • Orange dots appear in the top-right corner of tiles that contain MULTIPLE vehicle parts
  • This helps you quickly identify complex tiles
  • Click on a tile with an orange dot to see all parts and items in the Edit Tile dialog

ORIGIN MARKERS:
  • Red lines mark the X=0 and Y=0 axes
  • A red circle marks the origin point (0, 0)
  • These help you orient yourself on the infinite grid

COLORED TILES:
  • Light blue tiles: Contain vehicle parts or items
  • White tiles: Empty grid cells
  • Blue outline: Indicates a cell with content

=== TOOLS ===

PAINT TOOL:
  • Click or drag to paint tiles using the selected palette character
  • Uses the character shown in the "Char" field
  • Creates parts and items based on the palette definition

ERASE TOOL:
  • Click or drag to remove all parts and items from tiles
  • Completely clears a tile

EDIT TILE TOOL:
  • Click on a tile to open the detailed editor
  • Right-click also opens the tile editor
  • Add, remove, or modify individual parts and items
  • Edit fuel types, item chances, and more

=== KEYBOARD NAVIGATION ===

ARROW KEYS:
  • Use Up, Down, Left, Right to move the view one tile at a time
  • Click the canvas first to give it focus
  • Great for precise navigation

=== PALETTE ===

PALETTE SYSTEM:
  • Load palettes from JSON files or generate them from vehicles
  • Each character represents a specific part/item configuration
  • Characters are automatically generated when loading a vehicle
  • Search the palette to find specific parts or items
  • Double-click palette entries to edit them

=== VEHICLE LOADING ===

MULTI-VEHICLE FILES:
  • If a JSON file contains multiple vehicles, a selection dialog appears
  • Choose which vehicle to load from the list
  • Shows vehicle name, ID, and part/item counts

COORDINATE NORMALIZATION:
  • Vehicles are automatically shifted to start at (0, 0)
  • Ensures vehicles align properly with the grid

=== MOUSE HOVER ===

TOOLTIPS:
  • Hover over tiles to see detailed information
  • Shows all parts and items at that location
  • Displays part types, fuel types, item groups, and chances
  • Automatically hides when you move the mouse away

=== PANEL CONTROLS ===

LEFT PANEL:
  • Drag the separator bar to resize the left panel
  • All controls expand to fill the panel width
  • Palette, Tools, Vehicle Info, and File operations

RECENTER VIEW:
  • Click "Recenter" button (bottom right of canvas)
  • Centers the view on the vehicle (if loaded)
  • Or centers on origin (0, 0) if no vehicle

=== SAVING ===

EXPORT FORMAT:
  • Vehicles are saved in Cataclysm: Bright Nights JSON format
  • Includes "exported with vehicle painter" comment
  • Blueprint comes after parts/items
  • Matches the formatting style of official vehicle files

=== TIPS ===

1. Use the palette search to quickly find specific parts
2. Right-click is a quick way to edit tiles
3. Arrow keys provide precise navigation
4. Orange dots indicate tiles worth inspecting
5. Hover tooltips give instant information without clicking
6. The recenter button helps navigate large vehicles

For more information, check the project documentation."""
        
        text_widget.insert("1.0", info_text)
        text_widget.config(state=tk.DISABLED)  # Make it read-only
        
        # Close button
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Close", command=dialog.destroy).pack()
        
        # Make dialog modal
        dialog.update_idletasks()
        try:
            dialog.grab_set()
        except tk.TclError:
            pass
        
        # Center dialog
        dialog.update_idletasks()
        dialog_width = dialog.winfo_width()
        dialog_height = dialog.winfo_height()
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_width = self.root.winfo_width()
        root_height = self.root.winfo_height()
        dialog_x = root_x + (root_width - dialog_width) // 2
        dialog_y = root_y + (root_height - dialog_height) // 2
        dialog.geometry(f"+{dialog_x}+{dialog_y}")
    
    def _load_vehicles_from_file(self, filename):
        """Load vehicles from a JSON file. Handles both single vehicles and arrays of vehicles.
        
        Returns:
            List of Vehicle objects found in the file.
        """
        import json
        vehicles = []
        
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            # Check if it's an array of vehicles
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and ('parts' in item or 'id' in item):
                        try:
                            vehicle = Vehicle.from_dict(item)
                            vehicles.append(vehicle)
                        except Exception as e:
                            # Skip invalid vehicle entries
                            continue
            # Check if it's a single vehicle object
            elif isinstance(data, dict):
                if 'parts' in data or 'id' in data:
                    try:
                        vehicle = Vehicle.from_dict(data)
                        vehicles.append(vehicle)
                    except Exception as e:
                        # Single vehicle but invalid
                        pass
        except json.JSONDecodeError as e:
            # Invalid JSON
            raise ValueError(f"Invalid JSON file: {e}")
        except Exception as e:
            raise ValueError(f"Error reading file: {e}")
        
        return vehicles
    
    def _select_vehicle(self, vehicles, filename):
        """Show a dialog to select a vehicle from a list.
        
        Args:
            vehicles: List of Vehicle objects
            filename: Name of the file being loaded (for display)
        
        Returns:
            Selected Vehicle object, or None if cancelled
        """
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Select Vehicle - {filename}")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        
        # Label
        label = ttk.Label(dialog, text=f"Found {len(vehicles)} vehicles. Select one to load:")
        label.pack(pady=10)
        
        # Listbox with scrollbar
        listbox_frame = ttk.Frame(dialog)
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set, height=15)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        
        # Populate listbox with vehicle info
        vehicle_items = []
        for vehicle in vehicles:
            name = vehicle.name or "Unnamed"
            vid = vehicle.id or "unknown"
            parts_count = len(vehicle.parts) if vehicle.parts else 0
            items_count = len(vehicle.items) if vehicle.items else 0
            display_text = f"{name} (ID: {vid}) - {parts_count} parts, {items_count} items"
            listbox.insert(tk.END, display_text)
            vehicle_items.append(vehicle)
        
        # Select first item
        if vehicle_items:
            listbox.selection_set(0)
            listbox.activate(0)
        
        selected_vehicle = None
        
        def on_ok():
            nonlocal selected_vehicle
            selection = listbox.curselection()
            if selection:
                index = selection[0]
                selected_vehicle = vehicle_items[index]
            dialog.destroy()
        
        def on_double_click(event):
            on_ok()
        
        def on_cancel():
            dialog.destroy()
        
        # Bind double-click
        listbox.bind('<Double-Button-1>', on_double_click)
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.LEFT, padx=5)
        
        # Make dialog modal
        dialog.update_idletasks()
        try:
            dialog.grab_set()
        except tk.TclError:
            pass
        
        # Center dialog
        dialog.update_idletasks()
        dialog_width = dialog.winfo_width()
        dialog_height = dialog.winfo_height()
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_width = self.root.winfo_width()
        root_height = self.root.winfo_height()
        dialog_x = root_x + (root_width - dialog_width) // 2
        dialog_y = root_y + (root_height - dialog_height) // 2
        dialog.geometry(f"+{dialog_x}+{dialog_y}")
        
        # Wait for dialog to close
        dialog.wait_window()
        
        return selected_vehicle


def main():
    root = tk.Tk()
    app = VehiclePainterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

