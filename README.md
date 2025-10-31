# Vehicle Painter for Cataclysm: Bright Nights

A tkinter-based tool for painting and customizing vehicles in Cataclysm: Bright Nights.

## Features

- **Grid-based Painting**: Paint vehicles on a grid canvas
- **Color Selection**: Choose custom colors for vehicle parts
- **Multiple Tools**: Paint, Erase, and Select tools
- **Vehicle Management**: Create, load, and save vehicles
- **JSON Export**: Export vehicles in JSON format compatible with C:BN

## Installation

1. Ensure Python 3.7+ is installed
2. No additional packages required (tkinter comes with Python)

```bash
# Optional: Create a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

## Usage

Run the application:

```bash
python3 main.py
```

### Interface

- **Left Panel**: Contains color picker, tools, vehicle info, and file operations
- **Canvas**: Main painting area where you can draw your vehicle
- **Status Bar**: Shows current status and feedback

### Tools

- **Paint**: Click and drag to paint vehicle parts
- **Erase**: Remove parts from the vehicle
- **Select**: Select parts (coming soon)

## Project Structure

```
bn_vehicle_painter/
├── main.py          # Main application entry point
├── canvas.py        # Custom canvas widget for vehicle painting
├── vehicle.py       # Vehicle data model
├── requirements.txt # Project dependencies
└── README.md        # This file
```

## Future Enhancements

- Load/save vehicle definitions compatible with C:BN format
- Vehicle part types (frames, engines, wheels, etc.)
- Advanced selection and manipulation tools
- Undo/redo functionality
- Zoom controls
- Vehicle preview in different orientations

## License

MIT License

