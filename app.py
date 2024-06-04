from flask import Flask, request, Response
from taxi_ops_backend.database_management import DatabaseManagement
from taxi_ops_backend.taxi_driver_management import create_multiple_drivers, register_drivers_with_taxis, set_taxis_drivers_ready,test_create_50_taxis,register_multiple_taxis_drivers, register_multiple_taxis_drivers
from bson import json_util
import logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/register_user', methods=['POST'])
def register_user_endpoint():
    # data = request.json()
    data = request.get_json()
    name = data['name']
    email_id = data['email_id']
    phone_number = data['phone_number']
    # Add your logic to process the data and register the user
    # response = {
    #     "status": "success",
    #     "message": "User initial response"
    # }
    # return jsonify(response)

    if 'name' not in data or 'email_id' not in data or 'phone_number' not in data:
        # return jsonify({'error': 'Missing required fields'}), 400
        # return response({"message": "Missing required parameters"}, status=400, mimetype='application/json')
        return Response(json_util.dumps({"message": "Missing required parameters"}), status=400, mimetype='application/json')
    try:
        # result = register_user(name, email_id, phone_number)
        result = DatabaseManagement().create_user(user_name=name, email_id=email_id, phone_number=phone_number)
        # return jsonify({'message': 'User registered successfully try flow', 'data': result}), 201
        return Response(json_util.dumps({"message": result}), status=200, mimetype='application/json')
    except Exception as e:
        # return jsonify({'error': str(e)}), 500
        return Response(json_util.dumps({"message": str(e)}), status=500, mimetype='application/json')


@app.route('/register_taxi', methods=['POST'])
def register_taxi_endpoint():
    data = request.get_json()
    taxi_type = data['taxi_type']
    taxi_number = data['taxi_number']

    if 'taxi_type' not in data or 'taxi_number' not in data:
        return Response(json_util.dumps({"message": "Missing required parameters"}), status=400, mimetype='application/json')
    try:
        logging.debug(f"Calling test_create_50_taxis with taxi_type={taxi_type}, taxi_number={taxi_number}")
        data_taxis = test_create_50_taxis(1, taxi_type= taxi_type, taxi_number=taxi_number)
        result = register_multiple_taxis_drivers("Taxis", data_taxis, "location")

        logging.debug("Calling create_multiple_drivers with count=1")
        data_drivers = create_multiple_drivers(count=1)
        register_multiple_taxis_drivers("Drivers", data_drivers, "")

        logging.debug("Calling register_drivers_with_taxis")
        register_drivers_with_taxis()

        logging.debug("Calling set_taxis_drivers_ready")
        set_taxis_drivers_ready()

        return Response(json_util.dumps({"message": result}), status=200, mimetype='application/json')
    except Exception as e:
        return Response(json_util.dumps({"message": str(e)}), status=500, mimetype='application/json')

if __name__ == "__main__":
    app.run(debug=True)