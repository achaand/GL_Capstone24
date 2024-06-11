import json
from data_operations import DatabaseManagement

def register_user(name, email_id, phone_number) -> str:
    """
    Registers a new user in the database.
    :param name: str
    :param email_id: str
    :param phone_number: str
    :return: str
    """
    return DatabaseManagement().create_user(user_name=name, email_id=email_id, phone_number=phone_number)

def lambda_handler(event, context):
    """
    AWS Lambda handler function.
    :param event: dict, required
        API Gateway Lambda Proxy Input Format
    :param context: object, required
        Lambda Context runtime methods and attributes
    :return: dict
        API Gateway Lambda Proxy Output Format
    """
    try:
        # Extract parameters from the event
        body = json.loads(event.get('body', '{}'))
        name = body.get('name')
        email_id = body.get('email_id')
        phone_number = body.get('phone_number')

        # Validate inputs
        if not name or not email_id or not phone_number:
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "Missing required parameters"})
            }

        # Call the register_user function
        result = register_user(name, email_id, phone_number)

        # Return success response
        return {
            "statusCode": 200,
            "body": json.dumps({"message": result})
        }

    except Exception as e:
        # Return error response
        return {
            "statusCode": 500,
            "body": json.dumps({"message": str(e)})
        }