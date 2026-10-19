# SwissBioPics MCP Server

**Version 0.1.0**

> ⚠️ **Disclaimer**: This is an **unofficial, third-party implementation** and is not officially maintained by or affiliated with the SIB Swiss Institute of Bioinformatics or the SwissBioPics team. This project is independently developed. All SwissBioPics images and data are copyrighted by SIB.

An [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) server that provides AI assistants with access to [SwissBioPics](https://www.swissbiopics.org/) — a freely available library of interactive biological images for visualizing subcellular location data.

---

## Table of Contents

- [Overview](#overview)
- [About SwissBioPics](#about-swissbiopics)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
  - [Claude for Desktop](#claude-for-desktop)
  - [Cursor](#cursor)
  - [VS Code (Copilot Chat)](#vs-code-copilot-chat)
  - [Generic MCP Client](#generic-mcp-client)
- [Available Tools](#available-tools)
- [Usage Examples](#usage-examples)
- [Query Syntax](#query-syntax)
- [Project Structure](#project-structure)
- [Development](#development)
- [License & Citation](#license--citation)
- [Acknowledgements](#acknowledgements)

---

## Overview

[SwissBioPics](https://www.swissbiopics.org/) is a resource developed by the Swiss-Prot group at the SIB Swiss Institute of Bioinformatics. It provides an interactive library of cell images covering all kingdoms of life — from animal cells (muscle, neuron, epithelial, etc.) to fungal cells, plant cells, archaeal cells, and various bacterial morphologies (rod-shaped, coccus, spiral, etc.).

This MCP server exposes SwissBioPics data and functionality through a set of tools that AI assistants like Claude, ChatGPT, and others can discover and invoke. This enables conversational querying of subcellular location data, cell-type imagery, and biological descriptions.

> **中文文档**: [README_zh.md](./README_zh.md)

---

## About SwissBioPics

SwissBioPics is a freely available library of interactive biological images for visualizing subcellular location data. It includes cell types from all kingdoms of life.

- **Website**: https://www.swissbiopics.org/
- **License**: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
- **Citation**: SwissBioPics - an interactive library of cell images for the visualization of subcellular location data. PMID: [35411389](https://pubmed.ncbi.nlm.nih.gov/35411389/), DOI: [10.1093/database/baac026](https://doi.org/10.1093/database/baac026)
- **NPM Package**: [@swissprot/swissbiopics-visualizer](https://www.npmjs.com/package/@swissprot/swissbiopics-visualizer)
- **Developed by**: Swiss-Prot group, SIB Swiss Institute of Bioinformatics

---

## Features

This MCP server provides the following capabilities:

1. **🔍 Search** — Search for subcellular locations and cell types using advanced query syntax (AND, OR, NOT, wildcards, fuzzy search, exact phrases).
2. **💡 Auto-complete** — Get search suggestions as users type.
3. **📋 Cell Type Listing** — List all available cell types from the SwissBioPics homepage.
4. **🔬 Cell Type Details** — Retrieve metadata for a specific cell type by ID or name.
5. **🖼️ SVG Retrieval** — Fetch the raw SVG illustration of a cell type.
6. **📍 Location Extraction** — Extract all subcellular locations (SL IDs, names, descriptions) from a cell type's SVG.
7. **📖 Location Details** — Look up the detailed description of a specific subcellular location by its SL identifier.
8. **ℹ️ Project Info** — Get general information about the SwissBioPics project.

---

## Prerequisites

- **Python 3.10+** (3.10, 3.11, 3.12, 3.13 all supported)
- **[uv](https://docs.astral.sh/uv/)** — Fast Python package manager (recommended) or `pip`
- An MCP-compatible client (e.g., Claude for Desktop, Cursor, VS Code with Copilot Chat, or any other MCP client)

---

## Installation

### Option A: Using `uv` (recommended)

```bash
# Clone the repository
git clone https://github.com/ZengZichao/SwissBioPics-MCP.git
cd SwissBioPics-MCP

# Install dependencies with uv
uv sync
```

### Option B: Using `pip`

```bash
git clone https://github.com/ZengZichao/SwissBioPics-MCP.git
cd SwissBioPics-MCP

# Create a virtual environment
python -m venv .venv

# Activate it
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install in development mode
pip install -e .
```

---

## Configuration

### Claude for Desktop

Edit your Claude configuration file:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Add the server entry:

```json
{
  "mcpServers": {
    "swissbiopics": {
      "command": "uv",
      "args": [
        "--directory",
        "/ABSOLUTE/PATH/TO/SwissBioPics-MCP",
        "run",
        "swissbiopics-mcp"
      ]
    }
  }
}
```

> **Windows**: Use double backslashes (`\\`) or forward slashes (`/`) in the JSON path. Replace `/ABSOLUTE/PATH/TO/` with your actual path, e.g., `C:/Users/YourName/Projects/SwissBioPics-MCP`.

If you installed via `pip` instead of `uv`, use:

```json
{
  "mcpServers": {
    "swissbiopics": {
      "command": "python",
      "args": ["-m", "swissbiopics_mcp.server"],
      "cwd": "/ABSOLUTE/PATH/TO/SwissBioPics-MCP"
    }
  }
}
```

After saving, restart Claude for Desktop.

### Cursor

Add to your Cursor MCP settings (`Settings → MCP`):

```json
{
  "mcpServers": {
    "swissbiopics": {
      "command": "uv",
      "args": [
        "--directory",
        "/ABSOLUTE/PATH/TO/SwissBioPics-MCP",
        "run",
        "swissbiopics-mcp"
      ]
    }
  }
}
```

### VS Code (Copilot Chat)

Add to `.vscode/mcp.json` in your workspace or user settings:

```json
{
  "servers": {
    "swissbiopics": {
      "command": "uv",
      "args": [
        "--directory",
        "/ABSOLUTE/PATH/TO/SwissBioPics-MCP",
        "run",
        "swissbiopics-mcp"
      ]
    }
  }
}
```

### Generic MCP Client

The server runs on the **stdio** transport and can be launched by any MCP-compatible client:

```bash
# If installed via uv
uv run swissbiopics-mcp

# If installed via pip
python -m swissbiopics_mcp.server

# Direct execution
python src/swissbiopics_mcp/server.py
```

---

## Available Tools

| Tool | Description |
|------|-------------|
| `search_locations` | Search for subcellular locations and cell types using advanced query syntax. |
| `get_search_suggestions` | Get auto-complete suggestions for a partial search query. |
| `get_cell_types` | List all available cell types on SwissBioPics. |
| `get_cell_type_detail` | Get details (title, SVG file, URLs) for a specific cell type by ID or name. |
| `get_cell_svg` | Retrieve the raw SVG image content of a cell type. |
| `get_subcellular_locations` | Extract all subcellular locations (SL IDs, names, descriptions) from a cell type's SVG. |
| `get_location_detail` | Get the detailed description of a specific subcellular location by its SL ID. |
| `get_swissbiopics_info` | Get general information about the SwissBioPics project. |

---

## Usage Examples

Here are example prompts you can use with your AI assistant after configuring the server:

### Search for locations

> *"Search SwissBioPics for mitochondrion"*

> *"Search for cell types that contain both 'endosome' and 'lysosome'"*

### List cell types

> *"What cell types are available on SwissBioPics?"*

### Get cell type details

> *"Get details for cell type 8719"*

> *"Show me the Animal cell on SwissBioPics"*

### Retrieve SVG

> *"Get the SVG image for the Animal cell"*

### Explore subcellular locations

> *"List all subcellular locations in the Animal cell"*

> *"What are the subcellular locations in a Plant cell?"*

### Look up a specific location

> *"What is SL0173 in SwissBioPics?"*

> *"Get the description of SL-0243 (Secreted) in the Animal cell"*

### Get project info

> *"Tell me about the SwissBioPics project"*

---

## Query Syntax

The `search_locations` tool supports the following query syntax:

| Syntax | Meaning | Example |
|--------|---------|---------|
| `term1 term2` | AND — both terms must be present | `spindle body` |
| `term1 AND term2` | Explicit AND | `spindle AND body` |
| `term1 OR term2` | Either term | `SL-0073 OR chromatophore` |
| `"exact phrase"` | Exact phrase match | `"golgi stack"` |
| `term1 -term2` | NOT — exclude term2 | `endosome -peroxisome` |
| `term1 NOT term2` | Explicit NOT | `endosome NOT peroxisome` |
| `prefix*` | Wildcard prefix | `bact*` |
| `term~` | Fuzzy search (≈2 typos) | `rhoptri~` (finds "rhoptry") |
| `(…)` | Grouping / precedence | `lumen AND (SL0158 OR wall)` |

---

## Project Structure

```
SwissBioPics-MCP/
├── pyproject.toml                 # Project metadata & dependencies
├── README.md                      # English documentation (this file)
├── README_zh.md                   # Chinese documentation
├── LICENSE                        # MIT license
├── .gitignore                     # Git ignore rules
├── src/
│   └── swissbiopics_mcp/
│       ├── __init__.py            # Package metadata
│       └── server.py              # MCP server implementation
└── tests/
    ├── conftest.py                # Pytest configuration
    ├── test_parsers.py            # Unit tests for parsing functions
    └── test_tools.py              # Unit tests for MCP tool functions
```

---

## Development

### Setup

```bash
# Clone and install in development mode
git clone https://github.com/ZengZichao/SwissBioPics-MCP.git
cd SwissBioPics-MCP
uv sync
```

### Run the server directly

```bash
uv run swissbiopics-mcp
```

### Debug with MCP Inspector

```bash
# Using uv
uv run mcp dev src/swissbiopics_mcp/server.py

# Or using npx
npx @modelcontextprotocol/inspector uv run swissbiopics-mcp
```

### Run tests

```bash
uv run pytest
```

---

## License & Citation

### License

This MCP server code is licensed under the **MIT License** — see [LICENSE](./LICENSE).

The SwissBioPics images and data are licensed under [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/). When using SwissBioPics images or data, please credit SwissBioPics as the source.

### Citation

If you use SwissBioPics in your research, please cite:

> SwissBioPics - an interactive library of cell images for the visualization of subcellular location data. *Database*. PMID: [35411389](https://pubmed.ncbi.nlm.nih.gov/35411389/), DOI: [10.1093/database/baac026](https://doi.org/10.1093/database/baac026).

---

## Acknowledgements

- **SwissBioPics** is developed by Philippe Le Mercier (content, images), Jerven Bolleman (software: API/web-component), and Edouard de Castro (software: editor/website+js) at the [Swiss-Prot group](https://www.sib.swiss/alan-bridge-group), [SIB Swiss Institute of Bioinformatics](https://www.sib.swiss).
- Supported by the Swiss Federal Government through the [State Secretariat for Education, Research and Innovation (SERI)](https://www.sbfi.admin.ch/sbfi/en/home/seri/seri.html).
- This MCP server is an independent project and is not officially affiliated with SIB.
