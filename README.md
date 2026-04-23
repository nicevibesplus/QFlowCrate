<img src="./images/icon.svg" align="right" width="100" />

# QFlowCrate

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![QGIS >= 3.24](https://img.shields.io/badge/QGIS-%3E%3D3.24-green)](https://qgis.org)
[![Latest Release](https://img.shields.io/github/v/release/nicevibesplus/QFlowCrate)](https://github.com/nicevibesplus/QFlowCrate/releases/download/v0.0.7/qflowcrate-v0.0.7.zip)

A QGIS plugin that retrieves the steps of a spatial analysis workflow and bundles everything into a **RO‑Crate** – a self‑describing, machine‑readable package that contains data, metadata, and provenance information. It helps with making QGIS projects reproducible, shareable, and ready for FAIR publishing.
<br clear="right"/>

---

## Table of Contents  

- [What is QFlowCrate?](#what-is-qflowcrate)  
- [Features](#features)  
- [Installation and Quick start](#installation)  
- [Development](#development)  
- [License & Acknowledgements](#license--acknowledgements)  
- [Contact & Support](#contact--support)   

---

## What is QFlowCrate?

Geospatial analyses in QGIS involve many steps:
1. Loading data layers from several different sources.  
2. Applying geoprocessing operations (vector analysis, raster algebra, interpolation, etc.).  
3. Styling layers, creating legends, and designing print layouts. 

These actions are rarely documented in a structured, reusable way, which hampers **reproducibility**, **transparency**, and **long‑term preservation** of research results.  

QFlowCrate solves this problem by assisting the user to **capture the provenance** of the executed workflows in a QGIS project and exporting it as a **[RO‑Crate]((https://www.researchobject.org/ro-crate/))** – a community‑adopted standard for packaging research data and metadata. The resulting crate can be deposited in data repositories, shared with collaborators, or used as supplementary material for publications, thereby aligning geospatial workflows with FAIR principles.

More specifically, QFlowCrate will track down the file paths, URLs, coordinate reference systems, and symbology of **data layers** in the project. 
Additionally, it will track the **processing steps** that were applied to the data layer, including the name of the process, units of measurement and other parameters. Moreover, 
QFlowCrate will help you document the **metadata** of your project, prompting to fill in the project title, description, and author details.


![Animated show case](./images/showcase.gif)

> This project is based on the work of Andreas Rademaker for his Bachelor's thesis in Geoinformatics at the University of Münster
> (Institute for Geoinformatics), October 2025.

---

## Features  

| Functionality | Feature | 
|---------|------------------|
| **Provenance capture** | Data layers, coordinate systems, processing steps, symbology. |
| **RO‑Crate export** | Generates a standards‑compliant crate ready for FAIR sharing. All local data files are bundled in the exported ZIP. |
| **Selective packaging** | Choose which layers/files to include (e.g., omit large raw rasters). |
| **Custom metadata entry** | UI helps the user fill in title, description, and author details. |
| **Cross‑platform** | Works on Windows, macOS, and Linux Ubuntu (QGIS ≥ 3.40). |
| **Data‑format support** | <br>• **Vector:** Shapefile (`.shp`), GeoJSON (`.geojson`), KML (`.kml`) <br>• **Raster:** GeoTIFF (`.tif/.tiff`), PNG (`.png`), JPEG (`.jpg`) <br>• **Other:** CSV tables, OGC-compliant server connections (WFS, WMS) |
| **RO‑Crate import** | Imports a RO-Crate ZIP for visualization and inspection. Workflow re-execution is currently not supported. |

---

## Installation

### 1️⃣ Download the latest release  

Go to the **[Releases](https://github.com/nicevibesplus/QFlowCrate/releases)** page and download the ZIP file for the most recent version (Currently [qflowcrate‑v0.0.7.zip](https://github.com/nicevibesplus/QFlowCrate/releases/download/v0.0.7/qflowcrate-v0.0.7.zip)).

### 2️⃣ Install the plugin in QGIS  

1. Open QGIS.  
1. From the main menu choose **Plugins → Manage and Install Plugins → Install from ZIP**.
1. Browse your files and select the downloaded `qflowcrate‑vX.Y.Z.zip`.  
1. Click **Install Plugin**.  

### 3️⃣ Verify the installation  

- After the installation, a new **QFlowCrate** toolbar button (a small crate icon) should appear.  
- Open the **Plugins → Plugin Manager** and confirm that **QFlowCrate** is listed and enabled.  


---

## Quick start  

Below is a minimal, end‑to‑end example that demonstrates the typical workflow.

### Step 1 – Prepare a QGIS project. 

1. Suppose we load a locally stored shapefile containing point data.
2. We apply a simple operation, e.g., extract by attribute, and save the output of the operation as a temporary layer.

### Step 2 – Open the plugin 

1. Click the **QFlowCrate** toolbar button.  
2. You can read the instructions, if you feel like.
2. Navigate to the Graph tab.

### Step 3 – Add the data layers  

1. Click **Add Layer** and select the local shapefile from the list. Select the temporary layer, too.
1. Fill in the layer metadata for each layer.
1. The added data layers are displayed as blue
rectangles.

### Step 4 – Add the processing steps 

1. Click **Add Processing Step** and select the 'extractbyattribute' operation from the list.
1. Fill in the processing step metadata, as prompted.
2. The processing step is now visualised in the graph as a green ellipse.  


### Step 5 – Draw the connections 

1. Click the **Connection Mode** button.  
2. Click first on the source node (e.g., the shapefile rectangle) and then on the destination node (e.g., the 'extract by attribute' operation). You should now have an arrow that connects the shapefile and the processing operation.
2. Repeat as necessary, until all data flows are properly illustrated in the Graph.

### Step 6 – Export the RO‑Crate  

1. Navigate to the Export tab.
1. Choose a destination folder (e.g., `~/Documents/QFlowCrate_Exports/ProjectA`).  
2. Fill in the metadata fields (title, description, author details).  
3. Click **Export RO-Crate**.  

The plugin creates a folder structure similar to:

```
ProjectA/
├─ ro-crate-metadata.json
├─ shapefile_layer1/
│  ├─ geometry.zip
│  └─ symbology.qml
└─ temporary_layer2/
   ├─ geometry.geojson
   └─ symbology.qml
```

### Step 7 – Import a RO‑Crate  

1. Navigate to the Import tab.
1. Browse an already exported RO-Crate zip file.
1. Visualize the graph and inspect the graph elements for details. 

---


## Development  

### Prerequisites  

| Tool | Minimum version |
|------|-----------------|
| **QGIS** | 3.40+ |
| **Python** | 3.10+ (the version bundled with QGIS) |
| **uv** (fast Python package manager) | latest (<https://github.com/astral-sh/uv>) |
| **git** | any recent version |

### Setting up a development environment  


#### 1️⃣ Clone the repository (fork first if you intend to contribute)
```bash
git clone https://github.com/nicevibesplus/QFlowCrate.git
cd QFlowCrate
```

#### 2️⃣ Create a virtual environment with uv
```bash
uv sync # creates .venv and installs everything
```

#### 3️⃣ Activate the environment
```bash
# Linux/macOS/Git Bash
source .venv/bin/activate
```
or
```bash
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

### Creating a release  

A helper script bundles only the production files (including the `rocrate` dependency) into a ZIP and creates a Github release.

```bash
# Make the script executable (Linux/macOS)
chmod +x scripts/create_release.sh

# Create a new release – replace vX.Y.Z with your version tag
scripts/create_release.sh v0.1.0
```
or in Windows

```powershell
scripts\create_release.sh v0.1.0
```
---

## License & Acknowledgements 

- **License:** GNU GPL v3 – see the [LICENSE](LICENSE) file.  
- Based on the work conducted for the following thesis: 
  - **Title:** *Enhancing Map Reproducibility: Developing a QGIS Plugin for Automated Documentation of Data Provenance and Workflow*  
  - **Author:** Andreas Rademaker ([@nicevibesplus](https://github.com/nicevibesplus))  
  - **Degree:** B.Sc. Geoinformatics, University of Münster, Institute for Geoinformatics (October 2025)  
  - **Supervisors:** Eftychia Koukouraki, Brian Ochieng Pondi  

## Contact & Support  

Please use the **Github issue tracker:** <https://github.com/nicevibesplus/QFlowCrate/issues> 
