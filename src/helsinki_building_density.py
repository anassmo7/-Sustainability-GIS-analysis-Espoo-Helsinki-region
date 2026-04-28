"""Calculate building density for Helsinki districts using OpenStreetMap data."""

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import osmnx as ox
import pandas as pd


QUERY = "Helsinki, Finland"
CRS_FIN = "EPSG:3067"
OUTPUT_DIR = Path("outputs")
MAP_DIR = OUTPUT_DIR / "maps"
OUTPUT_CSV = OUTPUT_DIR / "helsinki_district_building_density.csv"
OUTPUT_MAP = MAP_DIR / "helsinki_building_density.png"


def configure_osmnx() -> None:
    """Configure OSMnx cache, logging, and timeout settings."""
    ox.settings.use_cache = True
    ox.settings.log_console = False
    ox.settings.timeout = 180


def download_helsinki_data() -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """Download Helsinki boundary, district boundaries, and buildings."""
    helsinki = ox.geocode_to_gdf(QUERY)
    helsinki_polygon = helsinki.geometry.iloc[0]

    district_tags = {"boundary": "administrative", "admin_level": "10"}
    districts_all = ox.features_from_polygon(helsinki_polygon, tags=district_tags)

    if isinstance(districts_all.index, pd.MultiIndex):
        districts = districts_all.loc["relation"].copy()
    elif "element_type" in districts_all.columns:
        districts = districts_all[districts_all["element_type"] == "relation"].copy()
    else:
        districts = districts_all.copy()

    districts = districts[districts.geometry.type.isin(["Polygon", "MultiPolygon"])].copy()

    buildings_all = ox.features_from_polygon(helsinki_polygon, tags={"building": True})
    buildings = buildings_all[buildings_all.geometry.type.isin(["Polygon", "MultiPolygon"])].copy()
    buildings = buildings[buildings.geometry.notna()].copy()

    return helsinki, districts, buildings


def prepare_layers(
    helsinki: gpd.GeoDataFrame,
    districts: gpd.GeoDataFrame,
    buildings: gpd.GeoDataFrame,
) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """Reproject layers, repair geometries, and remove unrealistic districts."""
    helsinki = helsinki.to_crs(CRS_FIN)
    districts = districts.to_crs(CRS_FIN)
    buildings = buildings.to_crs(CRS_FIN)

    districts["geometry"] = districts.geometry.buffer(0)
    buildings["geometry"] = buildings.geometry.buffer(0)

    helsinki_area = float(helsinki.geometry.iloc[0].area)
    districts["district_area_m2"] = districts.geometry.area
    districts = districts[districts["district_area_m2"] <= helsinki_area * 1.05].copy()

    return helsinki, districts, buildings


def calculate_density(districts: gpd.GeoDataFrame, buildings: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Calculate building density for each district."""
    districts = districts.copy()
    buildings = buildings.copy()
    districts["building_density_pct"] = 0.0

    for idx, district in districts.iterrows():
        district_gdf = gpd.GeoDataFrame(district.to_frame().T, crs=CRS_FIN)
        district_geometry = district_gdf.geometry.iloc[0]

        buildings_in_district = gpd.sjoin(
            buildings,
            district_gdf[["geometry"]],
            how="inner",
            predicate="intersects",
        )

        if len(buildings_in_district) > 0:
            buildings_in_district = buildings_in_district.copy()
            buildings_in_district["geometry"] = buildings_in_district.geometry.intersection(district_geometry)
            buildings_in_district = buildings_in_district[
                buildings_in_district.geometry.notna() & ~buildings_in_district.is_empty
            ]
            total_building_area = buildings_in_district.geometry.area.sum()
        else:
            total_building_area = 0.0

        district_area = float(district_geometry.area)
        density = (total_building_area / district_area) * 100 if district_area > 0 else 0.0
        districts.at[idx, "building_density_pct"] = round(density, 1)

    return districts


def save_results(helsinki: gpd.GeoDataFrame, districts: gpd.GeoDataFrame) -> None:
    """Save density CSV and choropleth map."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    MAP_DIR.mkdir(parents=True, exist_ok=True)

    export_columns = [column for column in ["name", "building_density_pct", "district_area_m2"] if column in districts.columns]
    districts[export_columns].sort_values("building_density_pct", ascending=False).to_csv(OUTPUT_CSV, index=False)

    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(12, 12))

    helsinki.boundary.plot(ax=ax, linewidth=1.5, color="white", alpha=0.7)
    districts.plot(
        ax=ax,
        column="building_density_pct",
        cmap="viridis",
        legend=True,
        edgecolor="black",
        linewidth=0.3,
    )

    ax.set_title("Building density by district (Helsinki)", fontsize=14)
    ax.set_axis_off()
    plt.savefig(OUTPUT_MAP, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def main() -> None:
    configure_osmnx()
    helsinki, districts, buildings = download_helsinki_data()
    helsinki, districts, buildings = prepare_layers(helsinki, districts, buildings)
    districts = calculate_density(districts, buildings)
    save_results(helsinki, districts)

    print("Density calculation completed.")
    print(f"CSV saved to {OUTPUT_CSV}")
    print(f"Map saved to {OUTPUT_MAP}")


if __name__ == "__main__":
    main()
