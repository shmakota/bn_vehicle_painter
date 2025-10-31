"""
Vehicle data model for Cataclysm: Bright Nights.
"""
import json
import copy


class Vehicle:
    """Represents a vehicle with parts and properties."""
    
    def __init__(self, name="Custom Vehicle", vehicle_id=None):
        self.id = vehicle_id or name.lower().replace(" ", "_")
        self.type = "vehicle"
        self.name = name
        self.parts = []  # List of vehicle parts
        self.items = []  # List of items/item groups
        self.blueprint = []  # Optional blueprint representation
    
    def add_part(self, part):
        """Add a vehicle part."""
        # Ensure part has required fields
        if 'x' not in part or 'y' not in part:
            raise ValueError("Part must have 'x' and 'y' coordinates")
        
        # Make a copy to avoid reference issues
        new_part = copy.deepcopy(part)
        self.parts.append(new_part)
    
    def remove_part(self, part_index):
        """Remove a part by index."""
        if 0 <= part_index < len(self.parts):
            del self.parts[part_index]
    
    def get_parts_at(self, x, y):
        """Get all parts at the given coordinates."""
        return [p for p in self.parts if p.get('x') == x and p.get('y') == y]
    
    def has_parts_at(self, x, y):
        """Check if there are any parts at the given coordinates."""
        return len(self.get_parts_at(x, y)) > 0
    
    def get_items_at(self, x, y):
        """Get all items at the given coordinates."""
        return [item for item in self.items if item.get('x') == x and item.get('y') == y]
    
    def has_items_at(self, x, y):
        """Check if there are any items at the given coordinates."""
        return len(self.get_items_at(x, y)) > 0
    
    def add_item(self, item):
        """Add an item or item group."""
        if 'x' not in item or 'y' not in item:
            raise ValueError("Item must have 'x' and 'y' coordinates")
        new_item = copy.deepcopy(item)
        self.items.append(new_item)
    
    def remove_item(self, item_index):
        """Remove an item by index."""
        if 0 <= item_index < len(self.items):
            del self.items[item_index]
    
    def get_bounds(self):
        """Get the bounding box of the vehicle."""
        if not self.parts:
            return (0, 0, 0, 0)
        
        xs = [p['x'] for p in self.parts if 'x' in p]
        ys = [p['y'] for p in self.parts if 'y' in p]
        
        if not xs or not ys:
            return (0, 0, 0, 0)
        
        return (min(xs), min(ys), max(xs), max(ys))
    
    def generate_blueprint(self):
        """Generate a simple blueprint showing the vehicle outline."""
        if not self.parts:
            return []
        
        bounds = self.get_bounds()
        if bounds == (0, 0, 0, 0):
            return []
        
        min_x, min_y, max_x, max_y = bounds
        width = max_x - min_x + 1
        height = max_y - min_y + 1
        
        # Create a grid marking which tiles have parts
        grid = {}
        for part in self.parts:
            if 'x' in part and 'y' in part:
                x = part['x'] - min_x
                y = part['y'] - min_y
                grid[(x, y)] = True
        
        # Generate blueprint rows
        blueprint = []
        for y in range(height):
            row = []
            line = ""
            for x in range(width):
                if (x, y) in grid:
                    line += "#"  # Simple character to show part exists
                else:
                    line += " "  # Empty space
            row.append(line)
            blueprint.append(row)
        
        return blueprint
    
    def to_dict(self):
        """Convert vehicle to dictionary (C:BN format)."""
        result = {
            'id': self.id,
            'type': self.type,
            'name': self.name,
            'parts': self.parts
        }
        if self.items:
            result['items'] = self.items
        
        # Generate blueprint if it doesn't exist or if we want to regenerate
        # Only include if we have parts
        # Blueprint comes AFTER parts in the JSON
        if self.parts:
            # Use existing blueprint if it's manually set and non-empty, otherwise generate
            if not self.blueprint:
                self.blueprint = self.generate_blueprint()
            if self.blueprint:
                result['blueprint'] = self.blueprint
        
        # Add comment for exported vehicles
        result['//'] = 'exported with vehicle painter'
        
        return result
    
    def normalize_coordinates(self):
        """Normalize coordinates to start from (0, 0) or center on grid."""
        if not self.parts and not self.items:
            return
        
        # Get all coordinates
        all_x = []
        all_y = []
        
        for part in self.parts:
            if 'x' in part:
                all_x.append(part['x'])
            if 'y' in part:
                all_y.append(part['y'])
        
        for item in self.items:
            if 'x' in item:
                all_x.append(item['x'])
            if 'y' in item:
                all_y.append(item['y'])
        
        if not all_x or not all_y:
            return
        
        # Find minimum coordinates
        min_x = min(all_x)
        min_y = min(all_y)
        
        # Shift all coordinates to start from (0, 0)
        for part in self.parts:
            if 'x' in part:
                part['x'] -= min_x
            if 'y' in part:
                part['y'] -= min_y
        
        for item in self.items:
            if 'x' in item:
                item['x'] -= min_x
            if 'y' in item:
                item['y'] -= min_y
    
    @classmethod
    def from_dict(cls, data):
        """Create a vehicle from a dictionary (C:BN format)."""
        vehicle = cls(
            name=data.get('name', 'Custom Vehicle'),
            vehicle_id=data.get('id')
        )
        vehicle.parts = data.get('parts', [])
        vehicle.items = data.get('items', [])
        vehicle.blueprint = data.get('blueprint', [])
        # Don't preserve comment from loaded files - it will be added on export
        # Normalize coordinates to align with grid
        vehicle.normalize_coordinates()
        return vehicle
    
    def to_json(self):
        """Export vehicle as JSON string with proper formatting matching bus.json style."""
        data = self.to_dict()
        
        # Build JSON manually to match bus.json formatting style
        lines = ['{']
        
        # Required fields first
        lines.append(f'    "id": {json.dumps(data["id"])},')
        lines.append(f'    "type": {json.dumps(data["type"])},')
        lines.append(f'    "name": {json.dumps(data["name"])},')
        
        # Parts - single line format like bus.json
        lines.append('    "parts": [')
        for i, part in enumerate(data['parts']):
            comma = ',' if i < len(data['parts']) - 1 else ''
            # Format as single line to match bus.json
            part_str = json.dumps(part, separators=(', ', ': '))
            lines.append(f'      {part_str}{comma}')
        lines.append('    ]')
        
        # Items (if any) - single line format
        if 'items' in data and data['items']:
            lines.append(',')
            lines.append('    "items": [')
            for i, item in enumerate(data['items']):
                comma = ',' if i < len(data['items']) - 1 else ''
                item_str = json.dumps(item, separators=(', ', ': '))
                lines.append(f'      {item_str}{comma}')
            lines.append('    ]')
        
        # Blueprint comes AFTER parts/items
        if 'blueprint' in data and data['blueprint']:
            lines.append(',')
            lines.append('    "blueprint": [')
            for i, row in enumerate(data['blueprint']):
                comma = ',' if i < len(data['blueprint']) - 1 else ''
                lines.append(f'      {json.dumps(row)}{comma}')
            lines.append('    ]')
        
        # Comment at the end (JSON5 style)
        if '//' in data:
            lines.append(',')
            lines.append(f'    "//": {json.dumps(data["//"])}')
        
        lines.append('}')
        
        return '\n'.join(lines)
    
    def save_to_file(self, filename):
        """Save vehicle to JSON file."""
        with open(filename, 'w') as f:
            f.write(self.to_json())
    
    @classmethod
    def from_json(cls, json_string):
        """Create a vehicle from JSON string."""
        data = json.loads(json_string)
        return cls.from_dict(data)
    
    @classmethod
    def load_from_file(cls, filename):
        """Load vehicle from JSON file."""
        with open(filename, 'r') as f:
            return cls.from_json(f.read())

