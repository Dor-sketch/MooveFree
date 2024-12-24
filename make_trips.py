import pandas as pd

def create_stops_file(gtfs_path, output_file):
    """
    Create a text file that stores the stops each bus line passes in its trips.

    Args:
        gtfs_path (str): Path to the folder containing GTFS files.
        output_file (str): Path to the output file where data will be saved.

    Returns:
        None
    """
    # Load GTFS files
    routes = pd.read_csv(f"{gtfs_path}/routes.txt")
    trips = pd.read_csv(f"{gtfs_path}/trips.txt")
    stop_times = pd.read_csv(f"{gtfs_path}/stop_times.txt")
    stops = pd.read_csv(f"{gtfs_path}/stops.txt")

    # Merge data to get a complete picture
    trips_stop_times = pd.merge(trips, stop_times, on="trip_id")
    trips_stop_times_stops = pd.merge(trips_stop_times, stops, on="stop_id")
    trips_stop_times_stops_routes = pd.merge(trips_stop_times_stops, routes, on="route_id")

    # Select and organize required columns
    bus_lines_data = trips_stop_times_stops_routes[[
        "route_short_name", "trip_id", "stop_sequence", "stop_id", "stop_name", "stop_lat", "stop_lon"
    ]]

    # Sort the data for clarity
    bus_lines_data = bus_lines_data.sort_values(by=["route_short_name", "trip_id", "stop_sequence"])

    # Save the result to a text file
    bus_lines_data.to_csv(output_file, index=False, sep=",", encoding="utf-8")
    print(f"Stops data has been saved to {output_file}")

# Example Usage
gtfs_path = "israel-public-transportation"  # Path to the GTFS files
output_file = "bus_lines_stops.txt"  # Path to the output file
create_stops_file(gtfs_path, output_file)
