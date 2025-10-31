"""
Tile editor dialog for editing vehicle parts and items on a specific tile.
"""

import tkinter as tk
from tkinter import ttk, messagebox


class TileEditorDialog:
    """Dialog for editing all parts and items on a specific tile."""
    
    def __init__(self, parent, vehicle, x, y, canvas_update_callback=None, palette=None):
        self.parent = parent
        self.vehicle = vehicle
        self.x = x
        self.y = y
        self.canvas_update_callback = canvas_update_callback
        self.palette = palette
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Edit Tile ({x}, {y})")
        self.dialog.geometry("650x600")
        self.dialog.transient(parent)
        
        # Don't grab yet - wait until window is viewable
        self.dialog.deiconify()
        self.dialog.lift()
        self.dialog.focus_force()
        
        self.part_indices = []
        self.item_indices = []
        
        self.setup_ui()
        self.load_tile_data()
        
        # Now that UI is set up, ensure window is visible and then grab
        self.dialog.update_idletasks()
        try:
            self.dialog.grab_set()
        except tk.TclError:
            # If grab fails, continue anyway - dialog will still work
            pass
    
    def setup_ui(self):
        """Set up the dialog UI."""
        # Main container
        container = ttk.Frame(self.dialog)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Coordinate label
        coord_label = ttk.Label(container, text=f"Editing tile at coordinates: ({self.x}, {self.y})", 
                               font=("TkDefaultFont", 10, "bold"))
        coord_label.pack(pady=(0, 10))
        
        # Parts section
        parts_frame = ttk.LabelFrame(container, text="Vehicle Parts", padding="10")
        parts_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Parts listbox frame
        parts_list_frame = ttk.Frame(parts_frame)
        parts_list_frame.pack(fill=tk.BOTH, expand=True)
        
        parts_scrollbar = ttk.Scrollbar(parts_list_frame, orient=tk.VERTICAL)
        parts_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.parts_listbox = tk.Listbox(parts_list_frame, yscrollcommand=parts_scrollbar.set, height=8)
        self.parts_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        parts_scrollbar.config(command=self.parts_listbox.yview)
        
        # Parts buttons
        parts_btn_frame = ttk.Frame(parts_frame)
        parts_btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(parts_btn_frame, text="Remove Selected", command=self.remove_selected_part).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(parts_btn_frame, text="Edit Fuel", command=self.edit_fuel).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(parts_btn_frame, text="Add Part", command=self.add_part).pack(side=tk.LEFT)
        
        # Items section
        items_frame = ttk.LabelFrame(container, text="Items / Item Groups", padding="10")
        items_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Items listbox frame
        items_list_frame = ttk.Frame(items_frame)
        items_list_frame.pack(fill=tk.BOTH, expand=True)
        
        items_scrollbar = ttk.Scrollbar(items_list_frame, orient=tk.VERTICAL)
        items_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.items_listbox = tk.Listbox(items_list_frame, yscrollcommand=items_scrollbar.set, height=8)
        self.items_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        items_scrollbar.config(command=self.items_listbox.yview)
        
        # Items buttons
        items_btn_frame = ttk.Frame(items_frame)
        items_btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(items_btn_frame, text="Remove Selected", command=self.remove_selected_item).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(items_btn_frame, text="Edit Item", command=self.edit_item).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(items_btn_frame, text="Add Item", command=self.add_item).pack(side=tk.LEFT)
        
        # Close button
        ttk.Button(container, text="Close", command=self.dialog.destroy).pack(pady=(10, 0))
    
    def load_tile_data(self):
        """Load parts and items for this tile."""
        # Clear and reload parts
        self.parts_listbox.delete(0, tk.END)
        self.part_indices = []
        
        for i, part in enumerate(self.vehicle.parts):
            if part.get('x') == self.x and part.get('y') == self.y:
                part_str = self.format_part(part)
                self.parts_listbox.insert(tk.END, part_str)
                self.part_indices.append(i)
        
        if not self.part_indices:
            self.parts_listbox.insert(tk.END, "(No parts at this tile)")
            self.parts_listbox.config(state=tk.DISABLED)
        else:
            self.parts_listbox.config(state=tk.NORMAL)
        
        # Clear and reload items
        self.items_listbox.delete(0, tk.END)
        self.item_indices = []
        
        for i, item in enumerate(self.vehicle.items):
            if item.get('x') == self.x and item.get('y') == self.y:
                item_str = self.format_item(item)
                self.items_listbox.insert(tk.END, item_str)
                self.item_indices.append(i)
        
        if not self.item_indices:
            self.items_listbox.insert(tk.END, "(No items at this tile)")
            self.items_listbox.config(state=tk.DISABLED)
        else:
            self.items_listbox.config(state=tk.NORMAL)
    
    def format_part(self, part):
        """Format a part for display."""
        if 'parts' in part:
            parts_str = ", ".join(part['parts'])
            result = f"Parts: {parts_str}"
        elif 'part' in part:
            result = f"Part: {part['part']}"
        else:
            result = "Part: (unknown)"
        
        if 'fuel' in part:
            result += f" | Fuel: {part['fuel']}"
        
        return result
    
    def format_item(self, item):
        """Format an item for display."""
        result = ""
        if 'item' in item:
            result += f"Item: {item['item']}"
        if 'item_groups' in item:
            if result:
                result += " | "
            groups_str = ", ".join(item['item_groups'])
            result += f"Groups: {groups_str}"
        if 'chance' in item:
            if result:
                result += " | "
            result += f"Chance: {item['chance']}%"
        
        return result or "Item: (empty)"
    
    def remove_selected_part(self):
        """Remove the selected part."""
        selection = self.parts_listbox.curselection()
        if not selection or len(self.part_indices) == 0:
            messagebox.showwarning("No Selection", "Please select a part to remove.")
            return
        
        idx = selection[0]
        if idx < len(self.part_indices):
            part_index = self.part_indices[idx]
            # Remove from vehicle (need to find current index since list changes)
            actual_parts = self.vehicle.get_parts_at(self.x, self.y)
            if idx < len(actual_parts):
                # Find the actual index in vehicle.parts
                target_part = actual_parts[idx]
                for i, p in enumerate(self.vehicle.parts):
                    if p is target_part:
                        self.vehicle.remove_part(i)
                        break
            
            self.load_tile_data()
            if self.canvas_update_callback:
                self.canvas_update_callback()
    
    def remove_selected_item(self):
        """Remove the selected item."""
        selection = self.items_listbox.curselection()
        if not selection or len(self.item_indices) == 0:
            messagebox.showwarning("No Selection", "Please select an item to remove.")
            return
        
        idx = selection[0]
        if idx < len(self.item_indices):
            # Find actual item index
            actual_items = self.vehicle.get_items_at(self.x, self.y)
            if idx < len(actual_items):
                target_item = actual_items[idx]
                for i, itm in enumerate(self.vehicle.items):
                    if itm is target_item:
                        self.vehicle.remove_item(i)
                        break
            
            self.load_tile_data()
            if self.canvas_update_callback:
                self.canvas_update_callback()
    
    def edit_fuel(self):
        """Edit fuel for the selected part."""
        selection = self.parts_listbox.curselection()
        if not selection or len(self.part_indices) == 0:
            messagebox.showwarning("No Selection", "Please select a part to edit fuel.")
            return
        
        idx = selection[0]
        actual_parts = self.vehicle.get_parts_at(self.x, self.y)
        if idx >= len(actual_parts):
            return
        
        part = actual_parts[idx]
        
        # Create dialog for fuel input
        fuel_dialog = tk.Toplevel(self.dialog)
        fuel_dialog.title("Edit Fuel")
        fuel_dialog.transient(self.dialog)
        
        ttk.Label(fuel_dialog, text="Fuel Type:").pack(pady=10, padx=10)
        
        fuel_var = tk.StringVar(value=part.get('fuel', ''))
        fuel_entry = ttk.Entry(fuel_dialog, textvariable=fuel_var, width=30)
        fuel_entry.pack(pady=5, padx=10)
        
        # Grab after UI is set up
        fuel_dialog.update_idletasks()
        try:
            fuel_dialog.grab_set()
        except tk.TclError:
            pass
        
        def save_fuel():
            fuel = fuel_var.get().strip()
            if fuel:
                part['fuel'] = fuel
            elif 'fuel' in part:
                del part['fuel']
            
            fuel_dialog.destroy()
            self.load_tile_data()
            if self.canvas_update_callback:
                self.canvas_update_callback()
        
        ttk.Button(fuel_dialog, text="Save", command=save_fuel).pack(pady=10)
    
    def add_part(self):
        """Add a new part to this tile."""
        part_dialog = tk.Toplevel(self.dialog)
        part_dialog.title("Add Part")
        part_dialog.transient(self.dialog)
        part_dialog.geometry("400x400")
        
        main_frame = ttk.Frame(part_dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Palette character selection (if palette available)
        use_palette = tk.BooleanVar(value=self.palette is not None)
        char_var = None
        
        if self.palette:
            palette_frame = ttk.LabelFrame(main_frame, text="From Palette", padding="10")
            palette_frame.pack(fill=tk.X, pady=(0, 10))
            
            ttk.Checkbutton(
                palette_frame,
                text="Use palette character",
                variable=use_palette
            ).pack(anchor=tk.W)
            
            char_frame = ttk.Frame(palette_frame)
            char_frame.pack(fill=tk.X, pady=(5, 0))
            
            ttk.Label(char_frame, text="Character:").pack(side=tk.LEFT, padx=(0, 5))
            char_var = tk.StringVar()
            char_entry = ttk.Entry(char_frame, textvariable=char_var, width=5)
            char_entry.pack(side=tk.LEFT, padx=(0, 5))
            
            char_preview = tk.Label(
                char_frame,
                text="",
                width=3,
                relief=tk.RAISED,
                borderwidth=1,
                font=("Courier", 10, "bold")
            )
            char_preview.pack(side=tk.LEFT)
            
            # List available characters
            chars_label = ttk.Label(palette_frame, text="Available characters:")
            chars_label.pack(anchor=tk.W, pady=(5, 0))
            
            chars_listbox = tk.Listbox(palette_frame, height=4)
            chars_listbox.pack(fill=tk.X, pady=(5, 0))
            for char in self.palette.get_available_characters():
                part_def = self.palette.get_part_definition(char)
                if part_def:
                    chars_listbox.insert(tk.END, char)
            
            def on_char_select(event):
                selection = chars_listbox.curselection()
                if selection:
                    char = chars_listbox.get(selection[0])
                    char_var.set(char)
                    char_preview.config(text=char)
            
            chars_listbox.bind('<<ListboxSelect>>', on_char_select)
            
            def on_char_entry_change(*args):
                char = char_var.get().strip()
                if len(char) == 1:
                    char_preview.config(text=char)
                else:
                    char_preview.config(text="")
            
            char_var.trace('w', on_char_entry_change)
        
        # Manual entry
        manual_frame = ttk.LabelFrame(main_frame, text="Manual Entry", padding="10")
        manual_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(manual_frame, text="Part Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        part_var = tk.StringVar()
        part_entry = ttk.Entry(manual_frame, textvariable=part_var, width=30)
        part_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        
        fuel_frame = ttk.Frame(manual_frame)
        fuel_frame.grid(row=1, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Label(fuel_frame, text="Fuel (optional):").pack(side=tk.LEFT, padx=(0, 5))
        fuel_var = tk.StringVar()
        fuel_entry = ttk.Entry(fuel_frame, textvariable=fuel_var, width=20)
        fuel_entry.pack(side=tk.LEFT)
        
        # Multiple parts option
        multi_frame = ttk.Frame(manual_frame)
        multi_frame.grid(row=2, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E))
        
        use_multiple = tk.BooleanVar()
        ttk.Checkbutton(
            multi_frame,
            text="Multiple parts (comma-separated)",
            variable=use_multiple
        ).pack(side=tk.LEFT)
        
        manual_frame.columnconfigure(1, weight=1)
        
        def save_part():
            if use_palette.get() and self.palette and char_var:
                # Use palette
                char = char_var.get().strip()
                if not char or len(char) != 1:
                    messagebox.showwarning("Invalid Input", "Please enter a palette character.")
                    return
                
                parts = self.palette.create_parts_from_char(char, self.x, self.y)
                if not parts:
                    messagebox.showwarning("Invalid Character", f"No part definition found for '{char}'.")
                    return
                
                for part in parts:
                    self.vehicle.add_part(part)
            else:
                # Manual entry
                part_name = part_var.get().strip()
                if not part_name:
                    messagebox.showwarning("Invalid Input", "Part name cannot be empty.")
                    return
                
                if use_multiple.get():
                    # Multiple parts
                    part_names = [p.strip() for p in part_name.split(',')]
                    part = {'x': self.x, 'y': self.y, 'parts': part_names}
                else:
                    # Single part
                    part = {'x': self.x, 'y': self.y, 'part': part_name}
                
                fuel = fuel_var.get().strip()
                if fuel:
                    part['fuel'] = fuel
                
                self.vehicle.add_part(part)
            
            part_dialog.destroy()
            self.load_tile_data()
            if self.canvas_update_callback:
                self.canvas_update_callback()
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=(10, 0))
        ttk.Button(button_frame, text="Add", command=save_part).pack()
        
        # Grab after UI is set up
        part_dialog.update_idletasks()
        try:
            part_dialog.grab_set()
        except tk.TclError:
            pass
    
    def edit_item(self):
        """Edit the selected item."""
        selection = self.items_listbox.curselection()
        if not selection or len(self.item_indices) == 0:
            messagebox.showwarning("No Selection", "Please select an item to edit.")
            return
        
        idx = selection[0]
        actual_items = self.vehicle.get_items_at(self.x, self.y)
        if idx >= len(actual_items):
            return
        
        item = actual_items[idx]
        
        item_dialog = tk.Toplevel(self.dialog)
        item_dialog.title("Edit Item")
        item_dialog.transient(self.dialog)
        
        main_frame = ttk.Frame(item_dialog, padding="10")
        main_frame.pack()
        
        # Item name
        ttk.Label(main_frame, text="Item:").grid(row=0, column=0, sticky=tk.W, pady=5)
        item_var = tk.StringVar(value=item.get('item', ''))
        ttk.Entry(main_frame, textvariable=item_var, width=30).grid(row=0, column=1, pady=5)
        
        # Item groups
        ttk.Label(main_frame, text="Item Groups (comma-separated):").grid(row=1, column=0, sticky=tk.W, pady=5)
        groups_var = tk.StringVar(value=", ".join(item.get('item_groups', [])))
        ttk.Entry(main_frame, textvariable=groups_var, width=30).grid(row=1, column=1, pady=5)
        
        # Chance
        ttk.Label(main_frame, text="Chance (%):").grid(row=2, column=0, sticky=tk.W, pady=5)
        chance_var = tk.StringVar(value=str(item.get('chance', '')))
        ttk.Entry(main_frame, textvariable=chance_var, width=30).grid(row=2, column=1, pady=5)
        
        def save_item():
            # Update item
            item_name = item_var.get().strip()
            if item_name:
                item['item'] = item_name
            elif 'item' in item:
                del item['item']
            
            groups = groups_var.get().strip()
            if groups:
                item['item_groups'] = [g.strip() for g in groups.split(',')]
            elif 'item_groups' in item:
                del item['item_groups']
            
            chance_str = chance_var.get().strip()
            if chance_str:
                try:
                    item['chance'] = int(chance_str)
                except ValueError:
                    messagebox.showerror("Invalid Input", "Chance must be a number.")
                    return
            elif 'chance' in item:
                del item['chance']
            
            item_dialog.destroy()
            self.load_tile_data()
            if self.canvas_update_callback:
                self.canvas_update_callback()
        
        ttk.Button(main_frame, text="Save", command=save_item).grid(row=3, column=0, columnspan=2, pady=10)
        
        # Grab after UI is set up
        item_dialog.update_idletasks()
        try:
            item_dialog.grab_set()
        except tk.TclError:
            pass
    
    def add_item(self):
        """Add a new item to this tile."""
        item_dialog = tk.Toplevel(self.dialog)
        item_dialog.title("Add Item")
        item_dialog.transient(self.dialog)
        item_dialog.geometry("400x350")
        
        main_frame = ttk.Frame(item_dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Palette character selection (if palette available)
        use_palette = tk.BooleanVar(value=False)
        char_var = None
        
        if self.palette:
            palette_frame = ttk.LabelFrame(main_frame, text="From Palette", padding="10")
            palette_frame.pack(fill=tk.X, pady=(0, 10))
            
            ttk.Checkbutton(
                palette_frame,
                text="Use palette character",
                variable=use_palette
            ).pack(anchor=tk.W)
            
            char_frame = ttk.Frame(palette_frame)
            char_frame.pack(fill=tk.X, pady=(5, 0))
            
            ttk.Label(char_frame, text="Character:").pack(side=tk.LEFT, padx=(0, 5))
            char_var = tk.StringVar()
            char_entry = ttk.Entry(char_frame, textvariable=char_var, width=5)
            char_entry.pack(side=tk.LEFT, padx=(0, 5))
            
            char_preview = tk.Label(
                char_frame,
                text="",
                width=3,
                relief=tk.RAISED,
                borderwidth=1,
                font=("Courier", 10, "bold")
            )
            char_preview.pack(side=tk.LEFT)
            
            # List available characters with items
            chars_label = ttk.Label(palette_frame, text="Available characters:")
            chars_label.pack(anchor=tk.W, pady=(5, 0))
            
            chars_listbox = tk.Listbox(palette_frame, height=3)
            chars_listbox.pack(fill=tk.X, pady=(5, 0))
            for char in self.palette.get_available_characters():
                item_def = self.palette.get_item_definition(char)
                if item_def:
                    chars_listbox.insert(tk.END, char)
            
            def on_char_select(event):
                selection = chars_listbox.curselection()
                if selection:
                    char = chars_listbox.get(selection[0])
                    char_var.set(char)
                    char_preview.config(text=char)
            
            chars_listbox.bind('<<ListboxSelect>>', on_char_select)
            
            def on_char_entry_change(*args):
                char = char_var.get().strip()
                if len(char) == 1:
                    char_preview.config(text=char)
                else:
                    char_preview.config(text="")
            
            char_var.trace('w', on_char_entry_change)
        
        # Manual entry
        manual_frame = ttk.LabelFrame(main_frame, text="Manual Entry", padding="10")
        manual_frame.pack(fill=tk.BOTH, expand=True)
        
        # Item name
        ttk.Label(manual_frame, text="Item:").grid(row=0, column=0, sticky=tk.W, pady=5)
        item_var = tk.StringVar()
        ttk.Entry(manual_frame, textvariable=item_var, width=30).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Item groups
        ttk.Label(manual_frame, text="Item Groups (comma-separated):").grid(row=1, column=0, sticky=tk.W, pady=5)
        groups_var = tk.StringVar()
        ttk.Entry(manual_frame, textvariable=groups_var, width=30).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Chance
        ttk.Label(manual_frame, text="Chance (%):").grid(row=2, column=0, sticky=tk.W, pady=5)
        chance_var = tk.StringVar()
        ttk.Entry(manual_frame, textvariable=chance_var, width=30).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)
        
        manual_frame.columnconfigure(1, weight=1)
        
        def save_item():
            if use_palette.get() and self.palette and char_var:
                # Use palette
                char = char_var.get().strip()
                if not char or len(char) != 1:
                    messagebox.showwarning("Invalid Input", "Please enter a palette character.")
                    return
                
                items = self.palette.create_items_from_char(char, self.x, self.y)
                if not items:
                    messagebox.showwarning("Invalid Character", f"No item definition found for '{char}'.")
                    return
                
                for item in items:
                    self.vehicle.add_item(item)
            else:
                # Manual entry
                item_name = item_var.get().strip()
                groups = groups_var.get().strip()
                chance_str = chance_var.get().strip()
                
                if not item_name and not groups:
                    messagebox.showwarning("Invalid Input", "Please provide either an item or item groups.")
                    return
                
                item = {'x': self.x, 'y': self.y}
                
                if item_name:
                    item['item'] = item_name
                
                if groups:
                    item['item_groups'] = [g.strip() for g in groups.split(',')]
                
                if chance_str:
                    try:
                        item['chance'] = int(chance_str)
                    except ValueError:
                        messagebox.showerror("Invalid Input", "Chance must be a number.")
                        return
                
                self.vehicle.add_item(item)
            
            item_dialog.destroy()
            self.load_tile_data()
            if self.canvas_update_callback:
                self.canvas_update_callback()
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=(10, 0))
        ttk.Button(button_frame, text="Add", command=save_item).pack()
        
        # Grab after UI is set up
        item_dialog.update_idletasks()
        try:
            item_dialog.grab_set()
        except tk.TclError:
            pass
