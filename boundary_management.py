"""This is the service layer which is exposed using API gateway.
This should go in lambda
"""
from data_operations import DatabaseManagement


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


def get_operation_boundary(city):
    """
    get operation boundary polygon
    @param city:
    @return:
    """
    return DatabaseManagement().get_operation_bound(city=city)

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
    # latitude = 13.00
    # longitude = 77.861
    latitude = 12.900
    longitude = 77.594
    result = DatabaseManagement().taxi_within_boundary(city, latitude, longitude)
    print(result)