import requests
import random
import time
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

# Define the boundary
BOUNDARY = {
    'min_lat': 8.0,
    'max_lat': 37.0,
    'min_lon': 68.0,
    'max_lon': 97.0
}

# API endpoint
API_URL = "https://example.com/update_location"

# Taxi details
TAXI_ID = "taxi_123"
taxi_status = "available"  # Initial status of the taxi

# User details
USER_EMAIL = "user@example.com"

# Initial taxi location
taxi_location = {
    'latitude': random.uniform(BOUNDARY['min_lat'], BOUNDARY['max_lat']),
    'longitude': random.uniform(BOUNDARY['min_lon'], BOUNDARY['max_lon'])
}

# Movement step size
STEP_SIZE = 0.01

# AWS SNS client
sns_client = boto3.client('sns', region_name='us-east-1')  # Change region as needed

def update_taxi_location(taxi_id, location):
    """
    Send a POST request to update the taxi location.
    :param taxi_id: ID of the taxi
    :param location: Dictionary with 'latitude' and 'longitude'
    """
    payload = {
        'taxi_id': taxi_id,
        'location': location
    }
    try:
        response = requests.post(API_URL, json=payload)
        if response.status_code == 200:
            print(f"Successfully updated location: {location}")
        else:
            print(f"Failed to update location. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error updating location: {e}")

def book_ride(taxi_id, user_email):
    """
    Book a ride and send a confirmation email via SNS.
    :param taxi_id: ID of the taxi
    :param user_email: Email of the user
    """
    global taxi_status
    if taxi_status == "available":
        taxi_status = "busy"
        message = f"Your ride with taxi {taxi_id} has been confirmed."
        try:
            sns_client.publish(
                TopicArn='arn:aws:sns:us-east-1:123456789012:YourSNSTopic',  # Replace with your SNS topic ARN
                Message=message,
                Subject='Ride Booking Confirmation',
                MessageAttributes={
                    'email': {
                        'DataType': 'String',
                        'StringValue': user_email
                    }
                }
            )
            print(f"Booking confirmation sent to {user_email}")
        except (NoCredentialsError, PartialCredentialsError) as e:
            print(f"AWS credentials error: {e}")
        except Exception as e:
            print(f"Error sending SNS message: {e}")
    else:
        print("Taxi is already busy. Cannot book the ride.")

def simulate_taxi_movement():
    global taxi_location
    direction = [STEP_SIZE, STEP_SIZE]  # Initial direction

    while True:
        # Update location
        taxi_location['latitude'] += direction[0]
        taxi_location['longitude'] += direction[1]

        # Boundary check and bounce back logic
        if taxi_location['latitude'] > BOUNDARY['max_lat'] or taxi_location['latitude'] < BOUNDARY['min_lat']:
            direction[0] = -direction[0]  # Reverse latitude direction
        if taxi_location['longitude'] > BOUNDARY['max_lon'] or taxi_location['longitude'] < BOUNDARY['min_lon']:
            direction[1] = -direction[1]  # Reverse longitude direction

        # Ensure location is within boundary after bounce back
        taxi_location['latitude'] = max(min(taxi_location['latitude'], BOUNDARY['max_lat']), BOUNDARY['min_lat'])
        taxi_location['longitude'] = max(min(taxi_location['longitude'], BOUNDARY['max_lon']), BOUNDARY['min_lon'])

        # Update location via API
        update_taxi_location(TAXI_ID, taxi_location)

        # Sleep for a while before the next update
        time.sleep(1)

if __name__ == "__main__":
    simulate_taxi_movement()