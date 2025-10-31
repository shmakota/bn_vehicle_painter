"""
Tileset loader for vehicle parts graphics.
"""
import json
import os
from PIL import Image, ImageTk


class TilesetLoader:
    """Loads and manages tileset graphics for vehicle parts."""
    
    def __init__(self, gfx_dir="gfx"):
        self.gfx_dir = gfx_dir
        self.tile_config = None
        self.tileset_images = {}  # filename -> PIL Image
        self.tile_cache = {}  # (filename, tile_index) -> ImageTk.PhotoImage
        self.tile_size = 32  # Default tile size
        self.part_to_tile = {}  # part_id -> (filename, tile_index, start_x, start_y)
        self.all_tiles = {}  # tile_id -> (filename, tile_index, start_x, start_y) - ALL tiles, not just vp_
        
        self._load_config()
        self._load_images()
        self._build_part_mapping()
    
    def _load_config(self):
        """Load tile_config.json."""
        config_path = os.path.join(self.gfx_dir, "tile_config.json")
        if not os.path.exists(config_path):
            return
        
        with open(config_path, 'r') as f:
            self.tile_config = json.load(f)
        
        # Get tile size from config
        if 'tile_info' in self.tile_config and len(self.tile_config['tile_info']) > 0:
            tile_info = self.tile_config['tile_info'][0]
            self.tile_size = tile_info.get('width', 32)
    
    def _load_images(self):
        """Load tileset images.
        Loads ALL tileset images that might contain vehicle parts.
        """
        if not self.tile_config:
            return
        
        # Collect all unique filenames that might be needed
        files_to_load = set()
        for file_info in self.tile_config.get('tiles-new', []):
            filename = file_info.get('file')
            if filename:
                files_to_load.add(filename)
        
        # Load all tileset images
        for filename in files_to_load:
            filepath = os.path.join(self.gfx_dir, filename)
            if os.path.exists(filepath):
                try:
                    img = Image.open(filepath)
                    self.tileset_images[filename] = img
                except Exception as e:
                    print(f"Warning: Could not load {filename}: {e}")
    
    def _build_part_mapping(self):
        """Build mapping from part IDs to tile information.
        Loads ALL tiles from ALL tileset files, not just vehicle parts.
        This allows referencing any tile by ID when needed.
        """
        if not self.tile_config:
            return
        
        # Process ALL tileset files
        for file_info in self.tile_config.get('tiles-new', []):
            filename = file_info.get('file')
            if not filename:
                continue
            
            # Check if there's a "sprite_offset" or starting position
            sprite_offset_x = file_info.get('sprite_offset_x', 0)
            sprite_offset_y = file_info.get('sprite_offset_y', 0)
            sprite_width = file_info.get('sprite_width', self.tile_size)
            sprite_height = file_info.get('sprite_height', self.tile_size)
            
            # Calculate starting tile position in image
            start_tile_x = sprite_offset_x // self.tile_size if sprite_offset_x else 0
            start_tile_y = sprite_offset_y // self.tile_size if sprite_offset_y else 0
            
            # Use sequential array index - tiles in JSON array should match image layout
            # fg values are not sequential (some have lower values than earlier tiles)
            # so we rely on array order matching the image layout
            tiles = file_info.get('tiles', [])
            valid_tile_index = 0  # Sequential position in image (left-to-right, top-to-bottom)
            
            for tile_info in tiles:
                if not isinstance(tile_info, dict):
                    continue
                
                tile_id = tile_info.get('id', '')
                if isinstance(tile_id, list) or not isinstance(tile_id, str):
                    continue
                
                # Store using sequential array index
                self.all_tiles[tile_id] = (filename, valid_tile_index, start_tile_x, start_tile_y)
                
                if tile_id.startswith('vp_'):
                    part_name = tile_id[3:]
                    self.part_to_tile[part_name] = (filename, valid_tile_index, start_tile_x, start_tile_y)
                
                valid_tile_index += 1
    
    def _tile_index_to_coords(self, tile_index, tiles_per_row):
        """Convert tile index to image coordinates."""
        row = tile_index // tiles_per_row
        col = tile_index % tiles_per_row
        x = col * self.tile_size
        y = row * self.tile_size
        return x, y
    
    def get_tile_image(self, part_name, target_size=None):
        """Get the tile image for a part name.
        First checks part_to_tile (vehicle parts without vp_ prefix),
        then checks all_tiles with vp_ prefix, then checks all_tiles directly.
        Also tries partial matches for cases like 'airship_balloon' -> 'balloon'
        
        Args:
            part_name: The name of the vehicle part (e.g., 'board', 'frame') or full tile ID
            target_size: Optional target size (width, height) to resize to
        
        Returns:
            ImageTk.PhotoImage or None if not found
        """
        # First try: direct part name lookup (for vehicle parts)
        if part_name in self.part_to_tile:
            tile_info = self.part_to_tile[part_name]
        # Second try: with vp_ prefix
        elif f"vp_{part_name}" in self.all_tiles:
            tile_info = self.all_tiles[f"vp_{part_name}"]
        # Third try: exact tile ID match
        elif part_name in self.all_tiles:
            tile_info = self.all_tiles[part_name]
        # Fourth try: partial match - ONLY for specific known cases
        # Only use partial matching for very specific cases like 'balloon' where we know it's safe
        # Don't use it for generic words like 'frame' which could match wrong tiles
        else:
            # Very limited partial matching - only for known safe cases
            # Try to find matching tiles by searching for key words, but be conservative
            parts = part_name.split('_')
            tile_info = None
            
            # Only try partial matching for specific keywords that we know are safe
            # e.g., 'balloon' is safe because it's not ambiguous
            safe_partial_words = ['balloon']  # Add more safe words here if needed
            
            # Strategy 1: Try each individual word ONLY if it's a safe word
            for word in parts:
                if word in safe_partial_words and word in self.all_tiles:
                    tile_info = self.all_tiles[word]
                    break
            
            if tile_info is None:
                return None  # No partial matching for other cases - be strict
        
        if len(tile_info) == 4:
            filename, tile_index, start_x, start_y = tile_info
        else:
            # Backward compatibility
            filename, tile_index = tile_info
            start_x, start_y = 0, 0
        
        # Check cache (include target_size in cache key if provided)
        cache_key = (filename, tile_index, start_x, start_y, target_size)
        if cache_key in self.tile_cache:
            return self.tile_cache[cache_key]
        
        # Load from image
        if filename not in self.tileset_images:
            return None
        
        img = self.tileset_images[filename]
        tiles_per_row = img.width // self.tile_size
        
        # Calculate tile position considering starting offset
        tile_row = tile_index // tiles_per_row
        tile_col = tile_index % tiles_per_row
        
        # Add starting offset
        final_row = tile_row + start_y
        final_col = tile_col + start_x
        
        x = final_col * self.tile_size
        y = final_row * self.tile_size
        
        # Extract tile
        tile_img = img.crop((x, y, x + self.tile_size, y + self.tile_size))
        
        # Resize if target size specified
        if target_size:
            # Ensure target_size is a tuple of integers (PIL requires integers)
            if isinstance(target_size, (tuple, list)) and len(target_size) >= 2:
                target_size = (int(target_size[0]), int(target_size[1]))
            tile_img = tile_img.resize(target_size, Image.Resampling.LANCZOS)
        
        # Convert to PhotoImage for Tkinter
        photo = ImageTk.PhotoImage(tile_img)
        
        # Cache it
        self.tile_cache[cache_key] = photo
        
        return photo
    
    def get_tile_for_part(self, part_dict):
        """Get tile image for a part dictionary.
        
        Args:
            part_dict: Part dictionary with 'part' key
        
        Returns:
            ImageTk.PhotoImage or None
        """
        part_name = part_dict.get('part')
        if not part_name:
            return None
        
        return self.get_tile_image(part_name)

