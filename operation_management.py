import json

API
5.
From the above user choose one taxi
Book the ride. Basic: give a message to the user. SNS: add-on: Send
notification to user: sns ???
API for book ride:
    Input: taxi ID, user ID, user location.
Output: make the booking confirmation. Json output.
Optional: Push to SNS to the email id of the user.
Taxi status is updated as a busy
Taxi is booked. Stop the movement of the taxi."""This is the service layer which is exposed using API gateway.
This should go in lambda
"""
from taxi_ops_backend.database_management import DatabaseManagement


def define_boundary_location(city: str,
                             left_bottom: (float, float),
                             left_top: (float, float),
                             right_top: (float, float),
                             right_bottom: (float, float)):
    """
    define city operation boundary
    @param city:
    @param left_bottom:
    @param left_top:
    @param right_top:
    @param right_bottom:
    @return:
    """
    return DatabaseManagement().create_operation_bound(city, left_bottom,
                                                       left_top,
                                                       right_top,
                                                       right_bottom)

def update_taxi_status(taxi_id, status):
    """
    Update the status of a taxi.
    :param taxi_id: str
    :param status: str
    :return: bool
    """
    return DatabaseManagement().update_taxi_status(taxi_id=taxi_id, status=status)

def send_notification(email, message):
    """
    Send an email notification using AWS SNS.
    :param email: str
    :param message: str
    :return: dict
    """
    response = sns_client.publish(
        TopicArn='arn:aws:sns:us-east-1:123456789012:xyz',  # Replace with your SNS Topic ARN
        Message=message,
        Subject='Taxi Booking Confirmation'
    )
    return response


def get_operation_boundary(city):
    """
    get operation boundary polygon
    @param city:
    @return:
    """
    return DatabaseManagement().get_operation_bound(city=city)

def book_ride(event, context):
    """
    Book a ride for the user. This function is intended to be deployed as an AWS Lambda function.
    :param event: dict
    :param context: Lambda context object
    :return: dict
    """
    taxi_id = event.get('taxi_id')
    user_id = event.get('user_id')
    user_location = event.get('user_location')
    city = event.get('city')

    if not taxi_id or not user_id or not user_location or not city:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing required parameters"})
        }

    # Fetch the user and taxi details
    user = DatabaseManagement().get_user(user_id)
    taxi = DatabaseManagement().get_taxi(taxi_id)

    if not user or not taxi:
        return {
            "statusCode": 404,
            "body": json.dumps({"error": "User or Taxi not found"})
        }

    # Check if the location is within the city boundary
    if not DatabaseManagement().taxi_within_boundary(city, user_location['latitude'], user_location['longitude']):
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Location is outside the operation boundary"})
        }

    # Check if the taxi is available
    if taxi['status'] != 'available':
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Taxi is not available"})
        }

    # Update the taxi status to busy
    update_taxi_status(taxi_id, 'busy')

    # Create the booking record
    booking = DatabaseManagement().create_booking(user_id=user_id, taxi_id=taxi_id, user_location=user_location)

    # Prepare the confirmation message
    confirmation_message = f"Booking confirmed! Taxi ID: {taxi_id}, User ID: {user_id}, Location: {user_location}"

    # Send the notification to the user's email
    notification_response = send_notification(user['email_id'], confirmation_message)

    # Prepare the JSON response
    response = {
        "message": "Taxi booked successfully",
        "booking_details": {
            "taxi_id": taxi_id,
            "user_id": user_id,
            "location": user_location,
            "confirmation_message": confirmation_message
        },
        "notification_response": notification_response
    }

    return {
        "statusCode": 200,
        "body": json.dumps(response)
    }



# Uncomment for the following to create a boundry and get the operation boundry.

if __name__ == "__main__":
    # Define the Boundary Coordinates for Bangalore
    # For simplicity, let's define a rectangular boundary around Bangalore:
    # Define the boundary for Bangalore
    # city = "Bangalore"
    # Left Bottom (South-West): (12.834, 77.491)
    # Left Top (North-West): (13.139, 77.491)
    # Right Top (North-East): (13.139, 77.861)
    # Right Bottom (South-East): (12.834, 77.861)
    #
    # city = "Bangalore"
    # left_bottom = (12.834, 77.491)
    # left_top = (13.139, 77.491)
    # right_top = (13.139, 77.861)
    # right_bottom = (12.834, 77.861)
    # #
    # MongoDB Atlas
    # [77.491, 12.834],  # Bottom-left
    # [77.861, 12.834],  # Bottom-right
    # [77.861, 13.139],  # Top-right
    # [77.491, 13.139],  # Top-left
    # [77.491, 12.834]  # Closing the loop to bottom-left
    # result = define_boundary_location(city, left_bottom, left_top, right_top, right_bottom)
    # print(result)

    # # Get the operations boundry : SUCCESS [[12.834, 77.491], [13.139, 77.491], [13.139, 77.861], [12.834, 77.861]]
    # city = "Bangalore"
    # result = get_operation_boundary(city)
    # print(result)

    # # Book a taxi within the boundary Taxi booked successfully
    # city = "Bangalore"
    # latitude = 12.9716
    # longitude = 77.5946
    # result = DatabaseManagement().taxi_within_boundary(city, latitude, longitude)
    # # Return that it iw w/n boundry range.
    # print(result)


    #
    # # Attempt to book a taxi outside the boundary Verify the exception message [ValueError: Location is outside the operation boundary]
    city = "Bangalore"
    latitude = 13.00
    longitude = 77.861
    result = DatabaseManagement().taxi_within_boundary(city, latitude, longitude)
    print(result)