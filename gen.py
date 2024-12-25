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
        output_dir = "docs/route_pages"




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
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <!-- Primary Meta Tags -->
    <title>קו {{ route_short_name }} - {{ route_long_name }} | MooveFree</title>
    <meta name="title" content="קו {{ route_short_name }} - {{ route_long_name }} | MooveFree">
    <meta name="description" content="מידע על קו {{ route_short_name }}: {{ route_long_name }}. צפו במפת המסלול, תחנות, וזמני נסיעה.">

    <!-- Open Graph / Facebook -->
    <meta property="og:type" content="website">
    <meta property="og:url" content="{{ current_url }}">
    <meta property="og:title" content="קו {{ route_short_name }} - {{ route_long_name }}">
    <meta property="og:description" content="מידע על קו {{ route_short_name }}: {{ route_long_name }}. צפו במפת המסלול, תחנות, וזמני נסיעה.">
    <meta property="og:image" content="https://dorpascal.com/MooveFree/assets/og-image.png">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta property="og:image:alt" content="MooveFree Logo">
    <meta property="og:site_name" content="MooveFree">
    <meta property="og:locale" content="he_IL">
    <meta name="theme-color" content="#2d3748">
    <meta name="apple-mobile-web-app-status-bar-style" content="#2d3748">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-title" content="MooveFree">
    <meta name="application-name" content="MooveFree">
    <meta name="msapplication-TileColor" content="#2d3748">
    <meta name="apple-itunes-app" content="app-id=6736739283">
    <!-- Twitter -->
    <meta property="twitter:card" content="summary_large_image">
    <meta property="twitter:url" content="{{ current_url }}">
    <meta property="twitter:title" content="קו {{ route_short_name }} - {{ route_long_name }}">
    <meta property="twitter:description" content="מידע על קו {{ route_short_name }}: {{ route_long_name }}. צפו במפת המסלול, תחנות, וזמני נסיעה.">
    <meta property="twitter:image" content="https://dorpascal.com/MooveFree/assets/og-image.png">

    <!-- Favicon -->
    <link rel="icon" type="image/svg+xml" href="../assets/favicon.svg">
    <link rel="alternate icon" type="image/png" href="../assets/favicon.png">

    <!-- Stylesheets -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css" rel="stylesheet">
    <link href="../assets/styles.css" rel="stylesheet">

    <!-- Schema.org markup for Google -->
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "BusTrip",
        "name": "קו {{ route_short_name }}",
        "description": "{{ route_long_name }}",
        "provider": {
            "@type": "Organization",
            "name": "תחבורה ציבורית בישראל"
        },
        "itinerary": {
            "@type": "ItemList",
            "itemListElement": [
                {% for stop in stops %}
                {
                    "@type": "BusStop",
                    "name": "{{ stop.name }}",
                    "geo": {
                        "@type": "GeoCoordinates",
                        "latitude": {{ stop.lat }},
                        "longitude": {{ stop.lon }}
                    }
                }{% if not loop.last %},{% endif %}
                {% endfor %}
            ]
        }
    }
    </script>
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "בית",
                "item": "https://dorpascal.com/"
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": "קווים",
                "item": "https://dorpascal.com/MooveFree/"
            },
            {
                "@type": "ListItem",
                "position": 3,
                "name": "קו {{ route_short_name }}"
            }
        ]
    }
    </script>
    <!-- Google Tag Manager -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-T7HFKFX0PR"></script>
    <script>
        window.dataLayer = window.dataLayer || [];
        function gtag() { dataLayer.push(arguments); }
        gtag('js', new Date());
        gtag('config', 'G-T7HFKFX0PR');
    </script>
    <!-- End Google Tag Manager -->
</head>
<body>
    <!-- Navigation -->
    <nav class="transit-nav" aria-label="ניווט ראשי">
        <div class="transit-container">
            <div class="transit-nav-content">
                <a href="../" class="transit-nav-back" aria-label="חזרה לכל הקווים">
                    <svg xmlns="http://www.w3.org/2000/svg" class="icon-back" viewBox="0 0 24 24" aria-hidden="true">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19l-7-7 7-7" />
                    </svg>
                    <span>כל הקווים</span>
                </a>
                <span class="transit-nav-brand">MooveFree - תחבורה ציבורית בישראל</span>
            </div>
        </div>
    </nav>

    <!-- Main Content -->
    <main class="transit-container" role="main">
        <!-- Route Header -->
        <div class="transit-card route-header">
            <h1 class="route-title">
                קו {{ route_short_name }}
                <span class="route-type-badge" aria-label="סוג תחבורה">
                    {% if route_type == '3' %}אוטובוס
                    {% elif route_type == '2' %}רכבת
                    {% elif route_type == '0' %}רכבת קלה
                    {% else %}אחר{% endif %}
                </span>
            </h1>
            <div class="route-subtitle">{{ route_long_name }}</div>
        </div>

        <!-- Map and Stops Grid -->
        <div class="transit-layout-main">
            <!-- Map -->
            <section class="transit-card" aria-label="מפת מסלול">
                <h2 class="route-title">מפת מסלול</h2>
                <div id="map" class="transit-map" aria-label="מפת מסלול אינטראקטיבית"></div>
            </section>

            <!-- Stops List -->
            <section class="transit-card" aria-label="רשימת תחנות">
                <h2 class="route-title">תחנות</h2>
                <div class="stops-container">
                    {% for stop in stops %}
                    <button class="stop-item"
                            onclick="highlightStop({{ stop.lat }}, {{ stop.lon }}, '{{ stop.name }}')"
                            aria-label="תחנה {{ stop.sequence }}: {{ stop.name }}">
                        <span class="stop-number">{{ stop.sequence }}</span>
                        <div class="stop-details">
                            <div class="stop-name">{{ stop.name }}</div>
                            <div class="stop-coordinates">{{ stop.lat }}, {{ stop.lon }}</div>
                        </div>
                    </button>
                    {% endfor %}
                </div>
            </section>
        </div>
    </main>

    <!-- Footer -->
    <footer class="transit-footer">
        <div class="transit-container">
            <p>© {{ current_year }} MooveFree by <a href="https://dorpascal.com" target="_blank" rel="noopener">Dor Pascal</a></p>
        </div>
    </footer>

    <!-- Scripts -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js"></script>
    <script>
        // Initialize map
        const map = L.map('map', {
            scrollWheelZoom: false // Disable scroll zoom for better mobile experience
        });

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);

        // Add stops to map
        const stops = {{ stops_json|safe }};
        const markers = [];
        const coordinates = stops.map(stop => [stop.lat, stop.lon]);

        stops.forEach(stop => {
            const marker = L.marker([stop.lat, stop.lon])
                .bindPopup(`<strong>${stop.sequence}. ${stop.name}</strong>`, {
                    direction: 'rtl',
                    className: 'rtl-popup'
                })
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
                if os.path.exists(f"{output_dir}/route_{route_short_name}.html"):
                    print(f"Page for route {route_short_name} already exists. Skipping...")
                    continue
                print(f"Generating page for route {route_short_name}...")

                # Get trips for this route
                route_trips = trips_df[trips_df['route_id'] == route['route_id']]

                if not route_trips.empty:
                    # Get first trip's stops
                    first_trip = route_trips.iloc[0]
                    trip_stops = stop_times_df[stop_times_df['trip_id'] == first_trip['trip_id']].sort_values('stop_sequence')
                    # if page already exists, skip

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
                        stops_json=json.dumps(stops_info),
                        current_url=f"https://dorpascal.com/MooveFree/route_pages/route_{route_short_name}",
                        current_year=datetime.now().year
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