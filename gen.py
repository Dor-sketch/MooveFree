import pandas as pd
import os
from jinja2 import Template, Environment, FileSystemLoader
import json
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2
import shutil

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in kilometers."""
    try:
        R = 6371  # Earth's radius in kilometers

        lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])  # Ensure values are float
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        return R * c
    except Exception as e:
        print(f"Error calculating distance: {e}")
        return 0


def generate_stylish_route_pages(gtfs_path):
    """Generate stylish HTML pages with maps for each route in the GTFS data."""
    try:
        # Create output directory
        output_dir = "route_pages"
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir)



        # Load GTFS files with error handling
        try:
            routes_df = pd.read_csv(f"{gtfs_path}/routes.txt")
            trips_df = pd.read_csv(f"{gtfs_path}/trips.txt")
            stop_times_df = pd.read_csv(f"{gtfs_path}/stop_times.txt")
            stops_df = pd.read_csv(f"{gtfs_path}/stops.txt")
        except Exception as e:
            print(f"Error reading GTFS files: {e}")
            return

        # HTML template for route pages
        route_template = Template("""
        <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Route {{ route_short_name }} - {{ route_long_name }}</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
    <link rel="stylesheet" href="styles.css">
    <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
</head>
<body>
    <!-- Navigation -->
    <nav class="transit-nav">
        <div class="transit-container">
            <div class="transit-nav-content">
                <a href="index.html" class="transit-nav-back">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
                    </svg>
                    <span>All Routes</span>
                </a>
                <span class="transit-nav-brand">Transit Explorer</span>
            </div>
        </div>
    </nav>

    <!-- Main Content -->
    <main class="transit-container">
        <!-- Route Header -->
        <div class="transit-card route-header">
            <div class="route-title">
                Route {{ route_short_name }}
                <span class="route-type-badge">
                    {% if route_type == '3' %}Bus
                    {% elif route_type == '2' %}Train
                    {% elif route_type == '0' %}Tram
                    {% else %}Other{% endif %}
                </span>
            </div>
            <div class="route-subtitle">{{ route_long_name }}</div>
        </div>

        <!-- Map and Stops Grid -->
        <div class="transit-layout-main">
            <!-- Map -->
            <div class="transit-card">
                <div class="route-title">Route Map</div>
                <div id="map" class="transit-map"></div>
            </div>

            <!-- Stops List -->
            <div class="transit-card">
                <div class="route-title">Stops</div>
                <div class="stops-container">
                    {% for stop in stops %}
                    <div class="stop-item" onclick="highlightStop({{ stop.lat }}, {{ stop.lon }}, '{{ stop.name }}')">
                        <span class="stop-number">{{ stop.sequence }}</span>
                        <div class="stop-details">
                            <div class="stop-name">{{ stop.name }}</div>
                            <div class="stop-coordinates">{{ stop.lat }}, {{ stop.lon }}</div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </main>

    <script>
        // Initialize map
        const map = L.map('map');
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap contributors'
        }).addTo(map);

        // Add stops to map
        const stops = {{ stops_json|safe }};
        const markers = [];
        const coordinates = stops.map(stop => [stop.lat, stop.lon]);

        stops.forEach(stop => {
            const marker = L.marker([stop.lat, stop.lon])
                .bindPopup(`<b>${stop.sequence}. ${stop.name}</b>`)
                .addTo(map);
            markers.push(marker);
        });

        // Draw route line
        const routeLine = L.polyline(coordinates, {
            color: 'var(--color-primary)',
            weight: 3,
            opacity: 0.8,
            lineJoin: 'round'
        }).addTo(map);

        // Fit map to route bounds
        map.fitBounds(routeLine.getBounds(), {padding: [50, 50]});

        // Function to highlight stop on map
        function highlightStop(lat, lon, name) {
            map.setView([lat, lon], 16, {
                animate: true,
                duration: 1
            });
            markers.forEach(marker => {
                if (marker.getLatLng().lat === lat && marker.getLatLng().lng === lon) {
                    marker.openPopup();
                }
            });
        }
    </script>
</body>
</html>
        """)

        # Generate individual route pages
        for _, route in routes_df.iterrows():
            try:
                # Clean route names as well
                route_short_name = str(route['route_short_name']).replace("'", "")
                route_long_name = str(route['route_long_name']).replace("'", "")
                print(f"Generating page for route {route_short_name}...")

                # Get trips for this route
                route_trips = trips_df[trips_df['route_id'] == route['route_id']]

                if not route_trips.empty:
                    # Get first trip's stops
                    first_trip = route_trips.iloc[0]
                    trip_stops = stop_times_df[stop_times_df['trip_id'] == first_trip['trip_id']].sort_values('stop_sequence')

                    # Get stop details
                    stops_info = []
                    for _, stop_time in trip_stops.iterrows():
                        try:
                            stop = stops_df[stops_df['stop_id'] == stop_time['stop_id']].iloc[0]
                            # Clean the stop name by removing any single quotes
                            clean_name = str(stop['stop_name']).replace("'", "")
                            stops_info.append({
                                'sequence': int(stop_time['stop_sequence']),
                                'name': clean_name,
                                'lat': float(stop['stop_lat']),
                                'lon': float(stop['stop_lon'])
                            })
                        except Exception as e:
                            print(f"Error processing stop: {e}")
                            continue

                    # Generate HTML
                    html_content = route_template.render(
                        route_short_name=route_short_name,
                        route_long_name=route_long_name,
                        route_type=route['route_type'],
                        agency_id=route.get('agency_id', 'N/A'),
                        stops=stops_info,
                        stops_json=json.dumps(stops_info)
                    )

                    # Save HTML file
                    with open(f"{output_dir}/route_{route_short_name}.html", 'w', encoding='utf-8') as f:
                        f.write(html_content)

            except Exception as e:
                print(f"Error processing route {route_short_name}: {e}")
                continue

        print(f"\nGenerated {len(routes_df)} route pages in '{output_dir}' directory")

    except Exception as e:
        print(f"Error generating route pages: {e}")

if __name__ == "__main__":
    # Example usage
    gtfs_path = "israel-public-transportation"  # Replace with your GTFS directory path
    generate_stylish_route_pages(gtfs_path)