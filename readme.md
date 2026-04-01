
# VelovStats - Vélo'v Statistics Viewer

## Project Overview

VelovStats is a Python-based project for analyzing and visualizing Vélo'v bike-sharing system statistics.

## Project Structure

```
velov_stat_viewer/
├── data/            # Data files
└── README.md        # This file
```

## Prerequisites

- Python 3.8+
- pip (Python package manager)

## Installation

```bash
pip install requests
```

## Running Python Scripts

### Script 1: Data Collection
```bash
python data/getData.py
```
Fetches and collects Vélo'v station data.

### Script 2: Data visualization generation
```bash
python generate_station_html.py data/small_sample.csv -o sample_station_report.html
```

Run scripts in sequence:
1. Collect data
3. Generate visualizations


