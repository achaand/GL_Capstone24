"""
Wrapper class over DB operations
"""
from datetime import datetime

from bson import ObjectId
from geojson import Point

from taxi_ops_backend.database import Database
from taxi_ops_backend.model import User, Taxi, Driver, OperationBoundary, TripInfo, TripInfoDetail
from taxi_ops_backend.taxi_ops_logger import TaxiOpsLogger
import random #Added by Suraj
from faker import Faker
# Set locale to Indian English
# fake_en_in = Faker('en_IN')


class DatabaseManagement:
    """
    Class doc string
    """

    def __init__(self):
        """
        Init Doc string
        """
        self._database = Database()
        self._logger = TaxiOpsLogger()

    def create_user(self, user_name, email_id, phone_number) -> str:
        """
        Makes an entry in User data
        :param user_name:
        :param email_id:
        :param phone_number:
        :return:
        """
        user: User = User(user_name, email_id, phone_number, location=Point([(0, 0)])) #Added Location by Suraj
        return self._database.insert_single_data(collection="Users",
                                                 data=user.to_dict(),  # pylint: disable=no-member
                                                 index_key="location") # Added by SUraj

    def create_taxi(self, taxi_type, taxi_number) -> str:
        """
        Makes an entry in Taxis table
        :param taxi_type: taxi type
        :param taxi_number: taxi number
        :return: Object(_id) string
        """
        taxi: Taxi = Taxi(taxi_type=taxi_type, taxi_number=taxi_number, status="Not Operational",
                          location=Point([(0, 0)]))
        return self._database.insert_single_data(collection="Taxis",
                                                 data=taxi.to_dict(),  # pylint: disable=no-member
                                                 index_key="location")
    # ADDED BY SURAJ
    def create_multiple_taxis_drivers(self, collection, data, index_key) -> str:
        """
        Makes an entry in Taxis table
        :param taxi_type: taxi type
        :param taxi_number: taxi number
        :return: Object(_id) string
        """
        return self._database.insert_multiple(collection,
                                                 data,  # pylint: disable=no-member
                                                 index_key)

    def create_multiple_drivers(self,count):
        self.fake = Faker('en_IN')
        drivers = [
            {
                "driver_name": self.fake.name(),
                "email_id": self.fake.email(),
                "phone_number": self.fake.phone_number(),
                "status": "OFF DUTY",
                "taxi_assigned": False,
                "location": {"type": "Point", "coordinates": (0, 0)},
                "driver_id": ""
            }
            for _ in range(count)
        ]
        return drivers

    # Added by Suraj
    def create_multiple_users(self, count):
        self.fake = Faker('en_IN')
        lat_min, lat_max = 77.491, 77.861
        lon_min, lon_max = 12.834, 13.139
        users = [
            {
                "user_name": self.fake.name(),
                "email_id": self.fake.email(),
                "phone_number": self.fake.phone_number(),
                # "location": {"type": "Point", "coordinates": (0, 0)}
                # "location": {"type": "Point", "coordinates": self.fake.local_latlng()},
                "location": {"type": "Point", "coordinates": (round(random.uniform(lat_min, lat_max), 3), round(random.uniform(lon_min, lon_max), 3))}
            }
            for _ in range(count)
        ]
        return users

    # driver
    def create_driver(self, driver_name, email_id, phone_number) -> str:
        """
        doc string
        :param driver_name:
        :param email_id:
        :param phone_number:
        :return:
        """
        driver: Driver = Driver(driver_name=driver_name,
                                email_id=email_id,
                                phone_number=phone_number)
        return self._database.insert_single_data(collection="Drivers",
                                                 data=driver.to_dict())  # pylint: disable=no-member

    def get_taxis(self, taxi_filter):
        """
        Gets all the taxis as per filter. In case, all is required, pass empty filter
        @param taxi_filter:
        @return:
        """
        taxi_documents = self._database.find_multiple("Taxis", taxi_filter)
        taxi_list = []
        for taxi_document in taxi_documents:
            taxi = Taxi(taxi_type=taxi_document['taxi_type'],
                        taxi_number=taxi_document['taxi_number'],
                        status=taxi_document['status'],
                        driver_id=taxi_document['driver_id'],
                        location=taxi_document['location'],
                        taxi_id=str(taxi_document['_id']))
            taxi_list.append(taxi)
        return taxi_list

    def get_drivers(self, driver_filter):
        """
        Gets all the drivers as per filter. In case, all is required, pass empty filter
        @param driver_filter:
        @return:
        """
        driver_documents = self._database.find_multiple("Drivers", driver_filter)
        driver_list = []
        for driver_document in driver_documents:
            driver = Driver(driver_name=driver_document['driver_name'],
                            email_id=driver_document['email_id'],
                            phone_number=driver_document['phone_number'],
                            status=driver_document["status"],
                            taxi_assigned=driver_document['taxi_assigned'],
                            location=driver_document['location'],
                            driver_id=str(driver_document['_id']))
            driver_list.append(driver)
        return driver_list

    def register_driver_with_taxi(self, driver: Driver, taxi: Taxi) -> bool:
        """
        update taxi with driver_id and mark driver as taxi_assigned.
        :param driver:
        :param taxi:
        :return:
        """
        matched_count, modified_count = \
            self._database.update_single("Taxis",
                                         {"_id": ObjectId(taxi.taxi_id)},
                                         {"$set": {'driver_id': taxi.driver_id}})
        self._logger.info("Taxi %s record Update: matched: %s and modified: %s",
                          taxi.taxi_number, matched_count, modified_count)
        if matched_count == modified_count == 1:
            matched_count, modified_count = \
                self._database.update_single("Drivers",
                                             {"_id": ObjectId(driver.driver_id)},
                                             {"$set": {'taxi_assigned': driver.taxi_assigned}})
            self._logger.info("Driver %s record Update: matched: %s and modified: %s",
                              driver.driver_name, matched_count, modified_count)

        self._logger.info("Taxi: %s is allocated to driver %s",
                          taxi.taxi_number, driver.driver_name)
        return matched_count == modified_count == 1
        # self._database.run_as_transactions(func_list)

    def get_taxi_current_status(self, taxi_id):
        """
        doc string
        :param taxi_id:
        :return:
        """
        taxi = self._database.find_one("Taxis", {"_id": ObjectId(taxi_id)})
        return taxi['status']

    def update_taxi_status(self, taxi_id, status) -> bool:
        """
        doc string
        :param taxi_id:
        :param status:
        :return:
        """
        matched_count, modified_count = self._database \
            .update_single(collection="Taxis",
                           update_filter={"_id": ObjectId(taxi_id)},
                           update={"$set": {'status': status}})
        return matched_count == modified_count == 1

    def update_driver_status(self, driver_id, status) -> bool:
        """
        doc string
        :param driver_id:
        :param status:
        :return:
        """
        matched_count, modified_count = self._database \
            .update_single(collection="Drivers",
                           update_filter={"_id": ObjectId(driver_id)},
                           update={"$set": {'status': status}})
        return matched_count == modified_count == 1

    def get_current_driver(self, taxi_id):
        """
        doc string
        :param taxi_id:
        :return:
        """

    def get_user_booking(self, user_id):
        """
        doc string
        :param user_id:
        :return:
        """

    def create_operation_bound(self, city,
                               left_bottom: (float, float),
                               left_top: (float, float),
                               right_top: (float, float),
                               right_bottom: (float, float)):
        """
        create operation boundary for city
        @param city:
        @param left_bottom:
        @param left_top:
        @param right_top:
        @param right_bottom:
        @return:
        """
        polygon = [left_bottom, left_top, right_top, right_bottom]
        operational_boundary = OperationBoundary(city, polygon)
        self._logger.info("Inserting Operational Boundary - %s",
                          operational_boundary.to_dict())  # pylint: disable=no-member
        return self._database.insert_single_data("Operation_Boundary",
                                                 operational_boundary.to_dict())  # pylint: disable=no-member

    def get_operation_bound(self, city):
        """
        get operation boundary
        @param city:
        @return:
        """
        document = self._database.find_one("Operation_Boundary", {"city": city})
        # Added by Suraj
        if document is None:
            raise ValueError(f"No boundary defined for city: {city}")
        polygon_coordinates = document["location"]
        self._logger.info("Fetched polygon for %s - %s", city, polygon_coordinates)
        return polygon_coordinates


    # Added by Suraj to check if the provided location are within the operations boundry.
    def taxi_within_boundary(self, city: str, latitude: float, longitude: float):
        """
        Book a taxi within the city boundary
        @param city:
        @param latitude:
        @param longitude:
        @return:
        """
        # Check if the location is within the boundary
        boundary = DatabaseManagement().get_operation_bound(city)
        if boundary is None:
            raise ValueError(f"No boundary defined for city: {city}")

        left_bottom, left_top, right_top, right_bottom = boundary
        if (left_bottom[0] <= latitude <= left_top[0] and
                left_bottom[1] <= longitude <= right_bottom[1]):
            # return DatabaseManagement().book_taxi(city, latitude, longitude)
            return boundary
        else:
            raise ValueError("Location is outside the operation boundary")


    # Added by Suraj to check if the provided location are within the operations boundry.
    def is_within_boundary(boundary, latitude, longitude):
        """
        Check if a point is within the boundary
        @param boundary:
        @param latitude:
        @param longitude:
        @return:
        """
        left_bottom, left_top, right_top, right_bottom = boundary
        return (left_bottom[0] <= latitude <= left_top[0] and
                left_bottom[1] <= longitude <= right_bottom[1])

    def update_taxi_location(self, taxi_id, location: Point) -> bool: #Updated by Suraj to take Point
        """
       Update taxi location.
       @param taxi_id: ID of the taxi
       @param location: Location as a dict with "coordinates" key containing [latitude, longitude]
       @return: True if the update was successful, False otherwise
        """
        geojson_location = { #Lot of EFFORTS has gone though to just get this format enabled SURAJ
            "type": "Point",
            "coordinates": location["coordinates"]
        }

        matched_count, modified_count = self._database \
            .update_single(collection="Taxis",
                           update_filter={"_id": ObjectId(taxi_id)},
                           update={"$set": {
                               'location': geojson_location}}
                           )
        return matched_count == modified_count == 1

    # Added by SUraj
    def update_user_location(self, user_id: str, location: Point) -> bool:
        """
        Update user location
        @param user_id: The ID of the user
        @param location: The new location of the user as a Point object
        @return: True if the update was successful, False otherwise
        """
        matched_count, modified_count = self._database \
            .update_single(collection="Users",
                           update_filter={"_id": ObjectId(user_id)},
                           update={"$set": {
                               'location': location["coordinates"]
                           }
                           })
        return matched_count == modified_count == 1


    def find_nearest_taxi(self, current_location,
                          max_distance, max_number_of_taxi) -> list:
        """
        find the nearest taxi
        @param current_location:
        @param max_distance:
        @param max_number_of_taxi:
        @return:
        """
        longitude = current_location["coordinates"][0]
        latitude = current_location["coordinates"][1]
        documents = self._database \
            .find_nearest_entities_in_collection("Taxis",
                                                 longitude,
                                                 latitude,
                                                 max_distance,
                                                 max_number_of_taxi)
        taxi_list = []
        for taxi_document in documents:
            # Check if the taxi is Available then only return Available taxi
            # if taxi_document['status'] == 'Available':
            taxi = Taxi(taxi_type=taxi_document['taxi_type'],
                        taxi_number=taxi_document['taxi_number'],
                        status=taxi_document['status'],
                        driver_id=taxi_document['driver_id'],
                        location=taxi_document['location'],
                        taxi_id=str(taxi_document['_id']))
            taxi_list.append(taxi)

        return taxi_list

    def create_trip(self, taxi_id, user_id, current_location, destination_location) -> str:
        """
        create trip
        @param taxi_id:
        @param user_id:
        @param current_location:
        @param destination_location:
        @return:
        """
        trip_info = TripInfo(trip_id="", user_id=user_id, taxi_id=taxi_id,
                             starting_point=current_location,
                             destination_point=destination_location,
                             status="Not Started")
        self._logger.info("Now creating trip with details - ")
        self._logger.info(trip_info.to_dict())  # pylint: disable=no-member
        return self._database.insert_single_data("TripInfos", trip_info.to_dict())  # pylint: disable=no-member

    def mark_trip_in_progress(self, trip_id) -> bool:
        """

        @param trip_id:
        @return:
        """
        matched_count, modified_count = self._database \
            .update_single(collection="TripInfos",
                           update_filter={"_id": ObjectId(trip_id)},
                           update={"$set": {
                               "status": "In Progress",
                               "start_time": datetime.now()}})
        return matched_count == modified_count == 1

    def insert_trip_location(self, trip_id, location, eta):
        """
        insert new location
        @param trip_id:
        @param location:
        @param eta:
        @return:
        """
        trip_info_detail = TripInfoDetail(trip_id=trip_id,
                                          location=location,
                                          reporting_time=datetime.now(),
                                          expected_time_for_completion_in_min=eta)
        return self._database.insert_single_data(collection="TripInfoDetail",
                                                 data=trip_info_detail.to_dict())

    def clean_up_database(self):
        """clean up database"""
        for collection in ["Taxis", "Users", "Drivers", "Operation_Boundary",
                           "TripInfos", "TripInfoDetail"]:
            self._database.drop_collection(collection=collection)
        # for collection in ["Operation_Boundary"]:
        #     self._database.drop_collection(collection=collection)

    # Written by Suraj
    def is_username_unique(self, collection_name, username):
        """
        Check if a username is unique in the specified collection
        :param collection_name: The name of the collection to check
        :param username: The username to check
        :return: True if the username is unique, False otherwise
        """
        try:
            # collection = self.db[collection_name]
            # user = collection.find_one({"username": username})
            # return user is None
            # if not username:
            #     return f"Document must contain '{username}' field"

            collection = self._database[collection_name]
            query = {}
            if collection_name == "Taxis":
                query = {"taxi_number": username}
            elif collection_name == "Users":
                query = {"name": username}
            elif collection_name == "Drivers":
                query = {"driver_name": username}
            else:
                raise ValueError("Unsupported collection name")

            document = collection.find_one(query)
            return document is None

        # except pymongo.errors.OperationFailure as e:
        #     print(f"Database operation failed: {e.details.get('errmsg', 'Unknown error')}")
        #     return False
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")
            return False


# Instance of Class Main
Object = DatabaseManagement()

# Calling Function1
# taxi_ops_backend.database_management.DatabaseManagement.clean_up_database()
# Object.clean_up_database()
# print("Clean up database done")

# result = Object.create_multiple_users(count=50)
# print(result)
# Object.create_user("Suraj","a@b.com","938298393893")
# print("User Cration done")

# Object.create_taxi("Comfort", "32111" )
# print("Taxi Cration done")
