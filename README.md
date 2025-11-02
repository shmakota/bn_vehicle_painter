# 🚗 Vehicle Painter for Cataclysm: Bright Nights

<div align="center">

**A powerful, feature-rich tool for designing and customizing vehicles in Cataclysm: Bright Nights**

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()

</div>

---

## 📖 Overview

Vehicle Painter is a comprehensive tkinter-based application designed for creating, editing, and customizing vehicles for the Cataclysm: Bright Nights game. With an intuitive grid-based interface, powerful tools, and full compatibility with the game's JSON format, you can design everything from simple cars to complex multi-tile vehicles.

### ✨ Key Highlights

- 🎨 **Visual Grid-Based Editor** - Intuitive drag-and-drop painting interface
- 🔄 **Full Undo/Redo System** - Never lose your work with 50-level history
- 🎯 **Palette System** - Create and reuse part/item configurations
- 🔍 **Smart Zoom & Pan** - Navigate and work at any scale (50%-400%)
- 🔄 **View Rotation** - View your vehicle from any angle (0°, 90°, 180°, 270°)
- 📁 **JSON Compatible** - Direct import/export to/from Cataclysm: Bright Nights format
- 🛠️ **Advanced Tile Editor** - Fine-tune individual tiles with detailed part/item control

---

## 🚀 Features

### 🎨 Painting & Editing Tools

- **Paint Tool** - Place vehicle parts and items on the grid with click or drag
- **Erase Tool** - Remove parts and items with precision
- **Edit Tile Tool** - Open detailed editor for individual tiles
- **Square Tool** - Fill rectangular areas quickly
- **Square Erase Tool** - Erase rectangular areas efficiently
- **Pan Tool** - Navigate large vehicles easily

### 🎨 Palette System

- **Custom Palette Entries** - Define reusable part/item configurations
- **Character-Based Selection** - Each palette entry uses a unique character
- **Search Functionality** - Quickly find palette entries
- **Auto-Generation** - Generate palettes automatically from loaded vehicles
- **Save/Load Palettes** - Create palette libraries for reuse
- **Multi-Part Support** - Handle complex tiles with multiple parts

### 🖱️ Navigation & View Controls

- **Mouse Wheel Zoom** - Scroll to zoom in/out (50% to 400%)
- **Pan Tool** - Drag to pan the canvas view
- **View Rotation** - Rotate view 90° to see vehicles from different angles
- **Arrow Key Navigation** - Precise grid-aligned scrolling
- **Recenter Button** - Instantly center view on vehicle or origin
- **Zoom Controls** - Dedicated zoom in/out/reset buttons
- **Infinite Scrolling** - Scroll region scales with zoom for unlimited access

### ⌨️ Keyboard Shortcuts

- **Ctrl+Z** - Undo last operation
- **Ctrl+Y** - Redo last undone operation
- **Arrow Keys** - Navigate canvas (grid-aligned movement)
- **Character Keys** - Switch to palette entry (when canvas has focus)
- **Ctrl + Mouse Wheel** - Zoom in/out at cursor position
- **Middle-Click** - Open tile editor (regardless of selected tool)
- **Right-Click** - Erase tile (regardless of selected tool)

### 📁 File Operations

- **New Vehicle** - Create a fresh vehicle from scratch
- **Load Vehicle** - Import vehicles from JSON files
- **Save Vehicle** - Export to Cataclysm: Bright Nights JSON format
- **Load Palette** - Import saved palette configurations
- **Save Palette** - Export palettes for reuse
- **Multi-Vehicle Support** - Load individual vehicles from files containing multiple vehicles

### 🔧 Advanced Features

- **Undo/Redo System** - 50 levels of undo/redo history
- **Drag Operation Grouping** - Entire drag operations become single undo steps
- **Tile Tooltips** - Hover to see detailed part/item information
- **Coordinate Display** - Real-time grid coordinate display
- **Part/Item Counters** - Track vehicle complexity
- **Multi-Part Tile Support** - Handle tiles with multiple parts
- **Item Groups Support** - Support for item groups and individual items
- **Fuel Configuration** - Set fuel types for vehicle parts
- **Chance-Based Items** - Configure item spawn chances

---

## 📦 Installation

### Requirements

- **Python 3.7 or higher**
- **tkinter** (included with most Python installations)

### Quick Start

1. **Clone or download the repository**
   ```bash
   git clone https://github.com/yourusername/bn_vehicle_painter.git
   cd bn_vehicle_painter
   ```

2. **Verify Python installation**
   ```bash
   python3 --version  # Should show 3.7 or higher
   ```

3. **Run the application**
   ```bash
   python3 main.py
   ```
   
   Or use the provided scripts:
   ```bash
   # Linux/Mac
   ./run.sh
   
   # Windows
   run.bat
   ```

### Optional: Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Run application
python3 main.py
```

---

## 📚 Usage Guide

### Getting Started

1. **Launch the Application**
   - Run `python3 main.py` or use the provided script

2. **Load or Create a Vehicle**
   - Click "New Vehicle" to start from scratch
   - Click "Load Vehicle" to import an existing vehicle
   - Loading a vehicle automatically generates a palette

3. **Set Up Your Palette**
   - If loading a vehicle, a palette is auto-generated
   - Click "Load Palette" to use a saved palette
   - Use "Add" to create custom palette entries
   - Double-click entries to edit them

4. **Start Painting**
   - Select a palette character from the list
   - Choose the "Paint" tool
   - Click or drag on the canvas to place parts

### Basic Workflow

```
1. Load/Create Vehicle → 2. Configure Palette → 3. Paint Tiles → 4. Edit Details → 5. Save
```

### Painting Tips

- **Fast Painting**: Use keyboard hotkeys to switch palette entries, then drag to paint
- **Precise Placement**: Use arrow keys for grid-aligned navigation
- **Quick Edits**: Middle-click any tile to open the tile editor
- **Batch Operations**: Use Square tool for filling large areas
- **View Management**: Use Pan tool or mouse wheel + scrollbars to navigate

### Tool Descriptions

| Tool | Description | Usage |
|------|-------------|-------|
| **Paint** | Place parts and items | Click or drag to paint tiles |
| **Erase** | Remove parts/items | Click or drag to erase |
| **Edit Tile** | Detailed tile editor | Click tile to open editor dialog |
| **Square** | Fill rectangles | Click and drag to define area |
| **Square Erase** | Erase rectangles | Click and drag to define area |
| **Pan** | Navigate canvas | Click and drag to pan view |

### Palette Management

**Creating Palette Entries:**
1. Click "Add" in the Palette section
2. Choose a character (or use suggested)
3. Define parts (single or multiple)
4. Optionally add items/item groups
5. Set fuel type if needed
6. Save

**Using Palettes:**
- Click palette entry in list to select
- Type character key when canvas has focus
- Selected entry shows in character preview box

**Editing Entries:**
- Double-click palette entry
- Or select and click "Edit Selected"
- Modify parts, items, fuel, etc.

---

## 🎯 Keyboard Shortcuts Reference

### Navigation
- `↑` `↓` `←` `→` - Scroll view by one grid cell
- `Ctrl + Mouse Wheel` - Zoom in/out
- `Mouse Wheel` - Zoom in/out (when not holding Ctrl)

### Editing
- `Ctrl+Z` - Undo last operation
- `Ctrl+Y` - Redo last undone operation
- `Character Keys` (a-z, A-Z, 0-9, etc.) - Switch to palette entry

### Mouse Actions
- **Left-Click** - Paint/Edit (depends on tool)
- **Left-Drag** - Continuous painting/editing
- **Middle-Click** - Open tile editor (any tool)
- **Right-Click** - Erase tile (any tool)
- **Right-Drag** - Continuous erasing

---

## 📁 File Formats

### Vehicle JSON Format

Vehicles are saved in Cataclysm: Bright Nights compatible JSON format:

```json
{
  "type": "vehicle",
  "id": "custom_vehicle",
  "name": "My Custom Vehicle",
  "parts": [
    {
      "part": "frame",
      "x": 0,
      "y": 0
    },
    {
      "part": "engine",
      "x": 1,
      "y": 0,
      "fuel": "gasoline"
    }
  ],
  "items": [
    {
      "item": "tool_belt",
      "x": 0,
      "y": 0,
      "chance": 100
    }
  ]
}
```

### Palette JSON Format

Palettes can be saved separately for reuse:

```json
{
  "type": "palette",
  "id": "my_palette",
  "vehicle_part": {
    "a": {
      "part": "frame"
    },
    "b": {
      "parts": ["wheel_mount_medium", "wheel"],
      "fuel": "diesel"
    }
  },
  "items": {
    "s": [
      {
        "item": "tool_belt"
      },
      {
        "item_groups": ["tools"]
      }
    ]
  }
}
```

---

## 🏗️ Project Structure

```
bn_vehicle_painter/
├── main.py                      # Main application and UI
├── canvas.py                    # Canvas widget with drawing/editing logic
├── vehicle.py                    # Vehicle data model
├── palette.py                    # Palette management system
├── tile_editor.py               # Tile editor dialog
├── tileset.py                   # Tileset loader (optional)
├── requirements.txt              # Python dependencies
├── README.md                    # This file
├── run.sh                       # Linux/Mac run script
├── run.bat                      # Windows run script
├── palettes/                    # Saved palette files
│   ├── car_palette.json
│   ├── humvee_tow_palette.json
│   └── ...
└── vehicles/                    # Vehicle JSON files
    ├── car.json
    ├── humvee_tow.json
    └── ...
```

### Core Components

- **main.py** - Application entry point, UI setup, event handling
- **canvas.py** - Canvas widget, drawing, zoom, pan, rotation, undo/redo
- **vehicle.py** - Vehicle data model, JSON import/export
- **palette.py** - Palette system, auto-generation, character mapping
- **tile_editor.py** - Detailed tile editing dialog

---

## 🔧 Advanced Features

### Undo/Redo System

- **50 levels of history** - Extensive undo/redo capability
- **Drag grouping** - Entire drag operations are single undo steps
- **Smart state tracking** - Only affected tiles are tracked
- **Automatic cleanup** - History cleared when loading new vehicles

### View Rotation

- Rotate view by 90° increments (0°, 90°, 180°, 270°)
- All tools work correctly in rotated views
- Grid lines and axis markers adapt to rotation
- Vehicle data remains unchanged (rotation is visual only)

### Zoom System

- **Range**: 50% to 400% zoom
- **Smart scrolling**: Scroll region scales with zoom
- **Maintains view center**: Zoom preserves what you're looking at
- **Keyboard shortcuts**: Ctrl+MouseWheel or MouseWheel

### Palette System

- **Auto-generation** - Palettes created automatically from vehicles
- **Multi-part separation** - Option to split multi-part tiles
- **Character assignment** - Automatic character selection (a-z, A-Z, 0-9, symbols)
- **Search functionality** - Filter palette entries in real-time

---

## 🐛 Troubleshooting

### Common Issues

**Problem**: Tiles aren't appearing when painting
- **Solution**: Ensure a palette is loaded and a palette entry is selected

**Problem**: Can't scroll to see all tiles after zooming
- **Solution**: This should be fixed - scroll region now scales with zoom

**Problem**: Keyboard shortcuts not working
- **Solution**: Click the canvas first to give it keyboard focus

**Problem**: Undo/Redo not working
- **Solution**: Operations are only tracked for paint/erase operations, not for tile editor changes

**Problem**: Origin (0,0) not visible
- **Solution**: Click "Recenter" button to center view on vehicle or origin

---

## 🎓 Tips & Best Practices

### Efficient Workflow

1. **Plan First** - Sketch your vehicle layout before building
2. **Use Palettes** - Create reusable palette entries for common configurations
3. **Keyboard Shortcuts** - Learn shortcuts to speed up workflow
4. **Grid Alignment** - Use arrow keys for precise placement
5. **Zoom for Detail** - Zoom in for detailed work, zoom out for overview
6. **Save Frequently** - Use undo/redo, but save your work regularly

### Palette Organization

- **Descriptive Names** - Use clear names for palette entries
- **Group Related** - Organize entries by function
- **Save Templates** - Save common configurations for reuse
- **Search Feature** - Use search to quickly find entries

### Building Vehicles

- **Start with Frame** - Build the base structure first
- **Add Wheels** - Place movement components
- **Add Function** - Install engine, seats, storage
- **Finish Details** - Add decorative/optional parts last

---

## 🙏 Acknowledgments

- Vibe-coded for the **Cataclysm: Bright Nights** community
- Compatible with Cataclysm: Bright Nights vehicle JSON format
- Inspired by the need for better vehicle design tools

---

## 📞 Support

- **Issues**: Report bugs or request features on GitHub Issues
- **Documentation**: See the built-in "Information Atlas" (Help menu) for detailed guides
- **Community**: Join the Cataclysm: Bright Nights community for discussions

---

<div align="center">

**Made with ❤️ for the Cataclysm: Bright Nights community**

[⭐ Star this repo](https://github.com/yourusername/bn_vehicle_painter) if you find it useful!

</div>
