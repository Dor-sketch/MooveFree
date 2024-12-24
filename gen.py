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

def create_styles_css(output_dir):
    """Create the styles.css file in the output directory."""
    css_content = """/* Base styles */
:root {
    --primary-color: #3B82F6;
    --primary-dark: #2563EB;
    --secondary-color: #764BA2;
    --gradient-start: #667EEA;
    --gradient-end: #764BA2;
    --text-primary: #1F2937;
    --text-secondary: #4B5563;
    --background-light: #F9FAFB;
    --card-hover-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

/* Navigation styles */
.nav-container {
    background: linear-gradient(135deg, var(--gradient-start) 0%, var(--gradient-end) 100%);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.nav-link {
    transition: opacity 0.2s ease;
}

.nav-link:hover {
    opacity: 0.8;
}

/* Map container styles */
.map-container {
    height: 500px;
    width: 100%;
    border-radius: 0.75rem;
    overflow: hidden;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    border: 2px solid #E5E7EB;
}

/* Stop card styles */
.stop-card {
    transition: all 0.3s ease;
    border: 1px solid #E5E7EB;
    position: relative;
    overflow: hidden;
}

.stop-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--card-hover-shadow);
    border-color: var(--primary-color);
}

.stop-number {
    background-color: var(--primary-color);
    color: white;
    width: 2rem;
    height: 2rem;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
}

/* Route header styles */
.route-header {
    background: white;
    border-radius: 0.75rem;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    border: 1px solid #E5E7EB;
}

.route-badge {
    background-color: #DBEAFE;
    color: var(--primary-color);
    font-weight: 600;
    padding: 0.5rem 1rem;
    border-radius: 9999px;
    font-size: 0.875rem;
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .map-container {
        height: 400px;
    }

    .stop-card {
        margin-bottom: 0.5rem;
    }
}

/* Custom scrollbar for stops list */
.stops-container {
    max-height: 600px;
    overflow-y: auto;
    scrollbar-width: thin;
    scrollbar-color: var(--primary-color) #E5E7EB;
}

.stops-container::-webkit-scrollbar {
    width: 6px;
}

.stops-container::-webkit-scrollbar-track {
    background: #E5E7EB;
    border-radius: 3px;
}

.stops-container::-webkit-scrollbar-thumb {
    background-color: var(--primary-color);
    border-radius: 3px;
}"""

    with open(os.path.join(output_dir, 'styles.css'), 'w', encoding='utf-8') as f:
        f.write(css_content)

def generate_stylish_route_pages(gtfs_path):
    """Generate stylish HTML pages with maps for each route in the GTFS data."""
    try:
        # Create output directory
        output_dir = "route_pages"
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir)

        # Create styles.css
        create_styles_css(output_dir)

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
            <link href="https://cdn.tailwindcss.com" rel="stylesheet">
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
            <link rel="stylesheet" href="styles.css">
            <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
        </head>
        <body class="bg-gray-50 min-h-screen">
            <!-- Navigation -->
            <nav class="nav-container text-white">
                <div class="container mx-auto px-4 py-3">
                    <div class="flex items-center justify-between">
                        <a href="index.html" class="nav-link flex items-center space-x-2">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
                            </svg>
                            <span>All Routes</span>
                        </a>
                        <span class="text-xl font-bold">Transit Explorer</span>
                    </div>
                </div>
            </nav>

            <!-- Main Content -->
            <main class="container mx-auto px-4 py-8">
                <!-- Route Header -->
                <div class="route-header p-6 mb-8">
                    <div class="flex items-center justify-between">
                        <div>
                            <div class="flex items-center space-x-3">
                                <h1 class="text-4xl font-bold text-gray-800">Route {{ route_short_name }}</h1>
                                <span class="route-badge">
                                    {% if route_type == '3' %}Bus
                                    {% elif route_type == '2' %}Train
                                    {% elif route_type == '0' %}Tram
                                    {% else %}Other{% endif %}
                                </span>
                            </div>
                            <p class="text-lg text-gray-600 mt-2">{{ route_long_name }}</p>
                        </div>
                        <div class="text-right">
                            <span class="px-4 py-2 bg-blue-100 text-blue-800 rounded-full">{{ stops|length }} Stops</span>
                        </div>
                    </div>
                </div>

                <!-- Map and Stops Grid -->
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    <!-- Map -->
                    <div class="lg:col-span-2">
                        <div class="bg-white rounded-lg shadow-lg p-6">
                            <h2 class="text-2xl font-bold text-gray-800 mb-4">Route Map</h2>
                            <div id="map" class="map-container"></div>
                        </div>
                    </div>

                    <!-- Stops List -->
                    <div class="lg:col-span-1">
                        <div class="bg-white rounded-lg shadow-lg p-6">
                            <h2 class="text-2xl font-bold text-gray-800 mb-4">Stops</h2>
                            <div class="stops-container space-y-3">
                                {% for stop in stops %}
                                <div class="stop-card bg-gray-50 rounded-lg p-4 cursor-pointer"
                                     onclick="highlightStop({{ stop.lat }}, {{ stop.lon }}, '{{ stop.name|replace("'", "\\'") }}')">
                                    <div class="flex items-center">
                                        <span class="stop-number mr-4 flex-shrink-0">
                                            {{ stop.sequence }}
                                        </span>
                                        <div>
                                            <p class="font-medium text-gray-800">{{ stop.name }}</p>
                                            <p class="text-sm text-gray-500">{{ stop.lat }}, {{ stop.lon }}</p>
                                        </div>
                                    </div>
                                </div>
                                {% endfor %}
                            </div>
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
                    color: '#3B82F6',
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
                route_short_name = str(route['route_short_name'])
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
                            stops_info.append({
                                'sequence': int(stop_time['stop_sequence']),
                                'name': stop['stop_name'],
                                'lat': float(stop['stop_lat']),
                                'lon': float(stop['stop_lon'])
                            })
                        except Exception as e:
                            print(f"Error processing stop: {e}")
                            continue

                    # Generate HTML
                    html_content = route_template.render(
                        route_short_name=route_short_name,
                        route_long_name=route['route_long_name'],
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