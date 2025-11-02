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
        self.left_panel.rowconfigure(0, weight=1)
        
        # Create scrollable canvas for left panel content
        left_canvas = tk.Canvas(self.left_panel, highlightthickness=0)
        left_scrollbar = ttk.Scrollbar(self.left_panel, orient=tk.VERTICAL, command=left_canvas.yview)
        self.left_scrollable_frame = ttk.Frame(left_canvas)
        self.left_scrollable_frame.columnconfigure(0, weight=1)  # Allow widgets to fill width
        
        # Configure canvas scrolling
        self.left_scrollable_frame.bind(
            "<Configure>",
            lambda e: left_canvas.configure(scrollregion=left_canvas.bbox("all"))
        )
        
        left_canvas.create_window((0, 0), window=self.left_scrollable_frame, anchor="nw")
        left_canvas.configure(yscrollcommand=left_scrollbar.set)
        
        # Grid canvas and scrollbar
        left_canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        left_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Update scroll region when window is resized or content changes
        def update_left_scroll_region(event=None):
            # Update the scroll region
            left_canvas.configure(scrollregion=left_canvas.bbox("all"))
            # Make sure the scrollable frame width matches canvas width (minus scrollbar if visible)
            canvas_width = left_canvas.winfo_width()
            if canvas_width > 1:
                left_canvas.itemconfig(left_canvas.find_all()[0], width=canvas_width)
        
        def on_canvas_configure(event):
            # When canvas is resized, update scrollable frame width
            canvas_width = event.width
            left_canvas.itemconfig(left_canvas.find_all()[0], width=canvas_width)
            update_left_scroll_region()
        
        self.left_scrollable_frame.bind("<Configure>", update_left_scroll_region)
        left_canvas.bind("<Configure>", on_canvas_configure)
        
        # Bind mousewheel to canvas (only when hovering over it)
        def on_left_panel_scroll_wheel(event):
            # Only scroll if mouse is over the left panel
            if self.left_panel.winfo_containing(event.x_root, event.y_root):
                left_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        def on_left_panel_scroll_button(event):
            # Linux button 4/5 for scrolling
            if event.num == 4:  # Scroll up
                left_canvas.yview_scroll(-1, "units")
            elif event.num == 5:  # Scroll down
                left_canvas.yview_scroll(1, "units")
        
        # Bind to left_panel instead of bind_all to avoid conflicts
        # Windows/Mac: MouseWheel
        self.left_panel.bind("<MouseWheel>", on_left_panel_scroll_wheel)
        left_canvas.bind("<MouseWheel>", on_left_panel_scroll_wheel)
        self.left_scrollable_frame.bind("<MouseWheel>", on_left_panel_scroll_wheel)
        # Linux: Button-4 and Button-5
        self.left_panel.bind("<Button-4>", on_left_panel_scroll_button)
        self.left_panel.bind("<Button-5>", on_left_panel_scroll_button)
        left_canvas.bind("<Button-4>", on_left_panel_scroll_button)
        left_canvas.bind("<Button-5>", on_left_panel_scroll_button)
        self.left_scrollable_frame.bind("<Button-4>", on_left_panel_scroll_button)
        self.left_scrollable_frame.bind("<Button-5>", on_left_panel_scroll_button)
        
        # Store references
        self.left_canvas = left_canvas
        self.left_scrollbar = left_scrollbar
        
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
        palette_frame = ttk.LabelFrame(self.left_scrollable_frame, text="Palette", padding="10")
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
        tools_frame = ttk.LabelFrame(self.left_scrollable_frame, text="Tools", padding="10")
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
        
        ttk.Radiobutton(
            tools_frame,
            text="Square",
            variable=self.tool_var,
            value="square"
        ).grid(row=3, column=0, sticky=tk.W)
        
        ttk.Radiobutton(
            tools_frame,
            text="Square Erase",
            variable=self.tool_var,
            value="square_erase"
        ).grid(row=4, column=0, sticky=tk.W)
        
        ttk.Radiobutton(
            tools_frame,
            text="Pan",
            variable=self.tool_var,
            value="pan"
        ).grid(row=5, column=0, sticky=tk.W)
        
        # Undo/Redo buttons
        undo_redo_frame = ttk.Frame(tools_frame)
        undo_redo_frame.grid(row=6, column=0, sticky=(tk.W, tk.E), pady=(10, 5))
        undo_redo_frame.columnconfigure(0, weight=1)
        undo_redo_frame.columnconfigure(1, weight=1)
        
        self.undo_button = ttk.Button(
            undo_redo_frame,
            text="Undo (Ctrl+Z)",
            command=self.undo_action
        )
        self.undo_button.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        self.redo_button = ttk.Button(
            undo_redo_frame,
            text="Redo (Ctrl+Y)",
            command=self.redo_action
        )
        self.redo_button.grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        ttk.Label(
            tools_frame,
            text="Middle-click: Edit Tile",
            font=("TkDefaultFont", 7),
            foreground="gray"
        ).grid(row=7, column=0, sticky=tk.W, pady=(5, 0))
        
        ttk.Label(
            tools_frame,
            text="Right-click: Delete/Erase",
            font=("TkDefaultFont", 7),
            foreground="gray"
        ).grid(row=8, column=0, sticky=tk.W)
        
        # Vehicle info frame
        info_frame = ttk.LabelFrame(self.left_scrollable_frame, text="Vehicle Info", padding="10")
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
        file_frame = ttk.LabelFrame(self.left_scrollable_frame, text="File", padding="10")
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
        self.canvas.zoom_callback = self.update_zoom_label
        self.canvas.coordinate_callback = self.update_coordinate_label
        
        # Add zoom and recenter buttons on canvas frame (bottom right)
        button_frame = ttk.Frame(canvas_frame)
        self.zoom_out_button = ttk.Button(
            button_frame,
            text="−",
            command=self.zoom_out,
            width=3
        )
        self.zoom_out_button.pack(side=tk.LEFT, padx=2)
        
        self.zoom_label = ttk.Label(button_frame, text="100%")
        self.zoom_label.pack(side=tk.LEFT, padx=2)
        
        self.zoom_in_button = ttk.Button(
            button_frame,
            text="+",
            command=self.zoom_in,
            width=3
        )
        self.zoom_in_button.pack(side=tk.LEFT, padx=2)
        
        self.reset_zoom_button = ttk.Button(
            button_frame,
            text="Reset",
            command=self.reset_zoom,
            width=6
        )
        self.reset_zoom_button.pack(side=tk.LEFT, padx=2)
        
        self.recenter_button = ttk.Button(
            button_frame,
            text="Recenter",
            command=self.recenter_view
        )
        self.recenter_button.pack(side=tk.LEFT, padx=2)
        
        self.recenter_canvas_frame = canvas_frame
        self.button_frame = button_frame
        # Position will be set after canvas is configured
        
        # Add coordinate label in bottom left corner
        self.coordinate_label = ttk.Label(
            canvas_frame,
            text="(0, 0)",
            background="white",
            relief=tk.SUNKEN,
            padding=(5, 2)
        )
        self.coordinate_label.place(x=10, y=10)  # Temporary position, will be updated
        
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
        # Position coordinate label in bottom left corner
        self.position_coordinate_label()
        
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
        """Position the zoom/recenter buttons in the bottom right corner of the canvas."""
        def update_position():
            # Get canvas frame dimensions (not canvas widget, but the frame containing it)
            frame_width = self.recenter_canvas_frame.winfo_width()
            frame_height = self.recenter_canvas_frame.winfo_height()
            if frame_width > 1 and frame_height > 1:
                # Get button frame dimensions
                self.button_frame.update_idletasks()
                btn_width = self.button_frame.winfo_width() or 200
                btn_height = self.button_frame.winfo_height() or 25
                
                # Position in bottom right with some padding (account for scrollbar)
                # Scrollbar is 17px wide, so subtract that from available width
                x = frame_width - btn_width - 25  # Extra padding for scrollbar area
                y = frame_height - btn_height - 25  # Padding from bottom
                
                self.button_frame.place(x=x, y=y)
        
        # Update position after canvas is configured
        self.root.after_idle(update_position)
        # Also update when canvas frame resizes
        self.recenter_canvas_frame.bind("<Configure>", lambda e: update_position())
    
    def position_coordinate_label(self):
        """Position the coordinate label in the bottom left corner of the canvas."""
        def update_position(event=None):
            # Get canvas frame dimensions (not canvas widget, but the frame containing it)
            frame_width = self.recenter_canvas_frame.winfo_width()
            frame_height = self.recenter_canvas_frame.winfo_height()
            if frame_width > 1 and frame_height > 1:
                # Get coordinate label dimensions
                self.coordinate_label.update_idletasks()
                label_width = self.coordinate_label.winfo_width() or 80
                label_height = self.coordinate_label.winfo_height() or 20
                
                # Position in bottom left with some padding
                # Account for horizontal scrollbar at bottom (17px height)
                # The canvas takes up most of the frame, scrollbar is at bottom
                x = 10  # Padding from left edge
                y = frame_height - label_height - 30  # Padding from bottom (accounting for horizontal scrollbar ~17px + padding)
                
                self.coordinate_label.place(x=x, y=y)
        
        # Update position after canvas is configured
        self.root.after_idle(update_position)
        # Also update when canvas frame resizes
        # Use a named function to avoid lambda overwriting issues
        self.recenter_canvas_frame.bind("<Configure>", update_position)
    
    def zoom_in(self):
        """Zoom in on the canvas."""
        self.canvas.zoom_in()
        self.update_zoom_label()
    
    def zoom_out(self):
        """Zoom out on the canvas."""
        self.canvas.zoom_out()
        self.update_zoom_label()
    
    def reset_zoom(self):
        """Reset zoom to 100% and recenter view."""
        self.canvas.reset_zoom()
        self.update_zoom_label()
        # Recenter after resetting zoom
        self.root.after_idle(self.recenter_view)
    
    def update_zoom_label(self):
        """Update the zoom percentage label."""
        zoom_percent = int(self.canvas.zoom_level * 100)
        self.zoom_label.config(text=f"{zoom_percent}%")
    
    def update_coordinate_label(self, grid_x, grid_y):
        """Update the coordinate label with current grid position."""
        if grid_x is None or grid_y is None:
            self.coordinate_label.config(text="")
        else:
            self.coordinate_label.config(text=f"({grid_x}, {grid_y})")
    
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
                
                # Convert grid coordinates to canvas coordinates (grid_size may be float)
                target_canvas_x = center_x * self.canvas.grid_size
                target_canvas_y = center_y * self.canvas.grid_size
                
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
                    # The viewport's left edge should be positioned so the center shows target_canvas_x
                    # left_edge = target_canvas_x - canvas_width / 2
                    # scroll_x represents where the left edge is as a fraction of the scrollable area
                    # left_edge = region_min_x + scroll_x * (region_width - canvas_width)
                    # But Tkinter's xview_moveto uses a simpler model:
                    # The viewport shows from (region_min_x + scroll_x * region_width) to (region_min_x + scroll_x * region_width + canvas_width)
                    # For the center to be at target_x:
                    # target_x = region_min_x + scroll_x * region_width + canvas_width / 2
                    # scroll_x = (target_x - region_min_x - canvas_width / 2) / region_width
                    scroll_x = (target_canvas_x - region_min_x - canvas_width / 2) / region_width
                    scroll_y = (target_canvas_y - region_min_y - canvas_height / 2) / region_height
                    
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
                # Using the same calculation as above
                scroll_x = (0 - region_min_x - canvas_width / 2) / region_width
                scroll_y = (0 - region_min_y - canvas_height / 2) / region_height
                
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
        edit_dialog.geometry("500x650")
        
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
            self.canvas.clear_history()  # Clear undo/redo history for new vehicle
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
                self.canvas.clear_history()  # Clear undo/redo history when loading new vehicle
                
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
    
    def undo_action(self):
        """Handle undo button click."""
        if self.canvas.undo():
            self.update_status("Undo: Last operation undone")
            self.update_parts_count()
        else:
            self.update_status("Nothing to undo")
    
    def redo_action(self):
        """Handle redo button click."""
        if self.canvas.redo():
            self.update_status("Redo: Last undone operation restored")
            self.update_parts_count()
        else:
            self.update_status("Nothing to redo")
    
    def show_information_atlas(self):
        """Show an enhanced information dialog explaining UI elements and features."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Information Atlas - Vehicle Painter")
        dialog.geometry("900x750")
        dialog.transient(self.root)
        
        # Main container
        main_container = ttk.Frame(dialog)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_frame = ttk.Frame(main_container)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = ttk.Label(
            title_frame,
            text="🚗 Vehicle Painter - Information Atlas",
            font=("TkDefaultFont", 16, "bold")
        )
        title_label.pack()
        
        subtitle_label = ttk.Label(
            title_frame,
            text="Complete guide to all features, shortcuts, and tips",
            font=("TkDefaultFont", 9),
            foreground="gray"
        )
        subtitle_label.pack()
        
        # Search frame
        search_frame = ttk.Frame(main_container)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="Search:", font=("TkDefaultFont", 9)).pack(side=tk.LEFT, padx=(0, 5))
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var, width=30)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Notebook for tabs
        notebook = ttk.Notebook(main_container)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tab content functions
        def create_text_widget(parent):
            """Create a text widget with scrollbar."""
            text_frame = ttk.Frame(parent)
            text_frame.pack(fill=tk.BOTH, expand=True)
            
            scrollbar = ttk.Scrollbar(text_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            text_widget = tk.Text(
                text_frame,
                yscrollcommand=scrollbar.set,
                wrap=tk.WORD,
                padx=15,
                pady=15,
                font=("TkDefaultFont", 10),
                relief=tk.FLAT,
                bg="#FAFAFA"
            )
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.config(command=text_widget.yview)
            return text_widget
        
        def configure_text_tags(text_widget):
            """Configure text formatting tags."""
            text_widget.tag_configure("heading", font=("TkDefaultFont", 12, "bold"), foreground="#2C3E50")
            text_widget.tag_configure("subheading", font=("TkDefaultFont", 10, "bold"), foreground="#34495E")
            text_widget.tag_configure("highlight", foreground="#E74C3C", font=("TkDefaultFont", 10, "bold"))
            text_widget.tag_configure("code", font=("Courier", 9), background="#ECF0F1", relief=tk.RAISED, borderwidth=1)
            text_widget.tag_configure("tip", foreground="#27AE60", font=("TkDefaultFont", 10))
            text_widget.tag_configure("bullet", foreground="#3498DB")
        
        # Tab 1: Getting Started
        tab1 = ttk.Frame(notebook)
        notebook.add(tab1, text="🚀 Getting Started")
        text1 = create_text_widget(tab1)
        configure_text_tags(text1)
        
        getting_started = """Getting Started with Vehicle Painter

Welcome to the Vehicle Painter for Cataclysm: Bright Nights! This tool allows you to create, edit, and customize vehicles with a visual, grid-based interface.

QUICK START GUIDE

1. LOAD OR CREATE A VEHICLE
   • Click "Load Vehicle" to open an existing vehicle JSON file
   • Click "New Vehicle" to start from scratch
   • Vehicles are automatically centered at (0, 0) when loaded

2. UNDERSTAND THE INTERFACE
   • Left Panel: Palette, tools, and vehicle information
   • Center Canvas: Your vehicle grid where you paint and edit
   • Bottom Right: Zoom controls and recenter button
   • Bottom Left: Coordinate display showing current mouse position

3. PAINT YOUR FIRST TILE
   • Select a palette entry (character) from the list
   • Choose "Paint" tool from the Tools section
   • Click or drag on the canvas to place parts and items

4. SAVE YOUR WORK
   • Click "Save Vehicle" to export your creation
   • Files are saved in Cataclysm: Bright Nights JSON format
   • Compatible with the game's vehicle system

BASIC WORKFLOW

The typical workflow is:
1. Load or create a vehicle
2. Select parts/items from the palette (or generate palette from vehicle)
3. Use Paint tool to place them on the grid
4. Use Edit Tile tool (middle-click) to fine-tune individual tiles
5. Use Erase tool (right-click) to remove unwanted parts
6. Save your vehicle

COORDINATE SYSTEM

• Grid coordinates are shown in the bottom-left corner as (x, y)
• Origin (0, 0) is marked with red lines and a circle
• The grid extends infinitely in all directions
• Use arrow keys for precise navigation
• Click "Recenter" to center your view on the vehicle or origin

"""
        text1.insert("1.0", getting_started)
        text1.config(state=tk.DISABLED)
        
        # Tab 2: Tools & Features
        tab2 = ttk.Frame(notebook)
        notebook.add(tab2, text="🛠️ Tools & Features")
        text2 = create_text_widget(tab2)
        configure_text_tags(text2)
        
        tools_features = """Tools & Features Guide

TOOLS OVERVIEW

The application provides three main tools accessible from the Tools section in the left panel:

PAINT TOOL (Default)
   • Purpose: Place parts and items on the grid
   • Usage: Click or drag to paint tiles
   • Palette: Uses the currently selected palette character
   • Behavior:
     - Left-click: Place one tile
     - Left-drag: Continuously place tiles as you drag
     - Automatically creates parts/items based on palette definition
   • Tip: The selected character in the palette determines what gets placed

ERASE TOOL
   • Purpose: Remove all parts and items from tiles
   • Usage: Click or drag to erase tiles
   • Behavior:
     - Right-click: Erase one tile
     - Right-drag: Continuously erase tiles as you drag
     - Completely clears tiles (parts AND items)
   • Keyboard: Right mouse button always erases, regardless of tool selection
   • Warning: Erasing cannot be undone (though you can reload your save)

EDIT TILE TOOL
   • Purpose: Detailed editing of individual tiles
   • Usage: Click on a tile to open the editor dialog
   • Triggers:
     - Middle-click on any tile
     - Left-click when Edit Tile tool is selected
     - Double-click a tile with the Paint tool
   • Features:
     - View all parts and items at that location
     - Add new parts with specific properties
     - Remove individual parts or items
     - Edit fuel types for parts
     - Edit item chances and groups
     - Modify existing part configurations

ZOOM CONTROLS

Located in the bottom-right corner of the canvas:

• Zoom Out (-): Decrease zoom level (minimum 50%)
• Zoom Level Display: Shows current zoom percentage
• Zoom In (+): Increase zoom level (maximum 400%)
• Reset: Return to 100% zoom and recenter view
• Recenter: Center view on vehicle or origin

Keyboard Shortcuts:
• Ctrl + Mouse Wheel: Zoom in/out at cursor position
• Mouse Wheel: Scroll the canvas (when not holding Ctrl)

VISUAL INDICATORS

On the Canvas:
• Light Blue Tiles: Contain vehicle parts or items
• White Tiles: Empty grid cells
• Green Plus (Top-Right): Tile contains items that spawn
• Orange Plus (Bottom-Right): Tile contains multiple parts
• Red Lines: X=0 and Y=0 axes
• Red Circle: Origin point (0, 0)
• Coordinate Display: Current mouse grid position (bottom-left)

In the Palette:
• Character: The symbol used to represent this configuration
• Description: User-friendly name for the palette entry
• Parts: List of vehicle parts included
• Items: List of items/item groups that spawn

COORDINATE DISPLAY

The coordinate display in the bottom-left corner shows:
• Current grid position of your mouse cursor
• Format: (x, y) where x and y are grid coordinates
• Updates in real-time as you move the mouse
• Disappears when mouse leaves the canvas area

"""
        text2.insert("1.0", tools_features)
        text2.config(state=tk.DISABLED)
        
        # Tab 3: Keyboard Shortcuts
        tab3 = ttk.Frame(notebook)
        notebook.add(tab3, text="⌨️ Keyboard Shortcuts")
        text3 = create_text_widget(tab3)
        configure_text_tags(text3)
        
        shortcuts = """Complete Keyboard Shortcuts Reference

NAVIGATION SHORTCUTS

Arrow Keys (Canvas must have focus)
   ↑ Up Arrow:      Scroll view up by one grid cell
   ↓ Down Arrow:    Scroll view down by one grid cell
   ← Left Arrow:    Scroll view left by one grid cell
   → Right Arrow:   Scroll view right by one grid cell
   
   Note: Click the canvas first to give it keyboard focus

MOUSE SHORTCUTS

Left Mouse Button:
   • Click:         Place/paint tile (Paint tool) or edit tile (Edit tool)
   • Drag:          Continuous painting or editing

Middle Mouse Button:
   • Click:         Always opens tile editor, regardless of selected tool
   • Quick Edit:    Fastest way to edit a tile

Right Mouse Button:
   • Click:         Erase tile (always, regardless of selected tool)
   • Drag:          Continuous erasing

Mouse Wheel:
   • Scroll:        Scroll canvas up/down (when not holding Ctrl)
   • Ctrl + Scroll: Zoom in/out at cursor position

KEYBOARD HOTKEYS FOR PALETTE

When canvas has focus:
   • Press any character key: Switch to that palette entry (if it exists)
   • Automatically switches to Paint mode
   • Only switches palette selection, doesn't place tile automatically

Example:
   1. Click canvas to give it focus
   2. Press 'a' key → selects palette entry with character 'a'
   3. Left-click to place that palette entry

FILE OPERATIONS

There are no keyboard shortcuts for file operations. Use the buttons:
   • New Vehicle:    Creates a fresh vehicle
   • Load Vehicle:   Opens file dialog to load JSON
   • Save Vehicle:   Saves current vehicle to JSON
   • Information Atlas: Opens this help dialog

EFFICIENCY TIPS

Fast Painting Workflow:
   1. Use keyboard hotkeys to quickly switch palette entries
   2. Hold left mouse button and drag for continuous painting
   3. Use arrow keys to navigate while painting

Fast Editing Workflow:
   1. Use middle-click for instant tile editor
   2. Use right-click drag for quick erasing
   3. Use arrow keys for precise positioning

Fast Navigation:
   1. Use arrow keys for grid-aligned movement
   2. Use mouse wheel for smooth scrolling
   3. Use Recenter button to jump to vehicle/origin
   4. Use Ctrl+wheel to zoom while keeping position centered

"""
        text3.insert("1.0", shortcuts)
        text3.config(state=tk.DISABLED)
        
        # Tab 4: Palette System
        tab4 = ttk.Frame(notebook)
        notebook.add(tab4, text="🎨 Palette System")
        text4 = create_text_widget(tab4)
        configure_text_tags(text4)
        
        palette_info = """Palette System Guide

UNDERSTANDING THE PALETTE

The palette is the core of the painting system. Each character in the palette represents a specific configuration of vehicle parts and/or items.

PALETTE ENTRIES

Each palette entry contains:
   • Character: Single character symbol (e.g., 'a', 'b', '1', '!')
   • Description: Human-readable name
   • Parts: List of vehicle parts (e.g., "frame", "wheel", "seat")
   • Items: List of items or item groups that spawn at this location

Example Palette Entry:
   Character: 'f'
   Description: "Frame"
   Parts: frame
   Items: (none)

Another Example:
   Character: 's'
   Description: "Seat with items"
   Parts: seat
   Items: item:tool_belt, groups:tools

GENERATING PALETTES

Automatic Generation:
   • When you load a vehicle, a palette is automatically generated
   • Each unique part/item combination gets its own character
   • Characters are assigned in order: a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r, s, t, u, v, w, x, y, z
   • Then: A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T, U, V, W, X, Y, Z
   • Then: 0, 1, 2, 3, 4, 5, 6, 7, 8, 9
   • Then: !, @, #, $, %, ^, &, *, (, ), -, _, +, =, [, ], {, }, |, \\, :, ;, ", ', <, >, ?, /, ~, `

Multi-Part Separation:
   • When loading, you can choose to separate multi-part tiles
   • If enabled, tiles with multiple parts become separate palette entries
   • Allows individual editing of each part

MANAGING PALETTES

Loading Palettes:
   • Click "Load Palette" to load a saved palette JSON file
   • Palettes can be saved separately from vehicles
   • Useful for creating reusable part configurations

Saving Palettes:
   • Click "Save Palette" to export your current palette
   • Saves all palette entries with their configurations
   • Can be loaded later for reuse

Searching Palettes:
   • Use the search box above the palette list
   • Filters entries by character, description, or part/item names
   • Case-insensitive search
   • Real-time filtering as you type

EDITING PALETTE ENTRIES

To Edit an Entry:
   1. Double-click any entry in the palette list
   2. Or select an entry and click "Edit Palette Entry"

Edit Dialog Options:
   • Change character (must be unique)
   • Edit description
   • Modify parts list
   • Modify items/item groups
   • Add or remove elements

Adding New Entries:
   1. Click "Add Palette Entry" button
   2. Choose a unique character
   3. Define description, parts, and items
   4. Save to add to palette

USING THE PALETTE

Selecting an Entry:
   • Click on an entry in the palette list
   • Or type the character key when canvas has focus
   • Selected entry is highlighted

Painting with Palette:
   1. Select a palette entry
   2. Choose Paint tool
   3. Click or drag on canvas
   4. Tiles are painted with that entry's configuration

Keyboard Hotkeys:
   • Press any character key to switch to that palette entry
   • Automatically switches to Paint mode
   • Speeds up workflow significantly

TIPS FOR EFFICIENT PALETTE USE

1. Organize your palette: Use descriptive names
2. Use keyboard hotkeys: Much faster than clicking
3. Search frequently: Find entries quickly
4. Create templates: Save common configurations
5. Separate complex tiles: Use multi-part separation for easier editing

"""
        text4.insert("1.0", palette_info)
        text4.config(state=tk.DISABLED)
        
        # Tab 5: Tips & Tricks
        tab5 = ttk.Frame(notebook)
        notebook.add(tab5, text="💡 Tips & Tricks")
        text5 = create_text_widget(tab5)
        configure_text_tags(text5)
        
        tips_tricks = """Tips & Tricks for Efficient Vehicle Building

GENERAL WORKFLOW TIPS

1. START WITH A PLAN
   • Sketch your vehicle layout on paper first
   • Identify major components (frame, wheels, engine, etc.)
   • Plan the general shape and structure

2. USE THE ORIGIN AS REFERENCE
   • Start building from (0, 0) or nearby
   • Use origin markers (red lines) for alignment
   • Keeps your vehicle organized and centered

3. BUILD IN LAYERS
   • Start with frame/base structure
   • Add wheels and movement components
   • Add functional parts (engine, seats, etc.)
   • Add decorative/optional parts last

PALETTE OPTIMIZATION

1. CREATE COMMON TEMPLATES
   • Save frequently used part combinations
   • Reuse templates across multiple vehicles
   • Example: "Standard Wheel" = wheel + frame corner

2. USE DESCRIPTIVE NAMES
   • Name palette entries clearly
   • Makes searching easier
   • Helps remember what each character represents

3. ORGANIZE BY FUNCTION
   • Group related palette entries together
   • Use naming conventions (e.g., "wheel_front", "wheel_back")
   • Makes large palettes manageable

4. SEPARATE COMPLEX TILES
   • Enable multi-part separation when loading
   • Allows fine-tuning of individual parts
   • Easier to edit later

NAVIGATION EFFICIENCY

1. USE ARROW KEYS FOR PRECISION
   • Much more accurate than mouse scrolling
   • Grid-aligned movement
   • Essential for detailed work

2. ZOOM FOR DETAIL WORK
   • Zoom in (Ctrl+wheel) for precise placement
   • Zoom out to see overall structure
   • Use Reset button to quickly return to 100%

3. USE RECENTER FREQUENTLY
   • Quickly jump to vehicle center
   • Find your vehicle if you get lost
   • Useful after loading or large edits

EDITING TECHNIQUES

1. MIDDLE-CLICK FOR QUICK EDITS
   • Fastest way to open tile editor
   • No need to switch tools
   • Works from any tool mode

2. RIGHT-CLICK DRAG FOR CLEANUP
   • Efficiently remove unwanted parts
   • Great for fixing mistakes
   • Continuous erasing saves time

3. USE COORDINATE DISPLAY
   • Know exactly where you are
   • Plan tile placement precisely
   • Helpful for symmetry and alignment

4. INSPECT ORANGE INDICATORS
   • Orange plus means multiple parts
   • Often needs fine-tuning
   • Use tile editor to verify configuration

WORKFLOW SHORTCUTS

Fast Painting:
   1. Use keyboard hotkeys to switch palette entries
   2. Hold left mouse and drag
   3. Use arrow keys to navigate while painting

Fast Editing:
   1. Middle-click to edit tiles
   2. Use keyboard shortcuts in dialog
   3. Right-click drag to erase mistakes

Fast Navigation:
   1. Arrow keys for grid movement
   2. Mouse wheel for smooth scrolling
   3. Recenter button for jumping

ADVANCED TECHNIQUES

1. HOVER TOOLTIPS
   • Get instant information without clicking
   • See all parts and items at a glance
   • Perfect for verification

2. SEARCH FUNCTIONALITY
   • Quickly find specific parts in palette
   • Filter by part name, item name, or description
   • Essential for large palettes

3. MULTI-PART SEPARATION
   • Separate complex tiles during loading
   • Edit each part individually
   • Recombine as needed

4. COORDINATE PLANNING
   • Plan symmetrical vehicles using coordinates
   • Mirror parts across axes
   • Use coordinate display for precision

COMMON WORKFLOWS

Building a New Vehicle:
   1. New Vehicle → Name and ID
   2. Build frame structure
   3. Add wheels and engine
   4. Add seats and storage
   5. Add optional parts
   6. Save vehicle

Editing Existing Vehicle:
   1. Load Vehicle → Select vehicle
   2. Recenter view
   3. Use middle-click to edit specific tiles
   4. Use right-click to remove unwanted parts
   5. Save changes

Creating a Palette Template:
   1. Build a vehicle with common configurations
   2. Load it to generate palette
   3. Save palette separately
   4. Reuse palette for similar vehicles

TROUBLESHOOTING

If tiles aren't appearing:
   • Check palette is loaded
   • Verify Paint tool is selected
   • Ensure a palette entry is selected

If editing doesn't work:
   • Make sure you're clicking on a tile with content
   • Try middle-click instead of left-click
   • Check tooltip to see what's at that location

If coordinates seem wrong:
   • Use Recenter button
   • Check origin markers (red lines)
   • Verify coordinate display matches expectations

If palette isn't generating:
   • Ensure vehicle file is valid JSON
   • Check parts are properly formatted
   • Try loading a known-good vehicle file

"""
        text5.insert("1.0", tips_tricks)
        text5.config(state=tk.DISABLED)
        
        # Tab 6: File Formats
        tab6 = ttk.Frame(notebook)
        notebook.add(tab6, text="📁 File Formats")
        text6 = create_text_widget(tab6)
        configure_text_tags(text6)
        
        file_formats = """File Format Documentation

VEHICLE JSON FORMAT

Vehicles are saved in Cataclysm: Bright Nights JSON format. The structure is:

{
  "type": "vehicle",
  "id": "vehicle_id_here",
  "name": "Vehicle Name",
  "parts": [
    {
      "part": "frame",
      "x": 0,
      "y": 0
    },
    {
      "part": "wheel",
      "x": 1,
      "y": 0
    }
  ],
  "items": [
    {
      "item": "tool_belt",
      "x": 0,
      "y": 0,
      "chance": 100
    }
  ],
  "blueprint": {
    "id": "vehicle_id_here",
    "name": "Vehicle Name"
  }
}

COORDINATE SYSTEM

• Coordinates are integer values (x, y)
• Grid-based positioning
• Vehicles are normalized to start near (0, 0) when loaded
• Negative coordinates are supported

PART DEFINITIONS

Simple Parts:
{
  "part": "frame",
  "x": 0,
  "y": 0
}

Parts with Fuel:
{
  "part": "engine",
  "x": 0,
  "y": 0,
  "fuel": "gasoline"
}

Parts with Multiple Components:
{
  "part": "frame",
  "x": 0,
  "y": 0,
  "parts": [
    {"part": "frame"},
    {"part": "wheel"}
  ]
}

ITEM DEFINITIONS

Items by Name:
{
  "item": "tool_belt",
  "x": 0,
  "y": 0
}

Items with Chance:
{
  "item": "rope",
  "x": 0,
  "y": 0,
  "chance": 75
}

Item Groups:
{
  "item_groups": ["tools", "survival"],
  "x": 0,
  "y": 0
}

Combined:
{
  "item": "lighter",
  "item_groups": ["tools"],
  "x": 0,
  "y": 0,
  "chance": 50
}

PALETTE JSON FORMAT

Palettes are saved separately and can be reused:

{
  "characters": {
    "a": {
      "description": "Frame",
      "parts": ["frame"],
      "items": []
    },
    "b": {
      "description": "Wheel",
      "parts": ["wheel"],
      "items": []
    }
  },
  "items": {
    "s": {
      "description": "Seat with tools",
      "parts": ["seat"],
      "items": [
        {"item": "tool_belt"},
        {"item_groups": ["survival"]}
      ]
    }
  }
}

LOADING BEHAVIOR

Multi-Vehicle Files:
• If JSON contains array of vehicles, selection dialog appears
• Shows vehicle name, ID, and part/item counts
• Choose which vehicle to load

Coordinate Normalization:
• Vehicles automatically shifted to start at (0, 0)
• Ensures consistent positioning
• Original coordinates preserved in saved file

Part Separation:
• Option to separate multi-part tiles when loading
• Each part becomes individual palette entry
• Allows granular editing

SAVING BEHAVIOR

Export Format:
• Matches Cataclysm: Bright Nights format
• Includes export comment
• Blueprint comes after parts/items
• Proper JSON formatting with indentation

File Structure:
• Parts section first
• Items section second
• Blueprint section last
• Comments added for clarity

COMPATIBILITY

The Vehicle Painter is designed to be compatible with:
• Cataclysm: Bright Nights vehicle JSON files
• Standard vehicle part names
• Standard item IDs and item groups
• Standard fuel types

When loading vehicles:
• Preserves all original data
• Handles missing fields gracefully
• Normalizes coordinates for editing
• Maintains compatibility on save

TIPS FOR FILE MANAGEMENT

1. BACKUP YOUR WORK
   • Save frequently
   • Keep backup copies
   • Version control for complex vehicles

2. ORGANIZE FILES
   • Use descriptive filenames
   • Group related vehicles
   • Save palettes separately

3. VALIDATE BEFORE SAVING
   • Check vehicle looks correct
   • Verify all parts are placed
   • Test in game if possible

4. REUSE PALETTES
   • Save common configurations
   • Load palettes for similar vehicles
   • Build a library of templates

"""
        text6.insert("1.0", file_formats)
        text6.config(state=tk.DISABLED)
        
        # Search functionality
        def search_text(search_term):
            """Search through all tabs for the search term."""
            if not search_term:
                # Reset all tabs
                for i in range(notebook.index("end")):
                    tab = notebook.nametowidget(notebook.tabs()[i])
                    if tab.winfo_children():
                        text_frame = tab.winfo_children()[0]
                        if text_frame.winfo_children():
                            text_widget = text_frame.winfo_children()[1]
                            text_widget.tag_remove("search_highlight", "1.0", tk.END)
                return
            
            search_term_lower = search_term.lower()
            found_any = False
            
            for i in range(notebook.index("end")):
                tab = notebook.nametowidget(notebook.tabs()[i])
                if not tab.winfo_children():
                    continue
                text_frame = tab.winfo_children()[0]
                if not text_frame.winfo_children():
                    continue
                text_widget = text_frame.winfo_children()[1]
                text_widget.tag_remove("search_highlight", "1.0", tk.END)
                
                content = text_widget.get("1.0", tk.END).lower()
                if search_term_lower in content:
                    found_any = True
                    # Find and highlight matches
                    start = "1.0"
                    while True:
                        pos = text_widget.search(search_term_lower, start, tk.END, nocase=True)
                        if not pos:
                            break
                        end = f"{pos}+{len(search_term)}c"
                        text_widget.tag_add("search_highlight", pos, end)
                        start = end
                    
                    text_widget.tag_config("search_highlight", background="#FFEB3B", foreground="#000")
                    
                    if not found_any or notebook.select() != notebook.tabs()[i]:
                        notebook.select(i)
                        text_widget.see("1.0")
                        # Scroll to first match
                        first_match = text_widget.search(search_term_lower, "1.0", tk.END, nocase=True)
                        if first_match:
                            text_widget.see(first_match)
                        break
            
            if not found_any:
                notebook.select(0)  # Go to first tab if nothing found
        
        search_var.trace("w", lambda *args: search_text(search_var.get()))
        
        # Close button
        button_frame = ttk.Frame(main_container)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        close_button = ttk.Button(button_frame, text="Close", command=dialog.destroy)
        close_button.pack(side=tk.RIGHT)
        
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

