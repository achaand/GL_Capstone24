from data_operations import DatabaseManagement

def register_user(name, email_id, phone_number) -> str:
    """
    doc string
    :param name:
    :param email_id:
    :param phone_number:
    :return:
    """
    return DatabaseManagement().create_user(user_name=name,
                                            email_id=email_id,
                                            phone_number=phone_number)

if __name__ == "__main__":

    # Example input
    name = "USER3333"
    email_id = "ram ram@example.com"
    phone_number = "2929292929"

    # Call the function
    # Register the user
    result = register_user(name, email_id, phone_number)
    print(result)


