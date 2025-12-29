# Control Panel

(c) 2024 ControlPanelProductions Ltd.  
dachboden.berlin

## Overview

Control Panel is a comprehensive tool developed by Dachboden for managing and interacting with ArtNet and DMX devices, featuring a rich Pygame-based GUI and extensive MicroPython device support. It integrates hardware control with a flexible software interface, allowing for complex device orchestration and scripting.

## Features

-   **Interactive GUI**: A robust Pygame-based interface with support for shaders, fullscreen mode, and dynamic resolution.
-   **Hardware Control**: Built-in support for ArtNet and DMX Universes to control lighting and stage equipment.
-   **Scripting Engine**: Support for running custom Python scripts (`userscripts`) to automate tasks or create custom behaviors.
-   **Web Server**: Integrated FastAPI server (`--start-server`) for remote interaction and script management.
-   **MicroPython Tools**: Specialized tools for developing, flashing, and managing ESP32-based devices.
-   **Developer Friendly**: Includes custom flake8 plugins and typing stubs generation.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd control-panel
    ```

2.  **Install the package:**
    It is recommended to use a virtual environment.
    ```bash
    pip install .
    # For development (editable mode) with dev dependencies
    pip install -e .[dev]
    ```

## Usage

### Main Application

Run the control panel using the `controlpanel` command:

```bash
controlpanel [OPTIONS]
```

**Common Options:**

-   `--no-gui`: Run in headless mode without the GUI.
-   `-f`, `--fullscreen`: Start the application in fullscreen mode.
-   `--width`, `--height`: Set custom window dimensions (default: 960x540).
-   `--start-server`: Start the integrated web server on port 8000.
-   `--load-scripts`: Load specific scripts from the `userscripts` directory.
-   `--shaders`: Enable shader support.

**Example:**
```bash
controlpanel --fullscreen --start-server --shaders
```

### Developer Tools

The project includes several CLI tools for hardware development:

#### Firmware Flashing (`flash_firmware`)
Flash MicroPython firmware to an ESP32 device.

```bash
flash_firmware -p <PORT> [--firmware <PATH_TO_FIRMWARE>]
```

#### File Transfer (`transfer`)
Transfer files to a MicroPython device via WebREPL.

```bash
transfer <HOSTNAME> [PATH] [OPTIONS]
```
-   `--IP`: Override IP address resolution.
-   `-p`: WebREPL password.
-   `-f`: Force transfer (ignore checksums).
-   `--transfer-files-only`: Skip directory structure creation.

#### Stub Generation (`generate_stubs`)
Generate type stubs for better IDE support.

```bash
generate_stubs
```

## Project Structure

-   `controlpanel/`: Main package source code.
    -   `api/`: Core API logic.
    -   `game_manager/`: Pygame GUI logic.
    -   `server/`: FastAPI web server.
    -   `upy/`: MicroPython source code for devices.
    -   `shared/`: Shared resources and manifests.
-   `dev_tools/`: Helper scripts for flashing and file transfer.
-   `userscripts/`: Directory for user-defined scripts.
-   `templates/`, `static/`: Web server assets.

## License

(c) 2024 ControlPanelProductions Ltd. All rights reserved.
