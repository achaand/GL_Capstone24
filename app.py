from flask import Flask, request, Response
from data_operations import DatabaseManagement
# from taxi_ops_backend.taxi_driver_management import create_multiple_drivers, register_drivers_with_taxis, set_taxis_drivers_ready,test_create_50_taxis,create_multiple_users, register_multiple_taxis_drivers,filter_taxis_by_type, book_and_initiate_trip,update_taxi_location, update_user_location, taxi_start_trip, taxi_end_trip
from taxi_driver_management import *
from bson import json_util
import logging
logging.basicConfig(level=logging.DEBUG)
import boto3

# SNS Topic ARN
SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:587455824571:TaxiCoOpAWSSNS'

app = Flask(__name__)

def send_sns_notification(topic_arn, message):
    sns_client = boto3.client('sns')
    try:
        response = sns_client.publish(
            TopicArn=topic_arn,
            Message=message
        )
        return response
    except Exception as e:
        logging.error(f"Failed to send SNS notification: {str(e)}")
        return None

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/define_boundary', methods=['POST'])
def define_boundary():
    data = request.get_json()
    city = data['city']
    boundary = data['boundary']
    if len(boundary) != 4:
        return Response(json_util.dumps({"ERROR: Boundary must have exactly 4 points": boundary}), status=400, mimetype='application/json')

    left_bottom, left_top, right_top, right_bottom = boundary
    created_boundary = DatabaseManagement().create_operation_bound(city=city, left_bottom= left_bottom, left_top= left_top, right_top = right_top, right_bottom=right_bottom)
    send_sns_notification(SNS_TOPIC_ARN, f"Boundry for {city} has been defined.")
    return Response(json_util.dumps({"message""Boundary defined successfully": created_boundary}), status=200, mimetype='application/json')

@app.route('/register_user', methods=['POST'])
def register_user_endpoint():
    data = request.get_json()
    name = data['name']
    email_id = data['email_id']
    phone_number = data['phone_number']
    location = data.get('location')
    city = location.get('city')

    if not name or not email_id or not location or not phone_number or not city:
        return Response(json_util.dumps({"message": "Missing required parameters"}), status=400, mimetype='application/json')
    try:
        # Extract latitude and longitude
        latitude = location.get('latitude')
        longitude = location.get('longitude')

        if not city or latitude is None or longitude is None:
            return Response(json_util.dumps({"ERROR": "City, latitude, and longitude are required in location"}),
                            status=400, mimetype='application/json')

        # Check if the user provided location is within the boundary
        if not DatabaseManagement().taxi_within_boundary(city, latitude, longitude):
            return Response(json_util.dumps({"ERROR": "User Location is outside the operation boundary"}), status=400,
                            mimetype='application/json')
        logging.debug(f"Calling create_multiple_users with user name={name}, email_id={email_id}")
        provided_loc = [longitude,latitude]
        data_multiple_users = create_multiple_users(count=1, name=name, email= email_id, phone= phone_number,location= provided_loc )
        register_multiple_taxis_drivers("Users", data_multiple_users, "location")
        send_sns_notification(SNS_TOPIC_ARN, f"SNS TaxiCoOpAWSSNS: User {name} is created.")

        return Response(json_util.dumps({"message : User Created": data_multiple_users}), status=200, mimetype='application/json')
    except Exception as e:
        return Response(json_util.dumps({"message": str(e)}), status=500, mimetype='application/json')


@app.route('/register_taxi', methods=['POST'])
def register_taxi_endpoint():
    data = request.get_json()
    taxi_type = data['taxi_type']
    taxi_number = data['taxi_number']
    location = data.get('location')

    if not taxi_type or not taxi_number or not location:
        return Response(json_util.dumps({"message": "Missing required parameters"}), status=400, mimetype='application/json')
    try:
        # Assuming 'city' is part of the location data, you may need to adjust this as per your data structure
        city = location.get('city')
        latitude = location.get('latitude')
        longitude = location.get('longitude')
        if not city or latitude is None or longitude is None:
            return Response(json_util.dumps({"ERROR": "City, latitude, and longitude are required in location"}),
                            status=400, mimetype='application/json')

        # Check if the location is within the boundary
        if not DatabaseManagement().taxi_within_boundary(city, latitude, longitude):
            return Response(json_util.dumps({"ERROR": "Taxi Location is outside the operation boundary"}), status=400,
                            mimetype='application/json')

        logging.debug(f"Calling test_create_50_taxis with taxi_type={taxi_type}, taxi_number={taxi_number}")
        provided_loc = [longitude,latitude]
        data_taxis = test_create_50_taxis(1, taxi_type= taxi_type, taxi_number=taxi_number, location=provided_loc)
        result = register_multiple_taxis_drivers("Taxis", data_taxis, "location")

        logging.debug("Calling create_multiple_drivers with count=1")
        data_drivers = create_multiple_drivers(count=1)
        register_multiple_taxis_drivers("Drivers", data_drivers, "")

        logging.debug("Calling register_drivers_with_taxis")
        register_drivers_with_taxis()

        logging.debug("Calling set_taxis_drivers_ready")
        set_taxis_drivers_ready()

        send_sns_notification(SNS_TOPIC_ARN, f"SNS TaxiCoOpAWSSNS: Taxi registered successfully {data_taxis}.")
        return Response(json_util.dumps({"message : Taxi registered successfully": data_taxis}), status=200, mimetype='application/json')
    except Exception as e:
        return Response(json_util.dumps({"message": str(e)}), status=500, mimetype='application/json')


@app.route('/find_taxi', methods=['POST'])
def find_taxi():
    data = request.get_json()

    required_fields = ['user_current_location', 'requested_taxi_type', 'max_distance', 'max_number_of_taxi', 'user_id',
                       'destination_location']

    for field in required_fields:
        if field not in data:
            return Response(json_util.dumps({"message": f"Missing required parameter: {field}"}), status=400,
                            mimetype='application/json')

    try:
        user_current_location = data['user_current_location']
        requested_taxi_type = data['requested_taxi_type']
        max_distance = data['max_distance']
        max_number_of_taxi = data['max_number_of_taxi']
        user_id = data['user_id']
        destination_location = data['destination_location']

        if not isinstance(user_current_location, dict) or 'coordinates' not in user_current_location:
            return Response(
                json_util.dumps({"message": "user_current_location must be a dictionary with 'coordinates'"}),
                status=400, mimetype='application/json')

        if not isinstance(destination_location, dict) or 'coordinates' not in destination_location:
            return Response(
                json_util.dumps({"message": "destination_location must be a dictionary with 'coordinates'"}),
                status=400, mimetype='application/json')

        if not isinstance(user_current_location['coordinates'], list) or len(user_current_location['coordinates']) != 2:
            return Response(json_util.dumps(
                {"message": "user_current_location coordinates must be a list with exactly 2 elements"}), status=400,
                            mimetype='application/json')

        if not isinstance(destination_location['coordinates'], list) or len(destination_location['coordinates']) != 2:
            return Response(
                json_util.dumps({"message": "destination_location coordinates must be a list with exactly 2 elements"}),
                status=400, mimetype='application/json')

        # Find nearest taxis
        nearest_taxis = DatabaseManagement().find_nearest_taxi(user_current_location, max_distance, max_number_of_taxi)

        if not nearest_taxis:
            return Response(json_util.dumps({"message": "No taxis found within the specified distance"}), status=404,
                            mimetype='application/json')

        available_taxis = [taxi for taxi in nearest_taxis if taxi.status == 'Available']
        if not available_taxis:
            return Response(json_util.dumps({"message": "No Available taxis found within the specified distance"}), status=404,
                            mimetype='application/json')

        # Filter taxis by requested type
        # filtered_taxis = filter_taxis_by_type(available_taxis, requested_taxi_type)
        # filtered_taxis = [taxi for taxi in available_taxis if taxi['type'] == requested_taxi_type]
        filtered_taxis = [taxi for taxi in available_taxis if taxi.taxi_type == requested_taxi_type]

        if not filtered_taxis:
            return Response(json_util.dumps({"message": f"No {requested_taxi_type} taxis available"}), status=404,
                            mimetype='application/json')

        # Prepare the response with multiple taxis
        taxis_response = [{"taxi_id": str(taxi.taxi_id), "taxi_type": str(taxi.taxi_type), "location": taxi.location} for taxi in filtered_taxis]

        send_sns_notification(SNS_TOPIC_ARN, f"SNS TaxiCoOpAWSSNS: Taxis available of Type {requested_taxi_type}.")

        return Response(json_util.dumps({"message": f"Taxis available of Type {requested_taxi_type}", "taxis": taxis_response}),
            status=200, mimetype='application/json')

    except Exception as e:
        return Response(json_util.dumps({"message: From the find_taxi ": str(e)}), status=500, mimetype='application/json')


@app.route('/book_and_initiate_trip', methods=['POST'])
def book_and_initiate_trip_endpoint():
    try:
        data = request.get_json()

        if not data:
            return Response(json_util.dumps({"message": "Request data is missing or not in JSON format"}), status=400,
                            mimetype='application/json')
        taxi_id = data.get('taxi_id')
        user_id = data.get('user_id')
        user_current_location = data.get('user_current_location')
        destination_location = data.get('destination_location')

        if not all([taxi_id, user_id, user_current_location, destination_location]):
            return Response(json_util.dumps({"message": "Missing required fields"}), status=400,
                            mimetype='application/json')

        # OPTIONAL Check if the location is within the boundary
        # if not DatabaseManagement().taxi_within_boundary(city, latitude, longitude):
        #     return Response(json_util.dumps({"ERROR": "Taxi Location is outside the operation boundary"}),
        #                     status=400,
        #                     mimetype='application/json')

        # Interchange coordinates to [longitude, latitude] for MogoDB
        latitude, longitude = user_current_location['coordinates']
        user_current_location['coordinates'] = [longitude, latitude]
        latitude, longitude = destination_location['coordinates']
        destination_location['coordinates'] = [longitude, latitude]

        trip_id = book_and_initiate_trip(taxi_id, user_id, user_current_location,
                                                              destination_location)
        send_sns_notification(SNS_TOPIC_ARN, f"NS TaxiCoOpAWSSNS:Trip {trip_id} has been booked and initiated.")

        return Response(json_util.dumps({"message": "Trip booked successfully", "trip_id": user_id}), status=200,
                        mimetype='application/json')

    except ValueError as ve:
        return Response(json_util.dumps({"message": str(ve)}), status=404, mimetype='application/json')
    except Exception as e:
        send_sns_notification(SNS_TOPIC_ARN, f"SNS TaxiCoOpAWSSNS: Error booking and initiating trip for user {trip_id}: {str(e)}")
        return Response(json_util.dumps({"message": str(e)}), status=500, mimetype='application/json')

@app.route('/taxi_simulator', methods=['POST'])
def taxi_simulator():
    try:
        count = request.json.get('count', 1)
        data_taxis = test_create_50_taxis(count=count, taxi_type="", taxi_number="", location="")
        result = register_multiple_taxis_drivers("Taxis", data_taxis, "location")

        data_drivers = create_multiple_drivers(count=count-5)
        register_multiple_taxis_drivers("Drivers", data_drivers, "")
        register_drivers_with_taxis()
        set_taxis_drivers_ready()

        send_sns_notification(SNS_TOPIC_ARN, f"SNS TaxiCoOpAWSSNS: Taxis created successfully {data_taxis}.")
        return Response(json_util.dumps({"message": " Taxis created successfully", "taxis:": data_taxis}), status=200,
                        mimetype='application/json')
    except Exception as e:
        return Response(json_util.dumps({"message": str(e)}), status=500, mimetype='application/json')

@app.route('/user_simulator', methods=['POST'])
def user_simulator():
    try:
        count = request.json.get('count', 1)
        data_users = create_multiple_users(count=count, name="", email="", phone="", location="")
        result = register_multiple_taxis_drivers("Users", data_users, "location")

        send_sns_notification(SNS_TOPIC_ARN, f"SNS TaxiCoOpAWSSNS: Users created successfully {data_users}.")
        return Response(json_util.dumps({"message": " Users created successfully", "Users:": data_users}), status=200,
                        mimetype='application/json')
    except Exception as e:
        return Response(json_util.dumps({"message": str(e)}), status=500, mimetype='application/json')

@app.route('/update-taxi-location', methods=['POST'])
def update_taxi_location_route():
    try:
        data = request.get_json()
        v_taxi_id = data.get('v_taxi_id')
        v_location = data.get('v_location')

        if not v_taxi_id or not v_location:
            raise ValueError("v_taxi_id and v_location are required")

        result = update_taxi_location(v_taxi_id, v_location)
        send_sns_notification(SNS_TOPIC_ARN, f"SNS TaxiCoOpAWSSNS: Updated Taxi Location successfully {v_location}.")

        return Response(json_util.dumps({"message": "Updated Taxi Location successfully", "Result:": v_location}), status=200,
                        mimetype='application/json')
    except ValueError as ve:
        return Response(json_util.dumps({"message": str(ve)}), status=404, mimetype='application/json')
    except Exception as e:
        return Response(json_util.dumps({"message": str(e)}), status=500, mimetype='application/json')

@app.route('/update-user-location', methods=['POST'])
def update_user_location_route():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        v_location = data.get('v_location')

        if not user_id or not v_location:
            raise ValueError("user_id and v_location are required")

        result = update_user_location(user_id, v_location)
        send_sns_notification(SNS_TOPIC_ARN, f"SNS TaxiCoOpAWSSNS: Updated User Location successfully {v_location}.")

        return Response(json_util.dumps({"message": "Updated User Location successfully", "Result:": v_location}),
                        status=200,
                        mimetype='application/json')
    except Exception as e:
        return Response(json_util.dumps({"message": str(e)}), status=500, mimetype='application/json')

@app.route('/start_trip', methods=['POST'])
def start_trip_route():
    data = request.get_json()
    taxi_id = data.get('taxi_id')
    user_id = data.get('user_id')
    current_location = data.get('current_location')
    destination_location = data.get('destination_location')

    try:
        success = taxi_start_trip(taxi_id, user_id, current_location, destination_location)
        if success:
            send_sns_notification(SNS_TOPIC_ARN, f"Trip for Taxi {taxi_id} has started.")
            return Response(json_util.dumps({"message": "Taxi is status in_progress"}),
                        status=200,
                        mimetype='application/json')
        else:
            return Response(json_util.dumps({"message: ERROR: Failed to start the trip"}), status=500, mimetype='application/json')
    except Exception as e:
        send_sns_notification(SNS_TOPIC_ARN, f"Error starting trip {taxi_id}: {str(e)}")
        return Response(json_util.dumps({"message": str(e)}), status=500, mimetype='application/json')

@app.route('/end_trip', methods=['POST'])
def end_trip_route():
    data = request.get_json()
    taxi_id = data.get('taxi_id')
    user_id = data.get('user_id')
    user_current_location = data.get('current_location')
    destination_location = data.get('destination_location')

    try:
        success = taxi_end_trip(taxi_id, user_id, user_current_location, destination_location)
        if success:
            send_sns_notification(SNS_TOPIC_ARN, f"Trip {taxi_id} has ended.")
            return Response(json_util.dumps({"message": "Taxi status is now completed"}),
                        status=200,
                        mimetype='application/json')
        else:
            return Response(json_util.dumps({"message: ERROR Failed to end the trip"}), status=500, mimetype='application/json')
    except Exception as e:
        send_sns_notification(SNS_TOPIC_ARN, f"Error ending trip: {str(e)}")
        return Response(json_util.dumps({"message": str(e)}), status=500, mimetype='application/json')


if __name__ == "__main__":
    app.run(debug=True)