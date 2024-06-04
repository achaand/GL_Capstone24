from taxi_ops_backend.database_management import DatabaseManagement

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


def register_user(name, email_id, phone_number, location) -> str:
    """
    doc string
    :param name:
    :param email_id:
    :param phone_number:
    :return:
    """

    if not is_within_boundary(location):
        raise ValueError("Location is outside the allowed boundary")

    return DatabaseManagement().create_user(user_name=name, email_id=email_id, phone_number=phone_number, location=location)


if __name__ == "__main__":

    # Example input
    name = "USER3333"
    email_id = "ram ram@example.com"
    phone_number = "2929292929"
    location = {"coordinates": [77.5, 12.9]}  # Example coordinates

    # Call the function
    # Register the user
    try:
        result = register_user(name, email_id, phone_number, location)
        print(result)
    except ValueError as e:
        print(f"Error: {e}")


