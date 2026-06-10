"""Минимальные тесты для пользовательского интерфейса (ConsoleUI)"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import unittest
from unittest.mock import patch
from io import StringIO

from db.backend.memory import Database, Record


class TestConsoleUI(unittest.TestCase):
    
    def setUp(self):
        self.db = Database()
        self.db.create_table("TestTable")
        self.stdout = StringIO()
        self.old_stdout = sys.stdout
        sys.stdout = self.stdout
    
    def tearDown(self):
        sys.stdout = self.old_stdout
    
    def _get_ui(self):
        from db.tui import ConsoleUI
        ui = ConsoleUI(self.db)
        ui.current_table = self.db.get_table("TestTable")
        return ui
    
    @patch('builtins.input')
    def test_read_int_valid(self, mock_input):
        mock_input.return_value = "42"
        ui = self._get_ui()
        result = ui._read_int("Введите число: ")
        self.assertEqual(result, 42)
    
    @patch('builtins.input')
    def test_read_int_invalid_then_valid(self, mock_input):
        mock_input.side_effect = ["abc", "42"]
        ui = self._get_ui()
        result = ui._read_int("Введите число: ")
        self.assertEqual(result, 42)
    
    @patch('builtins.input')
    def test_read_optional_int_empty(self, mock_input):
        mock_input.return_value = ""
        ui = self._get_ui()
        result = ui._read_int("Введите число: ", optional=True)
        self.assertIsNone(result)
    
    @patch('builtins.input')
    def test_read_optional_int_valid(self, mock_input):
        mock_input.return_value = "42"
        ui = self._get_ui()
        result = ui._read_int("Введите число: ", optional=True)
        self.assertEqual(result, 42)
    
    @patch('builtins.input')
    def test_read_data_dict_single(self, mock_input):
        mock_input.side_effect = ["name=John", ""]
        ui = self._get_ui()
        result = ui._read_data_dict()
        self.assertEqual(result, {"name": "John"})
    
    @patch('builtins.input')
    def test_read_data_dict_multiple(self, mock_input):
        mock_input.side_effect = ["name=John", "age=25", ""]
        ui = self._get_ui()
        result = ui._read_data_dict()
        self.assertEqual(result, {"name": "John", "age": 25})
    
    @patch('builtins.input')
    def test_read_data_dict_invalid(self, mock_input):
        mock_input.side_effect = ["wrong", "name=John", ""]
        ui = self._get_ui()
        result = ui._read_data_dict()
        self.assertEqual(result, {"name": "John"})
    
    @patch('builtins.input')
    def test_read_data_dict_empty(self, mock_input):
        mock_input.side_effect = [""]
        ui = self._get_ui()
        result = ui._read_data_dict()
        self.assertEqual(result, {})
    
    def test_print_records_empty(self):
        ui = self._get_ui()
        ui._print_records([])
        self.assertIn("Записи не найдены", self.stdout.getvalue())
    
    def test_print_records_with_data(self):
        ui = self._get_ui()
        records = [Record(1, {"name": "John"})]
        ui._print_records(records)
        self.assertIn("John", self.stdout.getvalue())
    
    def test_show_main_menu(self):
        ui = self._get_ui()
        ui._show_main_menu()
        self.assertIn("СИСТЕМА УПРАВЛЕНИЯ", self.stdout.getvalue())
    
    @patch('builtins.input')
    def test_create_new_table_success(self, mock_input):
        mock_input.return_value = "NewTable"
        ui = self._get_ui()
        ui._create_new_table()
        self.assertIn("создана", self.stdout.getvalue())
    
    @patch('builtins.input')
    def test_create_new_table_empty(self, mock_input):
        mock_input.return_value = ""
        ui = self._get_ui()
        ui._create_new_table()
        self.assertIn("не может быть пустым", self.stdout.getvalue())
    
    @patch('builtins.input')
    def test_create_new_table_duplicate(self, mock_input):
        mock_input.return_value = "TestTable"
        ui = self._get_ui()
        ui._create_new_table()
        self.assertIn("уже существует", self.stdout.getvalue())
    
    def test_show_tables(self):
        ui = self._get_ui()
        ui._show_tables()
        self.assertIn("Student", self.stdout.getvalue())
    
    @patch('builtins.input')
    def test_select_table_success(self, mock_input):
        mock_input.return_value = "1"
        ui = self._get_ui()
        ui.current_table = None
        ui._select_table()
        self.assertIsNotNone(ui.current_table)
    
    @patch('builtins.input')
    def test_select_table_invalid(self, mock_input):
        mock_input.return_value = "99"
        ui = self._get_ui()
        ui.current_table = None
        ui._select_table()
        self.assertIn("Неверный номер", self.stdout.getvalue())
    
    @patch('builtins.input')
    def test_sort_records_no_table(self, mock_input):
        ui = self._get_ui()
        ui.current_table = None
        ui._sort_records()
        self.assertIn("выберите таблицу", self.stdout.getvalue())
    
    @patch('builtins.input')
    def test_sort_records_success(self, mock_input):
        mock_input.side_effect = ["name", "1"]
        ui = self._get_ui()
        ui.current_table.insert({"name": "Apple"})
        ui.current_table.insert({"name": "Zebra"})
        ui._sort_records()
        output = self.stdout.getvalue()
        self.assertIn("Apple", output)
    
    @patch('builtins.input')
    def test_clear_table_success(self, mock_input):
        mock_input.return_value = "д"
        ui = self._get_ui()
        ui.current_table.insert({"name": "John"})
        ui._clear_table()
        self.assertEqual(ui.current_table.count(), 0)
        self.assertIn("очищена", self.stdout.getvalue())
    
    @patch('builtins.input')
    def test_clear_table_cancel(self, mock_input):
        mock_input.return_value = "н"
        ui = self._get_ui()
        ui.current_table.insert({"name": "John"})
        ui._clear_table()
        self.assertEqual(ui.current_table.count(), 1)
    
    @patch('builtins.input')
    def test_run_exit(self, mock_input):
        mock_input.return_value = "0"
        ui = self._get_ui()
        with patch('builtins.print'):
            ui.run()
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()