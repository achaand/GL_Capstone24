from taxi_ops_backend.database import Database
from taxi_ops_backend.database_management import DatabaseManagement

db_management = DatabaseManagement()

# Calling all the function from the DatabaseManagement of file database_management.py
# get_current_driver blank
# get_user_booking Blank


# class_instance = Database()
# collection_name = 'Taxis'
# key = 'location'
# result = class_instance.find_one("collection_name", "key" )
# print(result)


#"Taxis", "Users", "Drivers", "Operation_Boundary", "TripInfos", "TripInfoDetail"
# WORKING CODE to clean the database
result = db_management.clean_up_database()
print(result)

# Call the function
# collection_name = "users"
# username = "asdfsadf"
# if db_management.is_username_unique(collection_name, username):
#     print("Username is available.")
# #     # Register the user
# # result = db_management.register_user(name, email_id, phone_number)
# # print(result)
# else:
#     print("Username already exists.")


