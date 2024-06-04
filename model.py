"""Data model to used in this project"""

import datetime
from geojson import Point


# @dataclass
class User:  # pylint: disable=too-few-public-methods
    """User Table"""
    # attributes
    name: str
    email_id: str
    phone_number: str
    location: Point
    # will work out: user_id remains blank in DB
    user_id: str

    def __init__(self, name, email_id, phone_number, location, user_id=''): #SUraj changed location not none
        self.name = name
        self.email_id = email_id
        self.phone_number = phone_number
        self.location = location
        self.user_id = user_id

    def to_dict(self):
        """convert to dict"""
        # Add Location operations for indexing
        geojson_point = None
        if self.location is not None:
            # geojson_point = {"type": "Point", "coordinates": self.location["coordinates"][0]}
            geojson_point = self.location["coordinates"][0]

        return {"name": self.name, "email_id": self.email_id,
                "phone_number": self.phone_number,
                "location": geojson_point, "user_id": self.user_id} #Update Location Suraj


# @dataclass
class Driver:  # pylint: disable=too-few-public-methods
    """Driver Table"""
    driver_name: str
    email_id: str
    phone_number: str
    status: str
    taxi_assigned: bool
    location: Point
    # will work out: driver_id remains blank in DB
    driver_id: str

    def __init__(self, driver_name: str,
                 email_id: str,
                 phone_number: str,
                 status: str = "OFF DUTY",
                 taxi_assigned: bool = False,
                 location: Point = None,
                 # will work out: driver_id remains blank in DB
                 driver_id: str = ""):
        self.driver_name = driver_name
        self.email_id = email_id
        self.phone_number = phone_number
        self.status = status
        self.taxi_assigned = taxi_assigned
        self.location = location
        self.driver_id = driver_id

    def to_dict(self):
        """convert to dict"""
        return {"driver_name": self.driver_name, "email_id": self.email_id,
                "phone_number": self.phone_number, "status": self.status,
                "taxi_assigned": self.taxi_assigned, "driver_id": self.driver_id,
                "location": ""}


TaxiType = ["Basic", "Deluxe", "Luxury"]
TaxiStatus = ["Not Operational", "Occupied", "Available"]


# @dataclass
class Taxi:  # pylint: disable=too-few-public-methods
    """Taxi table"""
    taxi_type: str
    taxi_number: str
    status: str
    location: Point
    # Assumption for this project is that there would be 1 driver for a taxi
    driver_id: str
    # will work out: taxi_id remains blank in DB
    taxi_id: str

    def __init__(self, taxi_type, taxi_number, status, location, driver_id='', taxi_id=''):
        self.taxi_type = taxi_type
        self.taxi_number = taxi_number
        self.status = status
        self.location = location
        self.driver_id = driver_id
        self.taxi_id = taxi_id

    def to_dict(self):
        """converts taxi object to dict"""
        geojson_point = None
        if self.location is not None:
            # geojson_point = {"type": "Point", "coordinates": self.location["coordinates"][0]}
            geojson_point = self.location["coordinates"][0]

        return {"taxi_type": self.taxi_type, "taxi_number": self.taxi_number,
                "status": self.status, "driver_id": self.driver_id,
                "location": geojson_point}


# @dataclass
class OperationBoundary:  # pylint: disable=too-few-public-methods
    """Operation Boundary"""
    city: str
    location: list[(float, float)]

    def __init__(self, city, location):
        self.city = city
        self.location = location

    def to_dict(self):
        """convert to dict"""
        return {"city": self.city, "location": self.location}


TripStatus = ["Not Started", "In Progress", "Completed"]


# @dataclass
class TripInfo:
    """TripInfo Table"""
    trip_id: str
    user_id: str
    taxi_id: str
    starting_point: Point
    destination_point: Point
    status: TripStatus
    start_time: datetime.datetime
    end_time: datetime.datetime

    def __init__(self, trip_id: str,
                 user_id: str,
                 taxi_id: str,
                 starting_point: Point,
                 destination_point: Point,
                 status: TripStatus,
                 start_time: datetime.datetime = None,
                 end_time: datetime.datetime = None):
        self.trip_id = trip_id
        self.user_id = user_id
        self.taxi_id = taxi_id
        self.starting_point = starting_point
        self.destination_point = destination_point
        self.status = status
        self.start_time = start_time
        self.end_time = end_time

    @staticmethod
    def point_to_location(point):
        """
        geojson point to mongodb compatible location
        @param point:
        @return:
        """
        geojson_point = None
        if point is not None:
            geojson_point = point["coordinates"]
        return geojson_point

    def to_dict(self):
        """converts trip info into dict"""
        return {"trip_id": self.trip_id, "user_id": self.user_id,
                "taxi_id": self.taxi_id,
                "starting_point": self.point_to_location(self.starting_point),
                "destination_point": self.point_to_location(self.destination_point),
                "status": self.status, "start_time": self.start_time,
                "end_time": self.start_time}


# @dataclass
class TripInfoDetail:  # pylint: disable=too-few-public-methods
    """TripInfoDetail Table"""
    trip_id: str
    location: Point
    reporting_time: datetime.datetime
    expected_time_for_completion_in_min: int

    def __init__(self, trip_id: str,
                 location: Point,
                 reporting_time: datetime.datetime,
                 expected_time_for_completion_in_min: int):
        self.trip_id = trip_id
        self.location = location
        self.reporting_time = reporting_time
        self.expected_time_for_completion_in_min = expected_time_for_completion_in_min

    def to_dict(self):
        """converts taxi object to dict"""
        geojson_point = None
        if self.location is not None:
            geojson_point = self.location["coordinates"]

        return {"trip_id": self.trip_id, "location": geojson_point,
                "reporting_time": self.reporting_time,
                "expected_time_for_completion_in_min":
                    self.expected_time_for_completion_in_min}