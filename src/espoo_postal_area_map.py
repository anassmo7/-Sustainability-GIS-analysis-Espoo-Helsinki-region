"""Create a GIS map and building-density estimate for postal code 02150 in Espoo.

The workflow downloads OpenStreetMap buildings, roads, and boundary data using
OSMnx, reprojects everything to EPSG:3067, creates a static map, and prints the
building density percentage for the postal-code area.
"""

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import osmnx as ox


POSTAL_CODE = "02150"
PLACE_QUERY = f"{POSTAL_CODE}, Espoo, Finland"
CITY_QUERY = "Espoo, Finland"
CRS_FIN = "EPSG:3067"
OUTPUT_DIR = Path("outputs/maps")
OUTPUT_MAP = OUTPUT_DIR / f"espoo_{POSTAL_CODE}_map.png"


def configure_osmnx() -> None:
    """Configure OSMnx cache, logging, and timeout settings."""
    ox.settings.use_cache = True
    ox.settings.log_console = False
    ox.settings.timeout = 180


def download_data() -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """Download boundary, building, and road datasets from OpenStreetMap."""
    postal_area = ox.geocode_to_gdf(PLACE_QUERY)
    city_area = ox.geocode_to_gdf(CITY_QUERY)
    postal_polygon = postal_area.geometry.iloc[0]

    buildings = ox.features_from_polygon(postal_polygon, tags={"building": True})
    buildings = buildings[buildings.geometry.notna()].copy()
    buildings = buildings[buildings.geometry.type.isin(["Polygon", "MultiPolygon"])].copy()

    graph = ox.graph_from_polygon(postal_polygon, network_type="drive", simplify=True)
    _, edges = ox.graph_to_gdfs(graph, nodes=True, edges=True, fill_edge_geometry=True)
    roads = edges[edges.geometry.type.isin(["LineString", "MultiLineString"])].copy()

    return postal_area, city_area, buildings, roads


def reproject_layers(
    postal_area: gpd.GeoDataFrame,
    city_area: gpd.GeoDataFrame,
    buildings: gpd.GeoDataFrame,
    roads: gpd.GeoDataFrame,
) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """Reproject all spatial layers to EPSG:3067."""
    return (
        postal_area.to_crs(CRS_FIN),
        city_area.to_crs(CRS_FIN),
        buildings.to_crs(CRS_FIN),
        roads.to_crs(CRS_FIN),
    )


def calculate_building_density(postal_area: gpd.GeoDataFrame, buildings: gpd.GeoDataFrame) -> float:
    """Calculate building density as building area divided by district area."""
    district_geometry = postal_area.geometry.iloc[0].buffer(0)
    buildings = buildings.copy()
    buildings["geometry"] = buildings.geometry.buffer(0)

    buildings_in_district = buildings[buildings.intersects(district_geometry)].copy()
    buildings_in_district["geometry"] = buildings_in_district.geometry.apply(
        lambda geometry: geometry.intersection(district_geometry) if geometry is not None else None
    )
    buildings_in_district = buildings_in_district[
        buildings_in_district.geometry.notna() & ~buildings_in_district.is_empty
    ].copy()

    total_building_area = buildings_in_district.geometry.area.sum()
    district_area = district_geometry.area
    return (total_building_area / district_area) * 100 if district_area > 0 else 0.0


def plot_map(postal_area: gpd.GeoDataFrame, buildings: gpd.GeoDataFrame, roads: gpd.GeoDataFrame) -> None:
    """Create and save a map of buildings, roads, and the postal-code boundary."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    postal_geometry = postal_area.geometry.iloc[0]
    roads_clip = roads.clip(postal_geometry)
    buildings_clip = buildings.clip(postal_geometry)

    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(8, 10))
    ax.set_facecolor("black")
    fig.patch.set_facecolor("black")

    buildings_clip.plot(ax=ax, color="#CFCFCF", edgecolor="none", alpha=0.9, zorder=2)
    roads_clip.plot(ax=ax, color="#8A8A8A", linewidth=0.6, alpha=0.9, zorder=3)
    postal_area.boundary.plot(ax=ax, linewidth=2.5, color="red", alpha=1.0, zorder=4)

    minx, miny, maxx, maxy = postal_area.total_bounds
    pad_x = (maxx - minx) * 0.05
    pad_y = (maxy - miny) * 0.05
    ax.set_xlim(minx - pad_x, maxx + pad_x)
    ax.set_ylim(miny - pad_y, maxy + pad_y)

    ax.set_title(f"Espoo postal code {POSTAL_CODE}", fontsize=16, weight="bold", pad=10)
    ax.set_aspect("equal")
    ax.set_axis_off()

    plt.savefig(OUTPUT_MAP, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def main() -> None:
    configure_osmnx()
    postal_area, city_area, buildings, roads = download_data()
    postal_area, city_area, buildings, roads = reproject_layers(postal_area, city_area, buildings, roads)

    density = calculate_building_density(postal_area, buildings)
    plot_map(postal_area, buildings, roads)

    print(f"Building density in {POSTAL_CODE} is {density:.1f}%.")
    print(f"Map saved to {OUTPUT_MAP}")


if __name__ == "__main__":
    main()
