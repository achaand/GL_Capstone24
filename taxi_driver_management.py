"""
Taxi Administration. This is to be run on EC2 machine because this is
helper to the taxi ops
"""
import random

import pymongo
from taxi_ops_backend.custom_error import IllegalTaxiStatusState
from taxi_ops_backend.database_management import DatabaseManagement
from taxi_ops_backend.taxi_ops_logger import TaxiOpsLogger
from taxi_ops_backend.model import Taxi

#Added by Suraj
from pymongo.errors import ConfigurationError, OperationFailure
import time
import re
from taxi_ops_backend.database import Database
from faker import Faker

# Define the boundary coordinates
BOUNDARY_BOX = [
    [77.491, 12.834],  # Bottom-left
    [77.861, 12.834],  # Bottom-right
    [77.861, 13.139],  # Top-right
    [77.491, 13.139]   # Top-left
]

def is_within_boundary(location):
    """
    Check if the given location is within the specified boundary.
    :param location: dict with 'coordinates' key, e.g., {"coordinates": [77.5, 12.9]}
    :return: bool
    """
    lon, lat = location['coordinates']
    return BOUNDARY_BOX[0][0] <= lon <= BOUNDARY_BOX[1][0] and BOUNDARY_BOX[0][1] <= lat <= BOUNDARY_BOX[2][1]


def register_taxi(taxi_type, taxi_number, location):
    """
    doc string
    :param taxi_type:
    :param taxi_number:
    :return:
    """

    if not is_within_boundary(location):
        raise ValueError("Location is outside the allowed boundary")

    return DatabaseManagement().create_taxi(taxi_type=taxi_type, taxi_number=taxi_number, location=location)

# Added by Suraj
def register_multiple_taxis_drivers(collection, data,index_key):
    """
    doc string
    :param taxi_type:
    :param taxi_number:
    :return:
    """
    return DatabaseManagement().create_multiple_taxis_drivers(collection, data, index_key)


def register_driver(driver_name, email_id, phone_number) -> str:
    """
    doc string
    :param driver_name:
    :param email_id:
    :param phone_number:
    :return:
    """
    # try:
    #     # Validate driver name
    #     if not isinstance(driver_name, str) or not driver_name.strip():
    #         raise ValueError("Driver name must be a non-empty string")
    #
    #     # Validate email ID using a simple regex pattern
    #     email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    #     if not isinstance(email_id, str) or not re.match(email_pattern, email_id):
    #         raise ValueError("Invalid email ID format")
    #
    #     # Validate phone number (assuming a simple 10-digit format)
    #     # phone_pattern = r'^\d{10}$'
    #     # if not isinstance(phone_number, str) or not re.match(phone_pattern, phone_number):
    #     #     raise ValueError("Phone number must be a 10-digit string")
    #
    #     # Validate latitude and longitude
    #     # if not isinstance(latitude, (float, int)) or not (-90 <= latitude <= 90):
    #     #     raise ValueError("Latitude must be a number between -90 and 90")
    #     # if not isinstance(longitude, (float, int)) or not (-180 <= longitude <= 180):
    #     #     raise ValueError("Longitude must be a number between -180 and 180")
    #
    #     # Check if driver name is unique
    #     db_management = DatabaseManagement()
    #     existing_driver = db_management.find_driver_by_name(driver_name)
    #     if existing_driver:
    #         raise ValueError("Driver name must be unique")

    return DatabaseManagement().create_driver(driver_name=driver_name,
                                                  email_id=email_id,
                                                  phone_number=phone_number)

    # except pymongo.errors.OperationFailure as e:
    #     return f"Database operation failed: {e.details.get('errmsg', 'Unknown error')}"
    # except ValueError as ve:
    #     return str(ve)
    # except Exception as e:
    #     return f"An unexpected error occurred: {str(e)}"

def register_drivers_with_taxis():
    """registers driver with taxi
    :return: None
    """
    logger = TaxiOpsLogger()
    # get the required list of taxi and driver.
    unallocated_taxis = DatabaseManagement().get_taxis({"driver_id": ""})
    unallocated_drivers = DatabaseManagement().get_drivers({"taxi_assigned": False})

    # just randomise to be fair
    random.shuffle(unallocated_taxis)
    random.shuffle(unallocated_drivers)

    # now assign
    while len(unallocated_drivers) > 0 and len(unallocated_taxis) > 0:
        taxi = unallocated_taxis.pop(0)
        driver = unallocated_drivers.pop(0)
        driver.taxi_assigned = True
        taxi.driver_id = driver.driver_id
        logger.info("Now registering taxi: %s with driver: %s",
                    taxi.taxi_number,
                    driver.driver_name)

        success = False
        retry = 0
        while not success and retry < 3:
            success = DatabaseManagement().register_driver_with_taxi(driver=driver,
                                                                     taxi=taxi)
            retry += 1
        logger.info("Registration Result: %s", success)

def set_taxi_available(taxi_id) -> bool:
    """get available taxis"""
    return DatabaseManagement().update_taxi_status(taxi_id, "Available")


def get_available_taxis() -> list[Taxi]:
    """get available taxis"""
    return DatabaseManagement().get_taxis({"status": "Available"})


def get_taxi_current_status(taxi_id) -> str:
    """get taxi current status"""
    return DatabaseManagement().get_taxi_current_status(taxi_id=taxi_id)


def set_taxis_drivers_ready():
    """Per design, Driver make taxi available when he is ON-DUTY. Taxi should always emit
     location when it is available.
     This function is a series of helper procedure:
         1. The driver gets active - his status gets to ON DUTY
         2. The car becomes available and starts emitting its locations"""
    logger = TaxiOpsLogger()
    driver_list = DatabaseManagement().get_drivers(({}))
    taxi_list = DatabaseManagement().get_taxis(({}))
    taxi_dict: dict[str, Taxi] = {}
    for taxi in taxi_list:
        taxi_dict[taxi.driver_id] = taxi

    for driver in driver_list:
        b_success = DatabaseManagement().update_driver_status(driver_id=driver.driver_id,
                                                              status="ON-DUTY")
        if b_success:
            taxi = taxi_dict[driver.driver_id]
            logger.info("Driver - %s tagged with taxi %s status ON-DUTY: %s",
                        driver.driver_name, taxi.taxi_number, str(b_success))
            b_success = DatabaseManagement().update_taxi_status(taxi_id=taxi.taxi_id,
                                                                status="Available")
            logger.info("Associated taxi - %s status Available: %s", taxi.taxi_number,
                        str(b_success))

    logger.info("***All taxis and driver ready**** Refreshed list")
    taxi_list = DatabaseManagement().get_taxis(({}))
    logger.info(taxi_list)


def find_nearest_taxi(current_location, max_distance, max_number_of_taxi) -> list:
    """
    find the nearest taxi
    @param current_location:
    @param max_distance:
    @param max_number_of_taxi:
    @return:
    """
    # return DatabaseManagement().find_nearest_taxi(current_location,
    #                                               max_distance,
    #                                               max_number_of_taxi)
    # Added by Suraj
    try:
        return DatabaseManagement().find_nearest_taxi(current_location, max_distance, max_number_of_taxi)
    except pymongo.errors.OperationFailure as e:
        return f"Database operation failed: {e.details.get('errmsg', 'Unknown error')}"
    except ValueError as ve:
        return str(ve)
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"


def update_taxi_location(v_taxi_id, v_location):
    """
    update taxi location
    @param v_taxi_id:
    @param v_location:
    @return:
    """
    logger = TaxiOpsLogger()
    b_success = DatabaseManagement().update_taxi_location(v_taxi_id, v_location)
    logger.info("Taxi movement to %s - completed", v_location)
    return b_success

# //Added by Suraj
def update_user_location(v_user_id, v_location):
    """
    update user location
    @param v_user_id:
    @param v_location:
    @return:
    """
    logger = TaxiOpsLogger()
    b_success = DatabaseManagement().update_user_location(v_user_id, v_location)
    logger.info("User movement to %s - completed", v_location)
    return b_success


def book_and_initiate_trip(taxi_id, user_id, current_location, destination_location):
    """
    book_and_initiate_trip
    @param taxi_id:
    @param user_id:
    @param current_location:
    @param destination_location:
    @return:
    """
    # mark taxi_id status and Occupied.
    # Check if taxi_is current state is Available, If so, mark it Occupied. If not, send error
    logger = TaxiOpsLogger()

    current_status = DatabaseManagement().get_taxi_current_status(taxi_id)
    if current_status != "Available":
        raise IllegalTaxiStatusState(f"Taxi has already become {current_status}")

    b_success = DatabaseManagement().update_taxi_status(taxi_id, "Occupied")
    if b_success:
        trip_id = DatabaseManagement().create_trip(taxi_id, user_id,
                                                   current_location, destination_location)
        logger.info("Trip created - %s", trip_id)
        logger.info("Taxi moving to user location...")
        DatabaseManagement().update_taxi_location(taxi_id, current_location)
        logger.info("Taxi movement to %s - completed", current_location)

        b_success = DatabaseManagement().mark_trip_in_progress(trip_id=trip_id)
        if b_success:
            logger.info("Marking trip - %s in progress", trip_id)
            return trip_id, b_success
        return trip_id, b_success
    return None, False


def insert_trip_info_detail(trip_id, location, expected_time_for_completion):
    """
    insert trip info detail
    @param trip_id:
    @param location:
    @param expected_time_for_completion:
    @return:
    """
    return DatabaseManagement() \
        .insert_trip_location(trip_id=trip_id,
                              location=location,
                              eta=expected_time_for_completion)


def create_geo_spatial_index(self, collection, key: str):
    try:
        self._db[collection].create_index([(key, pymongo.GEOSPHERE)])
        self._logger.info("Geospatial index created on collection - %s, key - %s",
                          collection, key)
    except TypeError as exception:
        self._logger.error("An exception occurred :: %s", exception)
    except ConfigurationError as exception:
        self._logger.error("An exception occurred :: %s", exception)


# Added by Suraj
def generate_random_coordinates():
    # bounding_box = [
    #     [77.491, 12.834],  # Bottom-left
    #     [77.861, 12.834],  # Bottom-right
    #     [77.861, 13.139],  # Top-right
    #     [77.491, 13.139],  # Top-left
    #     [77.491, 12.834]  # Closing the loop to bottom-left
    # ]
    # lat_min, lat_max = 12.834, 13.139
    # lon_min, lon_max = 77.491, 77.861
    # New
    lat_min, lat_max = 77.491, 77.861
    lon_min, lon_max = 12.834, 13.139
    return round(random.uniform(lat_min, lat_max), 3), round(random.uniform(lon_min, lon_max), 3)

# Added by Suraj
def generate_random_taxi_number():
    return f"KA{random.randint(1, 99)}-{random.randint(1000, 9999)}"

# Added by Suraj
def test_create_50_taxis(count, taxi_type, taxi_number):
    taxi_types = ["Basic", "Deluxe", "Luxury"]

    # Create 50 taxi data entries
    taxis = [
        {
            "taxi_type": taxi_type if taxi_type else random.choice(taxi_types),
            "taxi_number": taxi_number if taxi_number else generate_random_taxi_number(),
            "status": "Not Operational",
            "location": {"type": "Point", "coordinates": generate_random_coordinates()},
            "city": "Bangalore",
            "driver_id": ""
        }
        for _ in range(count)
    ]
    return taxis

# Added by Suraj
def create_multiple_drivers(count):
    return DatabaseManagement() \
        .create_multiple_drivers(count)

# Added by Suraj
def create_multiple_users(count):
    return DatabaseManagement() \
        .create_multiple_users(count)

# Added by Suraj
def filter_taxis_by_type(taxis, requested_type):
    """
    Filter taxis by the requested type.
    @param taxis: List of Taxi objects
    @param requested_type: The type of taxi requested
    @return: List of taxis that match the requested type
    """
    filtered_taxis = [taxi for taxi in taxis if taxi.taxi_type == requested_type]
    if not filtered_taxis:
        raise ValueError("No taxis available of the requested type.")
    return filtered_taxis




# Added by Suraj,, generate a random path of coordinates within the boundary:
def taxi_simulate_random_coordinates_within_boundary(start_loc, end_loc, num_points):
    lat_diff = (end_loc["coordinates"][1] - start_loc["coordinates"][1]) / num_points
    lon_diff = (end_loc["coordinates"][0] - start_loc["coordinates"][0]) / num_points
    path = []
    for i in range(num_points):
        lat = start_loc["coordinates"][1] + (i * lat_diff)
        lon = start_loc["coordinates"][0] + (i * lon_diff)
        path.append([lon, lat])
    return path

if __name__ == "__main__":

    # Generate multiple taxi Added by Suraj

    # ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
    # ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
    data_taxis = test_create_50_taxis(count=50,taxi_type="", taxi_number="")
    result_multiple_taxi = register_multiple_taxis_drivers("Taxis",data_taxis,"location")

    data_drivers = create_multiple_drivers(count=10)
    result_multiple_drivers = register_multiple_taxis_drivers("Drivers", data_drivers, "")
    # #
    data_multiple_users = create_multiple_users(count=5)
    result_multiple_users = register_multiple_taxis_drivers("Users", data_multiple_users, "location")
    print(result_multiple_users)

    register_drivers_with_taxis()
    set_taxis_drivers_ready()
    # ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
    # ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————


    # register_taxi Success Object generated 664cc1a7e20bfb976d0a4000
    # result_register_taxi = register_taxi(taxi_type="Sedan", taxi_number="XYZ123")
    # print(result_register_taxi)
    # To call register_drivers_with_taxis()
    # To call set_taxis_drivers_ready()

    # register_driver Success
    # result = register_driver(driver_name="John Doe", email_id="john@example.com", phone_number="1234567890")
    # print(result)

    # register_drivers_with_taxis Success
    # result = register_drivers_with_taxis()
    # print(result)

    # set_taxi_available Success Returns True or False
    # result = set_taxi_available(taxi_id="6650545702aabe7b09e99075")
    # print(result)

    # get_available_taxis Object returned need to check
    # result = get_available_taxis()
    # print(result)

    # get_taxi_current_status Success Returns Availabe
    # result = get_taxi_current_status(taxi_id="6650545702aabe7b09e99075")
    # print(result)

    # set_taxis_drivers_ready Driver ON-DUTY and taxi avaiable
    # result = set_taxis_drivers_ready()
    # print(result)

    # Index the collections SUCCESS DONE check for the data import statement above FINAL _create_geo_spatial_index( collection_name, key)
    # class_instance = Database()
    # collection_name = 'Taxis'
    # key = 'location'
    # result = class_instance._create_geo_spatial_index( collection_name, key)
    # print(result)

    # find_nearest_taxi SUCCESS LOOK ABOVE TO BE DONE BEFORE this invoke a client
    # For the a given client ID
    # Get the Client cordinates from the database and assign to the current location
    # Then call the find_nearest_taxi()
    # Updated the Geo search by Suraj
    # current_location = {"coordinates": [77.527, 13.116]}  # Example coordinates for New York City
    # max_distance = 2000  # 2000 == 2 km
    # max_number_of_taxi = 5
    # result = find_nearest_taxi(current_location, max_distance, max_number_of_taxi)
    # # # Print the nearest taxis
    # if result:
    #     # for taxi in result:
    #     #     taxi_id = result['_id']
    #     #     print(result)
    #         for taxi in result:
    #             print(taxi.taxi_id, "--", taxi.taxi_type)
    # else:
    #     print("No taxi found within the specified distance.")

    # ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
    # collection_name = "users"
    # username = "johndoe"
    # # if is_username_unique(collection_name,username):
    # #     print("Username is available.")
    #     # Register the user
    #     # result = register_user(name, email_id, phone_number)
    #     # print(result)
    #
    # result = is_username_unique(collection_name = collection_name,username=username)
    # print(result)
    # else:
    #     print("Username already exists.")

    # ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
    # ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————


    # # Generate a path of 10 points within the boundary
    # Example usage
    # start_loc = {"coordinates": [77.65, 12.97]}
    # end_loc = {"coordinates": [77.841, 13.064]}
    # num_points = 10
    # path = taxi_simulate_random_coordinates_within_boundary(start_loc, end_loc, 10)
    # v_taxi_id = "665c6ffaa0400c9e207dd1e9"
    # for coordinates in path:
    #     v_location = {"coordinates": coordinates}
    #     result = update_taxi_location(v_taxi_id, v_location)
    #     print(result, "update_taxi_location updated")
    #     time.sleep(5)# Sleep for 1 second to simulate time between movements

    # ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
    # # SINGLE update_taxi_location SUCCESS  CHECK TAXI ID ON FAILURES
    # v_taxi_id = "6659b32069ca166b048a7610"
    # v_location = {"coordinates": [77.844, 12.977]}
    # result = update_taxi_location(v_taxi_id, v_location)
    # ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
    # ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————

    # ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
    # # update_user_location SUCCESS
    # user_id = "665076ee970c999bab2f396f"
    # v_location = {"coordinates": [12.999, 77.999]}  # Example coordinates for New York City
    # result = update_user_location(user_id, v_location)

    # ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
    # book_and_initiate_trip SUCCESS
    # # # Confirm that the User in w/n the boundry
    # Update user coordinates
    # # # Find taxi nearest to the user
    # # # Retrun one taxi and assing the taxi_id and call the boook and initate trip table.
    # # async Added by SUraj
    # # Find the nearest available taxis
    # Get the user id and get the location he is now present TO BE DONE

    # ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
    # ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
    # user_current_location = {"coordinates": [77.713, 12.851]}   # MANDAROTY Example coordinates
    # destination_location = {"coordinates": [77.65, 12.97]}  # Example coordinates
    # max_distance = 40000  # 5000 == 5 km
    # max_number_of_taxi = 10 #Keep the number same as the created Taxis
    # requested_taxi_type = "Luxury"  # Luxury, Deluxe, Basic Example requested taxi type
    # user_id = "665c6ffda0400c9e207dd1f6"
    # nearest_taxis = find_nearest_taxi(user_current_location, max_distance, max_number_of_taxi)
    # for taxi in nearest_taxis:
    #     print(taxi.taxi_id, "--", taxi.taxi_type, "", taxi.status)
    # if not nearest_taxis or isinstance(nearest_taxis, str):
    #     print("No nearby taxis available")
    # else:
    #     # Get available taxis from the nearby taxi list which is nearer to the User
    #     available_taxis = [taxi for taxi in nearest_taxis if taxi.status == 'Available']
    #     print("==================================================")
    #     print("Filter Available Taxis\n")
    #     for taxi in available_taxis:
    #         print(taxi.taxi_id, "--", taxi.taxi_type, "", taxi.status)
    #     print("==================================================")
    #     # requested_taxi_type = "Basic"  # Luxury, Deluxe, Basic Example requested taxi type
    #     filtered_taxis_type = filter_taxis_by_type(available_taxis, requested_taxi_type)
    #     print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
    #     print("Filter by the selected Taxi Type\n")
    #     for taxi in filtered_taxis_type:
    #         print(taxi.taxi_id, "--", taxi.taxi_type, "", taxi.status)
    #     print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n")
    #
    #     taxi_id = filtered_taxis_type[0].taxi_id #Get the first Taxi ID from the list
    #     # taxi_id = nearest_taxis[0]['taxi_id']
    #     print("Finally selectable available Taxi Type for booking")
    #     print(filtered_taxis_type[0].taxi_id, "---", filtered_taxis_type[0].taxi_type, "===" , filtered_taxis_type[0].status)
    #     book_and_initiate_trip(taxi_id, user_id, user_current_location, destination_location)

    # ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
    # ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————


    # ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
    # insert_trip_info_detail SUCCESS
    # Define the input parameters
    # trip_id = '6655b48c720eff9e6f77806b'
    # location = {"coordinates": [13.12, 77.70]}
    # expected_time_for_completion = '2023-10-01T11:00:00Z'
    # # Call the function
    # result = insert_trip_info_detail(trip_id, location, expected_time_for_completion)

