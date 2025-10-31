"""
Palette loader for vehicle painting.
"""

import json
import copy


class Palette:
    """Loads and manages vehicle painting palettes."""
    
    def __init__(self):
        self.vehicle_part = {}  # Character -> part definition
        self.items = {}  # Character -> item/itemgroup definition
        self.palette_id = None
        self.palette_type = None
    
    @classmethod
    def load_from_file(cls, filename):
        """Load palette from JSON file."""
        with open(filename, 'r') as f:
            data = json.load(f)
        
        palette = cls()
        palette.palette_type = data.get('type')
        palette.palette_id = data.get('id')
        palette.vehicle_part = data.get('vehicle_part', {})
        palette.items = data.get('items', {})
        
        return palette
    
    def get_part_definition(self, character):
        """Get the part definition for a character."""
        return self.vehicle_part.get(character)
    
    def get_item_definition(self, character):
        """Get the item definition for a character."""
        return self.items.get(character)
    
    def create_parts_from_char(self, character, x, y):
        """Create vehicle parts from a palette character at given coordinates."""
        part_def = self.get_part_definition(character)
        if part_def is None:
            return []
        
        parts = []
        
        if isinstance(part_def, str):
            # Simple part string
            part = {'x': x, 'y': y, 'part': part_def}
            parts.append(part)
        elif isinstance(part_def, dict):
            # Complex part definition
            if 'parts' in part_def:
                # Multiple parts
                for part_name in part_def['parts']:
                    part = {'x': x, 'y': y, 'part': part_name}
                    if 'fuel' in part_def:
                        part['fuel'] = part_def['fuel']
                    parts.append(part)
            elif 'part' in part_def:
                # Single part with properties
                part = {'x': x, 'y': y, 'part': part_def['part']}
                if 'fuel' in part_def:
                    part['fuel'] = part_def['fuel']
                parts.append(part)
        
        return parts
    
    def create_items_from_char(self, character, x, y):
        """Create items from a palette character at given coordinates."""
        item_def = self.get_item_definition(character)
        if item_def is None:
            return []
        
        # item_def can be a list of items or a single item
        if isinstance(item_def, list):
            # Multiple items with chances
            items = []
            for item_entry in item_def:
                item = {'x': x, 'y': y}
                if 'item' in item_entry:
                    item['item'] = item_entry['item']
                if 'item_groups' in item_entry:
                    item['item_groups'] = item_entry['item_groups']
                if 'chance' in item_entry:
                    item['chance'] = item_entry['chance']
                items.append(item)
            return items
        else:
            # Single item definition
            item = {'x': x, 'y': y}
            if 'item' in item_def:
                item['item'] = item_def['item']
            if 'item_groups' in item_def:
                item['item_groups'] = item_def['item_groups']
            if 'chance' in item_def:
                item['chance'] = item_def['chance']
            return [item]
    
    def get_available_characters(self):
        """Get all available palette characters."""
        chars = set(self.vehicle_part.keys())
        chars.update(self.items.keys())
        return sorted(chars)
    
    @classmethod
    def generate_from_vehicle(cls, vehicle, palette_id="auto_generated", separate_parts=False):
        """Generate a palette from an existing vehicle by analyzing its parts.
        
        Args:
            vehicle: Vehicle object to generate palette from
            palette_id: ID for the generated palette
            separate_parts: If True, separate multi-part tiles into individual parts.
                          If False, keep multi-part tiles as combined entries.
        """
        palette = cls()
        palette.palette_type = "vehicle_palette"
        palette.palette_id = palette_id
        
        # Collect unique part configurations
        part_configs = {}  # (part_name, fuel?) -> char
        char_counter = ord('A')  # Start with 'A'
        
        # Analyze parts
        for part in vehicle.parts:
            part_name = part.get('part')
            fuel = part.get('fuel')
            
            if 'parts' in part:
                # Multiple parts - extract part names from the list
                # Handle both string and dict formats
                parts_names = []
                for p in part['parts']:
                    if isinstance(p, str):
                        parts_names.append(p)
                    elif isinstance(p, dict):
                        # Extract part name from dict
                        if 'part' in p:
                            parts_names.append(p['part'])
                        elif 'parts' in p:
                            # Nested parts list - flatten it
                            for nested_p in p['parts']:
                                if isinstance(nested_p, str):
                                    parts_names.append(nested_p)
                                elif isinstance(nested_p, dict) and 'part' in nested_p:
                                    parts_names.append(nested_p['part'])
                
                if not parts_names:
                    # Skip if we couldn't extract any part names
                    continue
                
                if separate_parts:
                    # Separate each part into its own palette entry
                    for single_part_name in parts_names:
                        part_key = (single_part_name,)
                        if fuel:
                            part_key = part_key + (f"fuel:{fuel}",)
                        
                        if part_key not in part_configs:
                            # Assign a character
                            if char_counter > ord('Z'):
                                if char_counter > ord('z'):
                                    char_num = char_counter - ord('z') - 1
                                    if char_num < 10:
                                        char = chr(ord('0') + char_num)
                                    else:
                                        char = chr(ord('!') + (char_num - 10))
                                else:
                                    char = chr(char_counter)
                            else:
                                char = chr(char_counter)
                            
                            part_configs[part_key] = char
                            char_counter += 1
                            
                            # Create palette entry for single part
                            fuel_value = next((k.split(':')[1] for k in part_key if 'fuel:' in str(k)), None)
                            if fuel_value:
                                palette.vehicle_part[char] = {'part': single_part_name, 'fuel': fuel_value}
                            else:
                                palette.vehicle_part[char] = single_part_name
                else:
                    # Keep multiple parts together (original behavior)
                    parts_list = sorted(parts_names)
                    part_key = tuple(parts_list)
                    if fuel:
                        part_key = part_key + (f"fuel:{fuel}",)
                    
                    if part_key not in part_configs:
                        # Assign a character
                        if char_counter > ord('Z'):
                            if char_counter > ord('z'):
                                char_num = char_counter - ord('z') - 1
                                if char_num < 10:
                                    char = chr(ord('0') + char_num)
                                else:
                                    char = chr(ord('!') + (char_num - 10))
                            else:
                                char = chr(char_counter)
                        else:
                            char = chr(char_counter)
                        
                        part_configs[part_key] = char
                        char_counter += 1
                        
                        # Create palette entry
                        has_fuel = any('fuel:' in str(k) for k in part_key)
                        parts_list_clean = [p for p in part_key if not str(p).startswith('fuel:')]
                        fuel_value = next((k.split(':')[1] for k in part_key if 'fuel:' in str(k)), None)
                        
                        if len(parts_list_clean) == 1:
                            # Single part
                            if fuel_value:
                                palette.vehicle_part[char] = {'part': parts_list_clean[0], 'fuel': fuel_value}
                            else:
                                palette.vehicle_part[char] = parts_list_clean[0]
                        else:
                            # Multiple parts
                            palette.vehicle_part[char] = {'parts': parts_list_clean}
                            if fuel_value:
                                palette.vehicle_part[char]['fuel'] = fuel_value
            elif part_name:
                # Single part
                part_key = (part_name,)
                if fuel:
                    part_key = part_key + (f"fuel:{fuel}",)
                
                if part_key not in part_configs:
                    # Assign a character
                    if char_counter > ord('Z'):
                        if char_counter > ord('z'):
                            char_num = char_counter - ord('z') - 1
                            if char_num < 10:
                                char = chr(ord('0') + char_num)
                            else:
                                char = chr(ord('!') + (char_num - 10))
                        else:
                            char = chr(char_counter)
                    else:
                        char = chr(char_counter)
                    
                    part_configs[part_key] = char
                    char_counter += 1
                    
                    # Create palette entry
                    fuel_value = next((k.split(':')[1] for k in part_key if 'fuel:' in str(k)), None)
                    if fuel_value:
                        palette.vehicle_part[char] = {'part': part_name, 'fuel': fuel_value}
                    else:
                        palette.vehicle_part[char] = part_name
            else:
                continue
        
        # Analyze items (simpler - group by item/item_groups)
        item_configs = {}
        item_char_counter = ord('1')  # Start with '1' for items
        
        for item in vehicle.items:
            item_key = None
            if 'item' in item:
                item_key = ('item', item['item'])
            elif 'item_groups' in item:
                item_key = ('groups', tuple(sorted(item['item_groups'])))
            
            if item_key and item_key not in item_configs:
                # Assign character
                char = chr(item_char_counter)
                item_configs[item_key] = char
                item_char_counter += 1
                
                # Create palette entry
                if item_key[0] == 'item':
                    palette.items[char] = [{'item': item_key[1]}]
                else:
                    palette.items[char] = [{'item_groups': list(item_key[1])}]
                
                # Add chance if present
                if 'chance' in item:
                    palette.items[char][0]['chance'] = item['chance']
        
        return palette
    
    def save_to_file(self, filename):
        """Save palette to JSON file."""
        import json
        data = {
            'type': self.palette_type,
            'id': self.palette_id,
            'vehicle_part': self.vehicle_part,
            'items': self.items
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)

