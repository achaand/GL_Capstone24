import unittest
from lambda_handler import register_user

class TestUserManagement(unittest.TestCase):

    def test_register_user(self):
        result = register_user("John Doe", "john.doe@example.com", "1234567890")
        self.assertEqual(result, "User created successfully")

if __name__ == '__main__':
    unittest.main()