# taxi_simulation.py

from pymongo import MongoClient
import time

# MongoDB setup (replace with your MongoDB connection details)
client = MongoClient('mongodb://localhost:27017/')
db = client['taxi_service']
taxis_collection = db['taxis']


# Function to generate a straight path within the boundary
def generate_straight_path_within_boundary(start, end, num_points):
    lat_diff = (end[0] - start[0]) / num_points
    lon_diff = (end[1] - start[1]) / num_points

    path = []
    for i in range(num_points):
        lat = start[0] + (i * lat_diff)
        lon = start[1] + (i * lon_diff)
        path.append([lon, lat])

    return path


# Function to update taxi location
def update_taxi_location(taxi_id, new_location):
    taxis_collection.update_one(
        {"_id": taxi_id},
        {"$set": {"location": new_location}}
    )
    return {"status": "success", "message": "Taxi location updated successfully"}


# Function to simulate taxi movement
def simulate_taxi_movement():
    # Fetch all taxis from the database
    taxis = list(taxis_collection.find({}))

    # Generate a straight path for each taxi and update their locations
    for taxi in taxis:
        taxi_id = taxi['_id']
        current_location = taxi.get('location', {}).get('coordinates', [])
        if len(current_location) == 2:
            start = current_location
            end = [13.139, 77.861]  # Example end point within the boundary
            path = generate_straight_path_within_boundary(start, end, 10)
            for coordinates in path:
                v_location = {"coordinates": coordinates}
                result = update_taxi_location(taxi_id, v_location)
                print(result)
                time.sleep(5)  # Sleep for 5 seconds to simulate time between movements