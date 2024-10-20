# QOI Viewer

A simple QOI image viewer built with PySide6.

## Features

- Drag and drop QOI images for viewing.
- Zoom in and out using the mouse wheel.
- Toggle image size locking to resize the window without affecting the image.
- Reset zoom level to 1:1.
- Toggle always-on-top behavior.
- Navigate through multiple QOI images in the same directory using arrow keys.
- Move the image within the window using the mouse while holding the 'M' key.
- Optional frameless window mode.

## Requirements

- Python 3.6 or higher
- PySide6

## Usage

1. Install the required dependencies.
2. Run the script: `python main.py [options] [qoi_path]`

### Options

- `--notitle`: Run the viewer in frameless window mode.
- `qoi_path`: Path to a QOI image file to open on startup.

### Keyboard Shortcuts

- `Q` or `Esc`: Close the viewer.
- `L`: Toggle image size locking.
- `R`: Reset zoom level.
- `T`: Toggle always-on-top.
- `Left Arrow`: Open the previous QOI image in the directory.
- `Right Arrow`: Open the next QOI image in the directory.
- `M`: Toggle image moving mode.

## Examples

- Open a QOI image: `python main.py image.qoi`
- Run the viewer in frameless mode: `python main.py --notitle`
- Open an image and run in frameless mode: `python main.py --notitle image.qoi`

## Notes

- When image size is locked, resizing the window will not affect the image size.
- In image moving mode, click and drag the image to reposition it within the window.

## Disclaimer

This project is a work in progress and I am still learning. Any fixes or better alternatives on how to implement features are welcome in the form of issues or pull requests. 
