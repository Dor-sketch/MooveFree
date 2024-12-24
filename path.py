import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import LineString
import contextily as ctx

def plot_line_with_correct_edges(line_short_name, gtfs_path):
    """
    Plot the line on an OpenStreetMap basemap using station coordinates and order.
    Ensures correct edges by using one trip to determine the station order.

    Args:
        line_short_name (str): The short name of the line (e.g., "480").
        gtfs_path (str): Path to the folder containing GTFS files.

    Returns:
        None
    """
    # Load GTFS files
    routes = pd.read_csv(f"{gtfs_path}/routes.txt")
    trips = pd.read_csv(f"{gtfs_path}/trips.txt")
    stop_times = pd.read_csv(f"{gtfs_path}/stop_times.txt")
    stops = pd.read_csv(f"{gtfs_path}/stops.txt")

    # Step 1: Find the route_id(s) for the specified line
    line_routes = routes[routes['route_short_name'] == line_short_name]
    if line_routes.empty:
        print(f"No routes found for line {line_short_name}.")
        return

    route_ids = line_routes['route_id'].tolist()

    # Step 2: Find the trip_id(s) associated with these route_ids
    line_trips = trips[trips['route_id'].isin(route_ids)]
    if line_trips.empty:
        print(f"No trips found for line {line_short_name}.")
        return

    # Pick one specific trip to define the route sequence
    selected_trip_id = line_trips.iloc[0]['trip_id']

    # Step 3: Find the stop_id(s) and stop_sequence for the selected trip
    trip_stop_times = stop_times[stop_times['trip_id'] == selected_trip_id].sort_values(by='stop_sequence')

    # Step 4: Find the stop details in stops.txt
    trip_stops = stops[stops['stop_id'].isin(trip_stop_times['stop_id'])]
    trip_data = trip_stop_times.merge(trip_stops, on='stop_id').sort_values(by='stop_sequence')

    # Create GeoDataFrame for stops
    trip_stops_gdf = gpd.GeoDataFrame(
        trip_data,
        geometry=gpd.points_from_xy(trip_data['stop_lon'], trip_data['stop_lat']),
        crs="EPSG:4326"
    )

    # Create a LineString from stops in the correct sequence
    line_geometry = LineString(trip_stops_gdf.geometry.tolist())
    line_gdf = gpd.GeoDataFrame({"geometry": [line_geometry]}, crs="EPSG:4326")

    # Plot the map
    fig, ax = plt.subplots(figsize=(10, 10))
    trip_stops_gdf.plot(ax=ax, color="blue", markersize=50, label="Stops")
    line_gdf.plot(ax=ax, color="red", linewidth=2, label="Route")

    # Add basemap (OpenStreetMap)
    ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, crs="EPSG:4326")

    # Add labels with station order
    for _, row in trip_data.iterrows():
        ax.annotate(
            f"{row['stop_sequence']}: {row['stop_name']}",
            xy=(row['stop_lon'], row['stop_lat']),
            xytext=(3, 3),
            textcoords="offset points",
            fontsize=8
        )

    plt.legend()
    plt.title(f"Line {line_short_name} on OpenStreetMap with Correct Edges")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.show()

# Example Usage
gtfs_path = "israel-public-transportation"
plot_line_with_correct_edges("48", gtfs_path)
