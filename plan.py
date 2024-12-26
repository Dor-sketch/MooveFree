
import pandas as pd
from dataclasses import dataclass
from typing import List, Dict, Set, Optional, Tuple
from collections import defaultdict
import networkx as nx
import pickle
import os
from datetime import datetime
import json
from math import radians, sin, cos, sqrt, atan2

@dataclass
class Stop:
    """Represents a transit stop with coordinates"""
    stop_id: str
    stop_name: str
    lat: float
    lon: float

@dataclass
class Trip:
    """Represents a trip segment"""
    route_id: str
    from_stop: str
    to_stop: str
    departure_time: str
    arrival_time: str
    is_walking: bool = False

@dataclass
class Journey:
    """Represents a complete journey with multiple trips"""
    trips: List[Trip]
    total_time: int
    total_walking: float = 0  # in meters
class GTFSPlanner:
    def _normalize_time(self, time_str: str) -> str:
        """Normalize GTFS time format to handle times after midnight"""
        try:
            h, m, s = map(int, time_str.split(':'))
            if h >= 24:  # Convert times after midnight back to standard format
                h = h - 24
            return f"{h:02d}:{m:02d}:{s:02d}"
        except ValueError as e:
            print(f"Error normalizing time {time_str}: {e}")
            return time_str
    def _time_diff(self, time1: str, time2: str) -> int:
        """
        Calculate difference between two times in minutes, handling GTFS >24 hour format.

        Args:
            time1: First time (format HH:MM:SS or >24:MM:SS)
            time2: Second time (format HH:MM:SS or >24:MM:SS)
        Returns:
            int: time2 - time1 in minutes
        """
        def to_minutes(time_str):
            h, m, s = map(int, time_str.split(':'))
            total_minutes = h * 60 + m
            return total_minutes

        # Convert times directly without modification
        minutes1 = to_minutes(time1)
        minutes2 = to_minutes(time2)

        # Simply return the difference since GTFS already handles day wrapping with >24:00:00 format
        return minutes2 - minutes1

    def _find_next_trip(self, from_stop: str, to_stop: str, current_time: str, routes: set) -> Optional[Trip]:
        """Find the next available trip between two stops after a given time"""
        routes = {str(route) for route in routes}

        try:
            # Load stop times
            stop_times_df = pd.read_csv(f"{self.gtfs_path}/stop_times.txt")
            stop_times_df['stop_id'] = stop_times_df['stop_id'].astype(str)
            stop_times_df['trip_id'] = stop_times_df['trip_id'].astype(str)

            # Debug output
            print(f"\nSearching for trips from {from_stop} to {to_stop} after {current_time}")
            print(f"Looking at routes: {routes}")

            # Get trips that serve these stops
            from_stop_times = stop_times_df[stop_times_df['stop_id'] == from_stop]
            to_stop_times = stop_times_df[stop_times_df['stop_id'] == to_stop]

            if from_stop_times.empty:
                print(f"No departures found from stop {from_stop}")
                return None
            if to_stop_times.empty:
                print(f"No arrivals found at stop {to_stop}")
                return None

            print(f"Found {len(from_stop_times)} departures and {len(to_stop_times)} arrivals")

            # Find common trips
            common_trips = set(from_stop_times['trip_id']) & set(to_stop_times['trip_id'])
            print(f"Found {len(common_trips)} common trips between these stops")

            if not common_trips:
                return None

            # Filter trips by route
            self.trips['trip_id'] = self.trips['trip_id'].astype(str)
            self.trips['route_id'] = self.trips['route_id'].astype(str)

            valid_trips = self.trips[
                (self.trips['trip_id'].isin(common_trips)) &
                (self.trips['route_id'].isin(routes))
            ]

            print(f"Found {len(valid_trips)} trips on requested routes")

            if valid_trips.empty:
                return None

            best_trip = None
            earliest_arrival = None

            for trip_id in valid_trips['trip_id']:
                trip_stops = stop_times_df[stop_times_df['trip_id'] == str(trip_id)].sort_values('stop_sequence')

                from_stop_times = trip_stops[trip_stops['stop_id'] == from_stop]
                to_stop_times = trip_stops[trip_stops['stop_id'] == to_stop]

                if from_stop_times.empty or to_stop_times.empty:
                    continue

                from_stop_time = from_stop_times['departure_time'].iloc[0]
                to_stop_time = to_stop_times['arrival_time'].iloc[0]

                # Debug time comparison
                time_diff = self._time_diff(current_time, from_stop_time)
                print(f"Trip {trip_id}: Departs at {from_stop_time}, time diff from {current_time} is {time_diff} minutes")

                # Check if this trip is after current time and arrives earlier than current best
                if time_diff >= 0 and (earliest_arrival is None or
                                     self._time_diff(to_stop_time, earliest_arrival) < 0):
                    route_id = str(valid_trips[valid_trips['trip_id'] == trip_id]['route_id'].iloc[0])
                    best_trip = Trip(
                        route_id=route_id,
                        from_stop=from_stop,
                        to_stop=to_stop,
                        departure_time=from_stop_time,
                        arrival_time=to_stop_time
                    )
                    earliest_arrival = to_stop_time
                    print(f"Found better trip: Route {route_id}, {from_stop_time} -> {to_stop_time}")

            return best_trip

        except Exception as e:
            print(f"Error finding next trip: {str(e)}")
            traceback.print_exc()  # Print full stack trace
            return None
    def load_gtfs_data(self):
        """Load GTFS data and cached network if available"""
        print("Loading GTFS data...")

        # Load core GTFS files
        self.stops = pd.read_csv(f"{self.gtfs_path}/stops.txt")
        # Convert stop_id to string to ensure consistent type matching
        self.stops['stop_id'] = self.stops['stop_id'].astype(str)

        self.routes = pd.read_csv(f"{self.gtfs_path}/routes.txt")
        self.trips = pd.read_csv(f"{self.gtfs_path}/trips.txt")

        # Create cache directory if it doesn't exist
        os.makedirs('cache', exist_ok=True)
        cache_file = os.path.join('cache', 'network_data.pkl')

        # Try to load cached network
        if os.path.exists(cache_file):
            print("Loading cached network...")
            try:
                with open(cache_file, 'rb') as f:
                    cached_data = pickle.load(f)

                # Convert network data back to networkx Graph
                self.network = nx.Graph()
                self.network.add_edges_from(cached_data['edges'])

                # Convert defaultdict data
                self.stop_routes = defaultdict(set, {k: set(v) for k, v in cached_data['stop_routes'].items()})
                self.route_stops = defaultdict(set, {k: set(v) for k, v in cached_data['route_stops'].items()})

                # Convert direct connections
                self.direct_connections = {}
                for from_stop, to_stops in cached_data['direct_connections'].items():
                    self.direct_connections[from_stop] = {}
                    for to_stop, routes in to_stops.items():
                        self.direct_connections[from_stop][to_stop] = set(routes)

                print("✓ Loaded cached network successfully")

            except Exception as e:
                print(f"Failed to load cache: {str(e)}")
                print("Rebuilding network...")
                self.build_network()
        else:
            print("No cached network found, building network...")
            self.build_network()

    def __init__(self, gtfs_path: str, max_walking_distance: float = 500):
        """
        Initialize the GTFS trip planner

        Args:
            gtfs_path: Path to GTFS files
            max_walking_distance: Maximum walking distance between stops in meters
        """
        self.gtfs_path = gtfs_path
        self.max_walking_distance = max_walking_distance
        self.load_gtfs_data()

    def get_stop_details(self, stop_id: str) -> Tuple[str, float, float]:
        """Get stop name and coordinates"""
        stop_id = str(stop_id)  # Ensure stop_id is string
        stop_data = self.stops[self.stops['stop_id'].astype(str) == stop_id]

        if stop_data.empty:
            raise ValueError(f"Stop ID {stop_id} not found in stops data")

        stop = stop_data.iloc[0]
        return stop['stop_name'], float(stop['stop_lat']), float(stop['stop_lon'])
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in meters using Haversine formula"""
        R = 6371000  # Earth's radius in meters

        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        distance = R * c

        return distance

    def add_walking_connections(self):
        """Add walking connections between nearby stops"""
        print("\nAnalyzing walking connections...")
        walking_edges = []
        stops_df = self.stops.copy()

        # Convert stop coordinates to float
        stops_df['stop_lat'] = pd.to_numeric(stops_df['stop_lat'], errors='coerce')
        stops_df['stop_lon'] = pd.to_numeric(stops_df['stop_lon'], errors='coerce')

        # Remove stops with invalid coordinates
        valid_stops = stops_df.dropna(subset=['stop_lat', 'stop_lon'])

        # Create spatial index for efficient nearby stop finding
        from rtree import index
        idx = index.Index()
        stop_coords = {}

        # Build spatial index
        for _, stop in valid_stops.iterrows():
            stop_id = str(stop['stop_id'])
            lat, lon = stop['stop_lat'], stop['stop_lon']
            idx.insert(int(stop_id), (lon, lat, lon, lat))
            stop_coords[stop_id] = (lat, lon)

        # Find nearby stops
        walking_connections = 0
        for stop_id, (lat, lon) in stop_coords.items():
            # Find potential nearby stops using spatial index
            nearby = list(idx.intersection((
                lon - 0.01,  # roughly 1km at equator
                lat - 0.01,
                lon + 0.01,
                lat + 0.01
            )))

            for near_id in nearby:
                near_id = str(near_id)
                if near_id != stop_id:
                    near_lat, near_lon = stop_coords[near_id]
                    distance = self.calculate_distance(lat, lon, near_lat, near_lon)

                    if distance <= self.max_walking_distance:
                        # Add walking edge to network
                        self.network.add_edge(stop_id, near_id,
                                           weight=distance,
                                           type='walking')
                        walking_connections += 1

                        # Add to direct connections with special walking route
                        if stop_id not in self.direct_connections:
                            self.direct_connections[stop_id] = {}
                        if near_id not in self.direct_connections[stop_id]:
                            self.direct_connections[stop_id][near_id] = set()
                        self.direct_connections[stop_id][near_id].add('walking')

        print(f"Added {walking_connections} walking connections")

    def create_walking_trip(self, from_stop: str, to_stop: str, current_time: str) -> Trip:
        """Create a walking trip between stops"""
        # Get coordinates
        _, from_lat, from_lon = self.get_stop_details(from_stop)
        _, to_lat, to_lon = self.get_stop_details(to_stop)

        # Calculate walking time (assuming 5 km/h walking speed)
        distance = self.calculate_distance(from_lat, from_lon, to_lat, to_lon)
        walking_time_minutes = int((distance / 5000) * 60)  # convert to minutes

        # Calculate arrival time
        h, m, s = map(int, current_time.split(':'))
        total_minutes = h * 60 + m + walking_time_minutes
        arrival_h = total_minutes // 60
        arrival_m = total_minutes % 60
        arrival_time = f"{arrival_h:02d}:{arrival_m:02d}:00"

        return Trip(
            route_id='walking',
            from_stop=from_stop,
            to_stop=to_stop,
            departure_time=current_time,
            arrival_time=arrival_time,
            is_walking=True
        )
    def find_path(self, start_stop: str, end_stop: str, start_time: str) -> List[Journey]:
        """Find possible journeys between two stops"""
        # Convert stop IDs to strings
        start_stop = str(start_stop)
        end_stop = str(end_stop)

        print(f"\nFinding paths from {start_stop} to {end_stop} starting at {start_time}")

        # Get stop names for better output
        start_name = self.get_stop_details(start_stop)[0]
        end_name = self.get_stop_details(end_stop)[0]
        print(f"From: {start_name} to {end_name}")

        if start_stop == end_stop:
            print("Start and end stops are the same!")
            return []

        if not nx.has_path(self.network, start_stop, end_stop):
            print("No path exists between these stops!")
            return []

        # Find shortest paths in terms of stops
        paths = list(nx.all_shortest_paths(self.network, start_stop, end_stop))
        print(f"Found {len(paths)} possible paths")

        journeys = []
        for path_idx, path in enumerate(paths, 1):
            print(f"\nAnalyzing path {path_idx}/{len(paths)}:")

            # Convert path stops to strings and print
            path = [str(stop) for stop in path]  # Convert all stops in path to strings
            path_stops = []
            for stop_id in path:
                stop_name = self.get_stop_details(stop_id)[0]
                path_stops.append(f"{stop_id} ({stop_name})")
            print("Stops:", ' -> '.join(path_stops))

            # Convert path to trips
            trips = []
            current_time = start_time
            path_valid = True
            total_walking = 0

            for i in range(len(path) - 1):
                from_stop = path[i]  # Already string from earlier conversion
                to_stop = path[i + 1]  # Already string from earlier conversion

                # Get stop names for output
                from_name = self.get_stop_details(from_stop)[0]
                to_name = self.get_stop_details(to_stop)[0]
                print(f"\n  Finding connection from {from_name} to {to_name} after {current_time}")

                try:
                    # Find routes that connect these stops
                    possible_routes = self.direct_connections[from_stop][to_stop]
                    # Convert routes to strings for display
                    routes_display = ', '.join(str(route) for route in possible_routes)
                    print(f"  Found {len(possible_routes)} possible routes: {routes_display}")

                    next_trip = None

                    # Check for walking option (ensure string comparison)
                    if 'walking' in {str(r) for r in possible_routes}:
                        walking_trip = self.create_walking_trip(from_stop, to_stop, current_time)
                        print(f"  Walking option available: {walking_trip.departure_time} -> {walking_trip.arrival_time}")
                        next_trip = walking_trip
                        total_walking += self.calculate_distance(
                            *self.get_stop_details(from_stop)[1:],
                            *self.get_stop_details(to_stop)[1:]
                        )

                    # If not walking or if we want to check for better transit options
                    transit_routes = {str(r) for r in possible_routes if str(r) != 'walking'}
                    if transit_routes:
                        transit_trip = self._find_next_trip(from_stop, to_stop, current_time, transit_routes)
                        if transit_trip and (not next_trip or
                                           self._time_diff(current_time, transit_trip.arrival_time) <
                                           self._time_diff(current_time, next_trip.arrival_time)):
                            next_trip = transit_trip

                    if next_trip:
                        route_display = 'Walking' if next_trip.is_walking else f'Route {str(next_trip.route_id)}'
                        print(f"  Selected: {route_display} "
                              f"({next_trip.departure_time} -> {next_trip.arrival_time})")
                        trips.append(next_trip)
                        current_time = next_trip.arrival_time
                    else:
                        print("  No valid connection found for this segment")
                        path_valid = False
                        break

                except Exception as e:
                    print(f"  Error processing connection: {str(e)}")
                    path_valid = False
                    break

            if path_valid and trips and len(trips) == len(path) - 1:
                total_time = self._calculate_journey_time(trips)
                journeys.append(Journey(trips=trips, total_time=total_time, total_walking=total_walking))
                print(f"\nValid journey found! Total time: {total_time} minutes, Walking: {total_walking:.0f}m")
            else:
                print("\nPath invalid or incomplete")

        # Sort journeys by total time
        journeys.sort(key=lambda x: x.total_time)
        print(f"\nFound {len(journeys)} valid journeys")
        return journeys

    def build_network(self):
        """Build network representation of the transit system"""
        print("\nBuilding transit network...")
        from tqdm import tqdm

        # Create graph for finding connected stops
        self.network = nx.Graph()
        self.stop_routes = defaultdict(set)
        self.route_stops = defaultdict(set)
        self.direct_connections = {}

        # Build route catalog mapping - use first 5 digits as per docs
        print("Creating route catalog lookup...")
        route_catalog = defaultdict(set)
        catalog_to_routes = defaultdict(set)
        for _, route in self.routes.iterrows():
            route_id = str(route['route_id'])
            desc = str(route['route_desc'])
            # According to docs, route_desc contains "line catalog number-direction-alternative"
            if '-' in desc:
                catalog_num = desc.split('-')[0]  # Get first 5 digits
                route_catalog[route_id] = catalog_num
                catalog_to_routes[catalog_num].add(route_id)

        # Create trip to route lookup for faster access
        print("Creating trip-route lookup...")
        trip_route_lookup = dict(zip(
            self.trips['trip_id'].astype(str),
            self.trips['route_id'].astype(str)
        ))

        # Process stop_times in chunks
        print("Processing stop_times...")
        chunk_size = 1000000  # Process 1M rows at a time
        processed_trips = set()

        with tqdm(total=sum(1 for _ in open(f"{self.gtfs_path}/stop_times.txt")) - 1) as pbar:
            for chunk in pd.read_csv(
                f"{self.gtfs_path}/stop_times.txt",
                chunksize=chunk_size,
                usecols=['trip_id', 'stop_id', 'stop_sequence']
            ):
                # Convert IDs to strings
                chunk['trip_id'] = chunk['trip_id'].astype(str)
                chunk['stop_id'] = chunk['stop_id'].astype(str)

                # Group by trip and process
                for trip_id, trip_stops in chunk.groupby('trip_id'):
                    if trip_id in processed_trips:
                        continue

                    processed_trips.add(trip_id)
                    route_id = trip_route_lookup.get(trip_id)
                    if not route_id:
                        continue

                    # Get catalog number for this route
                    catalog_num = route_catalog.get(str(route_id))
                    if not catalog_num:
                        continue

                    # Get all related routes from same catalog
                    related_routes = catalog_to_routes[catalog_num]

                    # Sort stops by sequence
                    stops = trip_stops.sort_values('stop_sequence')['stop_id'].tolist()

                    # Add to route-stop mappings
                    for stop_id in stops:
                        # Add all related routes to this stop
                        self.stop_routes[stop_id].update(related_routes)
                        for r_id in related_routes:
                            self.route_stops[r_id].add(stop_id)

                    # Add edges between consecutive stops
                    for i in range(len(stops) - 1):
                        from_stop = stops[i]
                        to_stop = stops[i + 1]

                        self.network.add_edge(from_stop, to_stop)

                        # Add to direct connections with all related routes
                        for a, b in [(from_stop, to_stop), (to_stop, from_stop)]:
                            if a not in self.direct_connections:
                                self.direct_connections[a] = {}
                            if b not in self.direct_connections[a]:
                                self.direct_connections[a][b] = set()
                            self.direct_connections[a][b].update(related_routes)

                pbar.update(len(chunk))

        # Add walking connections
        print("\nAdding walking connections...")
        self.add_walking_connections()

        print(f"\nNetwork statistics:")
        print(f"- Nodes (stops): {len(self.network.nodes):,}")
        print(f"- Edges (connections): {len(self.network.edges):,}")
        print(f"- Routes: {len(self.route_stops):,}")
        print(f"- Direct connections: {sum(len(to_stops) for to_stops in self.direct_connections.values()):,}")

        # Cache the network
        print("\nCaching network for future use...")
        os.makedirs('cache', exist_ok=True)
        cache_file = os.path.join('cache', 'network_data.pkl')

        # Convert sets to lists for pickling
        cache_data = {
            'edges': list(self.network.edges()),
            'stop_routes': {k: list(v) for k, v in self.stop_routes.items()},
            'route_stops': {k: list(v) for k, v in self.route_stops.items()},
            'direct_connections': {
                from_stop: {
                    to_stop: list(routes)
                    for to_stop, routes in to_stops.items()
                }
                for from_stop, to_stops in self.direct_connections.items()
            }
        }

        with open(cache_file, 'wb') as f:
            pickle.dump(cache_data, f)
        print("✓ Network cached successfully")
def example_usage():
    """Example usage of the trip planner"""
    print("Starting GTFS Processing Example...")

    # Initialize planner with 800m max walking distance
    planner = GTFSPlanner("israel-public-transportation", max_walking_distance=800)

    # Find busy stops based on how many routes serve them
    print("\nFinding frequently served stops...")
    stop_route_counts = {stop: len(routes) for stop, routes in planner.stop_routes.items()}
    busy_stops = sorted(stop_route_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    # Get names of these stops
    print("\nBusiest stops:")
    for stop_id, route_count in busy_stops:
        try:
            stop_name, lat, lon = planner.get_stop_details(stop_id)
            print(f"Stop {stop_id} ({stop_name}): served by {route_count} routes")
        except Exception as e:
            print(f"Stop {stop_id}: Error getting details - {str(e)}")

    # Pick two busy stops for our test
    try:
        # Get the first and last stop from busy_stops
        start_stop_id = busy_stops[-1][0]  # First stop ID
        end_stop_id = busy_stops[0][0]   # Last stop ID

        # Print detailed journey information
        print("\nSearching for journeys...")
        journeys = planner.find_path(start_stop_id, end_stop_id, "08:00:00")

        if journeys:
            print("\nFound journeys (showing top 3):")
            for i, journey in enumerate(journeys[:3], 1):
                print(f"\nJourney {i}:")
                print(f"Total time: {journey.total_time} minutes")
                print(f"Total walking: {journey.total_walking:.0f} meters")

                for j, trip in enumerate(journey.trips, 1):
                    try:
                        from_name = planner.get_stop_details(trip.from_stop)[0]
                        to_name = planner.get_stop_details(trip.to_stop)[0]

                        print(f"\n  Leg {j}:")
                        if trip.is_walking:
                            print(f"    WALK: {from_name} -> {to_name}")
                            print(f"    Time: {trip.departure_time} -> {trip.arrival_time}")
                        else:
                            route_name = planner.routes[planner.routes['route_id'] == trip.route_id]['route_short_name'].iloc[0]
                            print(f"    Route {route_name}")
                            print(f"    From: {from_name} at {trip.departure_time}")
                            print(f"    To: {to_name} at {trip.arrival_time}")

                    except Exception as e:
                        print(f"  Leg {j}: Error getting details - {str(e)}")
        else:
            print("\n❌ No journeys found!")

    except Exception as e:
        print(f"\nError planning journey: {str(e)}")

if __name__ == "__main__":
    example_usage()
