from pymongo import MongoClient
import folium
import certifi
import time
from folium.plugins import TimestampedGeoJson

# MongoDB connection
DB_URI = "mongodb+srv://mogodbcloud:UYWhDW9VEOoYoEjf@mongodbcloudcluster.1l4vovv.mongodb.net/" \
            "?retryWrites=false"
client = MongoClient(DB_URI,tlsCAFile=certifi.where())
db = client["ProjectTaxi"]

# Collections
taxis_collection = db["Taxis"]
users_collection = db["Users"]

# Fetch data
taxis = list(taxis_collection.find({}))
users = list(users_collection.find({}))

# Debugging: Print the structure of the first taxi document
# if taxis:
#     print(taxis[0])

# Debugging: Print the structure of the first few taxi documents
# for i, taxi in enumerate(taxis[:5]):  # Print the first 5 taxis
#     print(f"Taxi {i}: {taxi}")


# Initialize the map centered at a specific location (e.g., Bangalore)
m = folium.Map(location=[12.9716, 77.5946], zoom_start=11)

# folium MAP Define color mapping for taxi status and type
# {'pink', 'gray', 'darkpurple', 'darkred', 'lightgreen',
# 'lightgray', 'lightred', 'black', 'orange', 'red', 'cadetblue',
# 'blue', 'green', 'darkblue', 'beige', 'lightblue', 'white', 'purple',
# 'darkgreen'}.

status_color_mapping = {
    'available': 'green',  # Green# Taxis that are available for hire
    'not operational': 'red',  # Red# Taxis that are not in service
    'on-duty': 'orange',  # Orange# Taxis that are on duty but not currently occupied
    'occupied': 'purple'  # white# Taxis that are currently occupied with passengers
}

type_color_mapping = {
    'basic': 'blue',  # Blue # Basic service taxis
    'deluxe': 'pink',  # Pink # Deluxe service taxis
    'luxury': 'white'  # White # Luxury service taxis
}

# Add taxi locations
for taxi in taxis:
    location = taxi.get('location', {})
    if isinstance(location, dict):
        coordinates = location.get('coordinates', [])
        if len(coordinates) == 2:
            longitude, latitude = coordinates
            # print(f"Taxi ID: {taxi.get('id', 'N/A')} - Coordinates: {latitude}, {longitude}")  # Debugging print
            # Determine color based on status and type
            status_color = status_color_mapping.get(taxi.get('status', '').lower(), 'purple')
            type_color = type_color_mapping.get(taxi.get('taxi_type', '').lower(), 'beige')
            color = status_color if taxi.get('status', '').lower() == 'available' else type_color

            # Create a detailed popup
            popup_html = f"""
                        <b>Taxi ID:</b> {taxi.get('_id', 'N/A')}<br>
                        <b>Status:</b> {taxi.get('status', 'N/A')}<br>
                        <b>Type:</b> {taxi.get('taxi_type', 'N/A')}<br>
                        <b>Driver:</b> {taxi.get('driver_id', 'N/A')}<br>
                        <b>Coordinates:</b> {longitude}, {latitude}
                        """
            # popup = folium.Popup(folium.IFrame(popup_html, width=300, height=150), max_width=300)
            popup = folium.Popup(popup_html, max_width=300)

            # Define the boundary coordinates
            boundary_coords = [
                [12.834, 77.491],  # Bottom-left
                [12.834, 77.861],  # Bottom-right
                [13.139, 77.861],  # Top-right
                [13.139, 77.491],  # Top-left
                [12.834, 77.491]  # Closing the loop to bottom-left
            ]
            # Draw the boundary
            folium.Polygon(
                locations=boundary_coords,
                color='blue',
                weight=2
            ).add_to(m)

            folium.CircleMarker(
                location=[latitude, longitude],
                radius=10,
                color=type_color,  # Border color
                fill=True,
                fill_color=status_color,  # Fill color
                fill_opacity=0.7,
                # popup=f"Status: {taxi['status']}, Type: {taxi['taxi_type']}"
                popup = popup
            ).add_to(m)
        else:
            print(f"Unexpected coordinates format: {coordinates}")
    else:
        print(f"Unexpected location format: {location}")

# Add user locations
for user in users:
    location = user.get('location', {})
    if isinstance(location, dict):
        coordinates = location.get('coordinates', [])
        if len(coordinates) == 2:
            longitude, latitude = coordinates
            # Create a detailed popup
            popup_html = f"""
                       <b>User ID:</b> {user.get('_id', 'N/A')}<br>
                       <b>Name:</b> {user.get('user_name', 'N/A')}<br>
                       <b>Coordinates:</b> {longitude}, {latitude}
                       """
            popup = folium.Popup(popup_html, max_width=300)

            folium.Marker(
                location=[latitude, longitude],
                icon=folium.Icon(color='green'),
                popup = popup
            ).add_to(m)
        else:
            print(f"Unexpected coordinates format: {coordinates}")
    else:
        print(f"Unexpected location format: {location}")

# Save the map to an HTML file
m.save('map.html')