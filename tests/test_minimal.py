import unittest
from src.db.backend.memory import StudentTable

class TestMinimal(unittest.TestCase):
    def test_import(self):
        table = StudentTable()
        self.assertIsNotNone(table)
        print("✓ Тест работает!")

if __name__ == '__main__':
    unittest.main()
