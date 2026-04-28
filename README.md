# Sustainability GIS Analysis – Espoo and Helsinki Region

This repository contains a Python-based GIS analysis using OpenStreetMap data for the Helsinki metropolitan region. The project focuses on mapping buildings, roads, administrative boundaries, and calculating building density as a sustainability indicator.

## Project description

Sustainability GIS analysis in Espoo and the Helsinki region, evaluating land use, transport access, green spaces, and environmental factors. The study identifies sustainable planning opportunities to improve urban resilience, reduce emissions, and enhance quality of life.

## Study areas

- **Espoo postal code area:** 02150, Espoo, Finland
- **Helsinki city districts:** Helsinki, Finland
- **Projected CRS:** EPSG:3067 (Euref-FIN), suitable for accurate area and distance calculations in Finland

## Repository structure

```text
sustainability-gis-espoo-helsinki/
├── README.md
├── requirements.txt
├── environment.yml
├── .gitignore
├── LICENSE
├── src/
│   ├── espoo_postal_area_map.py
│   └── helsinki_building_density.py
├── notebooks/
│   └── geospatial_analysis.ipynb
├── outputs/
│   └── maps/
└── data/
```

## Main analyses

### 1. Espoo postal-code GIS map

The script `src/espoo_postal_area_map.py`:

- downloads the postal-code boundary for `02150, Espoo, Finland`
- downloads building footprints from OpenStreetMap
- downloads the drivable road network
- reprojects all layers to EPSG:3067
- clips buildings and roads to the postal-code boundary
- creates a map showing buildings, roads, and the postal boundary
- calculates building density for the postal-code area

### 2. Helsinki district building density

The script `src/helsinki_building_density.py`:

- downloads the Helsinki city boundary
- downloads administrative district boundaries
- downloads building footprints
- reprojects data to EPSG:3067
- calculates building density by district
- creates a choropleth map of building density
- exports density results as CSV

## Installation

Create and activate a virtual environment, then install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

Alternatively, using conda:

```bash
conda env create -f environment.yml
conda activate sustainability-gis
```

## Usage

Run the Espoo postal-code map workflow:

```bash
python src/espoo_postal_area_map.py
```

Run the Helsinki district density workflow:

```bash
python src/helsinki_building_density.py
```

Generated maps and CSV files are saved in `outputs/maps/` and `outputs/`.

## Outputs

Expected outputs include:

- `outputs/maps/espoo_02150_map.png`
- `outputs/maps/helsinki_building_density.png`
- `outputs/helsinki_district_building_density.csv`

## Notes

The scripts download live OpenStreetMap data using OSMnx. Results may vary slightly over time as OpenStreetMap is updated.

## License

This project is released under the MIT License.
