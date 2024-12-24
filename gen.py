import pandas as pd
import os
from jinja2 import Template
import json

def generate_stylish_route_pages(gtfs_path):
    """
    Generate stylish HTML pages with maps for each route in the GTFS data.

    Args:
        gtfs_path (str): Path to the folder containing GTFS files
    """
    # Create output directory
    output_dir = "route_pages"
    os.makedirs(output_dir, exist_ok=True)

    # Load GTFS files
    routes_df = pd.read_csv(f"{gtfs_path}/routes.txt")
    trips_df = pd.read_csv(f"{gtfs_path}/trips.txt")
    stop_times_df = pd.read_csv(f"{gtfs_path}/stop_times.txt")
    stops_df = pd.read_csv(f"{gtfs_path}/stops.txt")

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
        <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
        <style>
            .map-container {
                height: 500px;
                width: 100%;
                border-radius: 0.5rem;
                overflow: hidden;
            }
            .stop-card {
                transition: all 0.3s ease;
            }
            .stop-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            }
            .gradient-bg {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }
            .glass-effect {
                background: rgba(255, 255, 255, 0.9);
                backdrop-filter: blur(10px);
            }
        </style>
    </head>
    <body class="bg-gray-50 min-h-screen">
        <!-- Navigation -->
        <nav class="gradient-bg text-white shadow-lg">
            <div class="container mx-auto px-4 py-3">
                <div class="flex items-center justify-between">
                    <a href="index.html" class="flex items-center space-x-2">
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
            <div class="bg-white rounded-lg shadow-lg p-6 mb-8">
                <div class="flex items-center justify-between">
                    <div>
                        <h1 class="text-4xl font-bold text-gray-800">Route {{ route_short_name }}</h1>
                        <p class="text-lg text-gray-600">{{ route_long_name }}</p>
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
                        <div class="space-y-3">
                            {% for stop in stops %}
                            <div class="stop-card bg-gray-50 rounded-lg p-4 cursor-pointer"
                                 onclick="highlightStop({{ stop.lat }}, {{ stop.lon }}, '{{ stop.name|replace("'", "\\'") }}')">
                                <div class="flex items-center">
                                    <span class="w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center mr-4 flex-shrink-0">
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
            const routeLine = L.polyline(coordinates, {color: '#3B82F6', weight: 3}).addTo(map);

            // Fit map to route bounds
            map.fitBounds(routeLine.getBounds(), {padding: [50, 50]});

            // Function to highlight stop on map
            function highlightStop(lat, lon, name) {
                map.setView([lat, lon], 16);
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

    # HTML template for index page
    index_template = Template("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Transit Routes Explorer</title>
        <link href="https://cdn.tailwindcss.com" rel="stylesheet">
        <style>
            .route-card {
                transition: all 0.3s ease;
            }
            .route-card:hover {
                transform: translateY(-4px);
            }
            .gradient-bg {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }
        </style>
    </head>
    <body class="bg-gray-50 min-h-screen">
        <!-- Header -->
        <header class="gradient-bg text-white py-12">
            <div class="container mx-auto px-4">
                <h1 class="text-4xl font-bold mb-2">Transit Routes Explorer</h1>
                <p class="text-xl opacity-90">Discover and explore public transportation routes</p>
            </div>
        </header>

        <!-- Main Content -->
        <main class="container mx-auto px-4 py-8">
            <!-- Stats -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div class="bg-white rounded-lg shadow-lg p-6 text-center">
                    <h3 class="text-lg text-gray-600">Total Routes</h3>
                    <p class="text-3xl font-bold text-gray-800">{{ routes|length }}</p>
                </div>
                <!-- Add more stats here if needed -->
            </div>

            <!-- Routes Grid -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {% for route in routes %}
                <a href="route_{{ route.route_short_name }}.html"
                   class="route-card block">
                    <div class="bg-white rounded-lg shadow-lg p-6 h-full">
                        <div class="flex items-center justify-between mb-4">
                            <span class="text-2xl font-bold text-gray-800">Route {{ route.route_short_name }}</span>
                            <span class="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                                {% if route.route_type == '3' %}
                                Bus
                                {% elif route.route_type == '2' %}
                                Train
                                {% elif route.route_type == '0' %}
                                Tram
                                {% else %}
                                Other
                                {% endif %}
                            </span>
                        </div>
                        <p class="text-gray-600">{{ route.route_long_name }}</p>
                    </div>
                </a>
                {% endfor %}
            </div>
        </main>

        <!-- Footer -->
        <footer class="bg-gray-800 text-white py-8 mt-12">
            <div class="container mx-auto px-4 text-center">
                <p>Created with ❤️ using GTFS data</p>
            </div>
        </footer>
    </body>
    </html>
    """)

    # Generate individual route pages
    for _, route in routes_df.iterrows():
        route_short_name = route['route_short_name']
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
                stop = stops_df[stops_df['stop_id'] == stop_time['stop_id']].iloc[0]
                stops_info.append({
                    'sequence': int(stop_time['stop_sequence']),
                    'name': stop['stop_name'],
                    'lat': float(stop['stop_lat']),
                    'lon': float(stop['stop_lon'])
                })

            # Generate HTML
            html_content = route_template.render(
                route_short_name=route_short_name,
                route_long_name=route['route_long_name'],
                route_type=route['route_type'],
                agency_id=route['agency_id'],
                stops=stops_info,
                stops_json=json.dumps(stops_info)
            )

            # Save HTML file
            with open(f"{output_dir}/route_{route_short_name}.html", 'w', encoding='utf-8') as f:
                f.write(html_content)

    # Generate index page
    index_html = index_template.render(routes=routes_df.to_dict('records'))
    with open(f"{output_dir}/index.html", 'w', encoding='utf-8') as f:
        f.write(index_html)

    print(f"\nGenerated {len(routes_df)} route pages and index page in '{output_dir}' directory")

if __name__ == "__main__":
    # Example usage
    gtfs_path = "israel-public-transportation"
    generate_stylish_route_pages(gtfs_path)