"""Тесты для пользовательского интерфейса (ConsoleUI)"""
import sys
import os
import tempfile
import shutil
import unittest
from unittest.mock import patch, MagicMock
from io import StringIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.db.backend.memory import Database, Record
from src.db.backend.file_database import FileDatabase
from src.db.backend.errors import InvalidAgeError, RecordNotFoundError, FileDatabaseError


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
        from src.db.tui import ConsoleUI
        ui = ConsoleUI(self.db)
        ui.current_table = self.db.get_table("TestTable")
        return ui
    
    # ===== Тесты для _read_int =====
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
    
    # ===== Тесты для _read_data_dict =====
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
    def test_read_data_dict_with_float(self, mock_input):
        mock_input.side_effect = ["price=10.5", ""]
        ui = self._get_ui()
        result = ui._read_data_dict()
        self.assertEqual(result, {"price": 10.5})
    
    @patch('builtins.input')
    def test_read_data_dict_invalid_format(self, mock_input):
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
    
    # ===== Тесты для _print_records =====
    def test_print_records_empty(self):
        ui = self._get_ui()
        ui._print_records([])
        self.assertIn("Записи не найдены", self.stdout.getvalue())
    
    def test_print_records_with_data(self):
        ui = self._get_ui()
        records = [Record(1, {"name": "John"})]
        ui._print_records(records)
        self.assertIn("John", self.stdout.getvalue())
    
    # ===== Тесты для _show_main_menu =====
    def test_show_main_menu(self):
        ui = self._get_ui()
        ui._show_main_menu()
        output = self.stdout.getvalue()
        self.assertIn("СИСТЕМА УПРАВЛЕНИЯ", output)
    
    def test_show_main_menu_with_table(self):
        ui = self._get_ui()
        ui.current_table = self.db.get_table("TestTable")
        ui._show_main_menu()
        output = self.stdout.getvalue()
        self.assertIn("TestTable", output)
    
    # ===== Тесты для _add_record =====
    @patch('builtins.input')
    def test_add_record_no_table(self, mock_input):
        ui = self._get_ui()
        ui.current_table = None
        ui._add_record()
        self.assertIn("выберите таблицу", self.stdout.getvalue())
    
    @patch('builtins.input')
    def test_add_record_success(self, mock_input):
        mock_input.side_effect = ["name=John", "age=25", ""]
        ui = self._get_ui()
        ui.current_table = self.db.get_table("TestTable")
        ui._add_record()
        self.assertIn("Запись добавлена", self.stdout.getvalue())
    
    @patch('builtins.input')
    def test_add_record_no_data(self, mock_input):
        mock_input.side_effect = [""]
        ui = self._get_ui()
        ui.current_table = self.db.get_table("TestTable")
        ui._add_record()
        self.assertIn("Нет данных", self.stdout.getvalue())
    
    @patch('builtins.input')
    def test_add_record_invalid_age(self, mock_input):
        mock_input.side_effect = ["age=-5", ""]
        ui = self._get_ui()
        ui.current_table = self.db.get_table("Student")
        with patch.object(ui.current_table, 'insert', side_effect=InvalidAgeError("Invalid age")):
            ui._add_record()
        self.assertIn("Ошибка возраста", self.stdout.getvalue())
    
    @patch('builtins.input')
    def test_add_record_exception(self, mock_input):
        mock_input.side_effect = ["name=John", ""]
        ui = self._get_ui()
        ui.current_table = self.db.get_table("TestTable")
        with patch.object(ui.current_table, 'insert', side_effect=Exception("DB error")):
            ui._add_record()
        self.assertIn("Ошибка при добавлении", self.stdout.getvalue())
    
    # ===== Тесты для _show_all_records =====
    def test_show_all_records_no_table(self):
        ui = self._get_ui()
        ui.current_table = None
        ui._show_all_records()
        self.assertIn("выберите таблицу", self.stdout.getvalue())
    
    def test_show_all_records_empty(self):
        ui = self._get_ui()
        ui.current_table = self.db.get_table("TestTable")
        ui.current_table.clear()
        ui._show_all_records()
        self.assertIn("Записи не найдены", self.stdout.getvalue())
    
    def test_show_all_records_with_data(self):
        ui = self._get_ui()
        ui.current_table = self.db.get_table("TestTable")
        ui.current_table.insert({"name": "John"})
        ui._show_all_records()
        self.assertIn("John", self.stdout.getvalue())
    
    # ===== Тесты для _find_records =====
    @patch('builtins.input')
    def test_find_records_no_table(self, mock_input):
        ui = self._get_ui()
        ui.current_table = None
        ui._find_records()
        self.assertIn("выберите таблицу", self.stdout.getvalue())
    
    @patch('builtins.input')
    def test_find_records_with_criteria(self, mock_input):
        mock_input.side_effect = ["name=John", ""]
        ui = self._get_ui()
        ui.current_table = self.db.get_table("TestTable")
        ui.current_table.insert({"name": "John"})
        ui._find_records()
        self.assertIn("John", self.stdout.getvalue())
    
    @patch('builtins.input')
    def test_find_records_empty_criteria(self, mock_input):
        mock_input.side_effect = [""]
        ui = self._get_ui()
        ui.current_table = self.db.get_table("TestTable")
        ui.current_table.insert({"name": "John"})
        ui._find_records()
        self.assertIn("John", self.stdout.getvalue())
    
    @patch('builtins.input')
    def test_find_records_exception(self, mock_input):
        mock_input.side_effect = ["name=John", ""]
        ui = self._get_ui()
        ui.current_table = self.db.get_table("TestTable")
        with patch.object(ui.current_table, 'find', side_effect=Exception("Search error")):
            ui._find_records()
        self.assertIn("Ошибка при поиске", self.stdout.getvalue())
    
    # ===== Тесты для _update_record =====
    @patch('builtins.input')
    def test_update_record_no_table(self, mock_input):
        ui = self._get_ui()
        ui.current_table = None
        ui._update_record()
        self.assertIn("выберите таблицу", self.stdout.getvalue())
    
    @patch('builtins.input')
    def test_update_record_not_found(self, mock_input):
        mock_input.side_effect = ["999", ""]
        ui = self._get_ui()
        ui.current_table = self.db.get_table("TestTable")
        ui._update_record()
        self.assertIn("не найдена", self.stdout.getvalue())
    
    @patch('builtins.input')
    def test_update_record_success(self, mock_input):
        mock_input.side_effect = ["1", "name=Johnny", ""]
        ui = self._get_ui()
        ui.current_table = self.db.get_table("TestTable")
        ui.current_table.insert({"name": "John"})
        ui._update_record()
        self.assertIn("обновлена", self.stdout.getvalue())
    
    @patch('builtins.input')
    def test_update_record_no_changes(self, mock_input):
        mock_input.side_effect = ["1", ""]
        ui = self._get_ui()
        ui.current_table = self.db.get_table("TestTable")
        ui.current_table.insert({"name": "John"})
        ui._update_record()
        self.assertIn("Нет изменений", self.stdout.getvalue())
    
    @patch('builtins.input')
    def test_update_record_exception(self, mock_input):
        mock_input.side_effect = ["1", "name=New", ""]
        ui = self._get_ui()
        ui.current_table = self.db.get_table("TestTable")
        ui.current_table.insert({"name": "John"})
        with patch.object(ui.current_table, 'update', side_effect=Exception("Update error")):
            ui._update_record()
        self.assertIn("Ошибка", self.stdout.getvalue())
    
    @patch('builtins.input')
    def test_update_record_invalid_age(self, mock_input):
        mock_input.side_effect = ["1", "age=-10", ""]
        ui = self._get_ui()
        ui.current_table = self.db.get_table("Student")
        ui.current_table.insert({"name": "John", "age": 20})
        with patch.object(ui.current_table, 'update', side_effect=InvalidAgeError("Invalid age")):
            ui._update_record()
        self.assertIn("Ошибка возраста", self.stdout.getvalue())
    
    # ===== Тесты для _delete_record =====
    @patch('builtins.input')
    def test_delete_record_no_table(self, mock_input):
        ui = self._get_ui()
        ui.current_table = None
        ui._delete_record()
        self.assertIn("выберите таблицу", self.stdout.getvalue())
    
    @patch('builtins.input')
    def test_delete_record_not_found(self, mock_input):
        mock_input.side_effect = ["999", ""]
        ui = self._get_ui()
        ui.current_table = self.db.get_table("TestTable")
        ui._delete_record()
        self.assertIn("не найдена", self.stdout.getvalue())
    
    @patch('builtins.input')
    def test_delete_record_success(self, mock_input):
        mock_input.side_effect = ["1", "д"]
        ui = self._get_ui()
        ui.current_table = self.db.get_table("TestTable")
        ui.current_table.insert({"name": "John"})
        ui._delete_record()
        self.assertIn("удалена", self.stdout.getvalue())
    
    @patch('builtins.input')
    def test_delete_record_cancel(self, mock_input):
        mock_input.side_effect = ["1", "н"]
        ui = self._get_ui()
        ui.current_table = self.db.get_table("TestTable")
        ui.current_table.insert({"name": "John"})
        ui._delete_record()
        self.assertIn("Удаление отменено", self.stdout.getvalue())
    
    # ===== Тесты для _create_new_table =====
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
    
    # ===== Тесты для _select_table =====
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
    def test_select_table_not_number(self, mock_input):
        mock_input.return_value = "abc"
        ui = self._get_ui()
        ui.current_table = None
        ui._select_table()
        self.assertIn("Введите число", self.stdout.getvalue())
    
    @patch('builtins.input')
    def test_select_table_no_tables(self, mock_input):
        # Очищаем все таблицы
        for table in self.db.list_tables():
            self.db.drop_table(table)
        mock_input.return_value = "1"
        ui = self._get_ui()
        ui._select_table()
        self.assertIn("Нет таблиц", self.stdout.getvalue())
    
    # ===== Тесты для _sort_records =====
    @patch('builtins.input')
    def test_sort_records_no_table(self, mock_input):
        ui = self._get_ui()
        ui.current_table = None
        ui._sort_records()
        self.assertIn("выберите таблицу", self.stdout.getvalue())
    
    @patch('builtins.input')
    def test_sort_records_empty(self, mock_input):
        mock_input.side_effect = ["name", "1"]
        ui = self._get_ui()
        ui.current_table = self.db.get_table("TestTable")
        ui.current_table.clear()
        ui._sort_records()
        self.assertIn("Нет записей для сортировки", self.stdout.getvalue())
    
    @patch('builtins.input')
    def test_sort_records_success(self, mock_input):
        mock_input.side_effect = ["name", "1"]
        ui = self._get_ui()
        ui.current_table = self.db.get_table("TestTable")
        ui.current_table.insert({"name": "Apple"})
        ui.current_table.insert({"name": "Zebra"})
        ui._sort_records()
        output = self.stdout.getvalue()
        self.assertIn("Apple", output)
    
    @patch('builtins.input')
    def test_sort_records_invalid_field(self, mock_input):
        mock_input.side_effect = ["invalid_field", "1"]
        ui = self._get_ui()
        ui.current_table = self.db.get_table("TestTable")
        ui.current_table.insert({"name": "Apple"})
        ui._sort_records()
        self.assertIn("не найдено", self.stdout.getvalue())
    
    @patch('builtins.input')
    def test_sort_records_descending(self, mock_input):
        mock_input.side_effect = ["name", "2"]
        ui = self._get_ui()
        ui.current_table = self.db.get_table("TestTable")
        ui.current_table.insert({"name": "Apple"})
        ui.current_table.insert({"name": "Zebra"})
        ui._sort_records()
        output = self.stdout.getvalue()
        self.assertIn("убыванию", output)
    
    @patch('builtins.input')
    def test_clear_table_no_table(self, mock_input):
        ui = self._get_ui()
        ui.current_table = None
        ui._clear_table()
        self.assertIn("выберите таблицу", self.stdout.getvalue())
    
    @patch('builtins.input')
    def test_clear_table_success(self, mock_input):
        mock_input.return_value = "д"
        ui = self._get_ui()
        ui.current_table = self.db.get_table("TestTable")
        ui.current_table.insert({"name": "John"})
        ui._clear_table()
        self.assertEqual(ui.current_table.count(), 0)
        self.assertIn("Таблица очищена", self.stdout.getvalue())
    
    @patch('builtins.input')
    def test_clear_table_cancel(self, mock_input):
        mock_input.return_value = "н"
        ui = self._get_ui()
        ui.current_table = self.db.get_table("TestTable")
        ui.current_table.insert({"name": "John"})
        ui._clear_table()
        self.assertEqual(ui.current_table.count(), 1)
    
    @patch('builtins.input')
    @patch('src.db.tui.FileDatabase')
    @patch('src.db.tui.InMemoryDatabase')
    def test_run_chooses_in_memory(self, mock_memory_db, mock_file_db, mock_input):
        """Тест: выбор in-memory БД (пункт 1)"""
        from src.db.tui import run
        
        mock_input.side_effect = ["1", "0"]  
        mock_memory_db.return_value = MagicMock()
        
        with patch('builtins.print'):
            run()
        
        mock_memory_db.assert_called_once()
        mock_file_db.assert_not_called()
    
    @patch('builtins.input')
    @patch('src.db.tui.FileDatabase')
    @patch('src.db.tui.InMemoryDatabase')
    def test_run_chooses_file_database_default_dir(self, mock_memory_db, mock_file_db, mock_input):
        """Тест: выбор файловой БД с директорией по умолчанию"""
        from src.db.tui import run
        
        mock_input.side_effect = ["2", "", "0"]  
        mock_file_db.return_value = MagicMock()
        
        with patch('builtins.print'):
            run()
        
        mock_file_db.assert_called_once_with(data_dir="data")
        mock_memory_db.assert_not_called()
    
    @patch('builtins.input')
    @patch('src.db.tui.FileDatabase')
    @patch('src.db.tui.InMemoryDatabase')
    def test_run_chooses_file_database_custom_dir(self, mock_memory_db, mock_file_db, mock_input):
        """Тест: выбор файловой БД с пользовательской директорией"""
        from src.db.tui import run
        
        mock_input.side_effect = ["2", "/custom/path", "0"]
        mock_file_db.return_value = MagicMock()
        
        with patch('builtins.print'):
            run()
        
        mock_file_db.assert_called_once_with(data_dir="/custom/path")
        mock_memory_db.assert_not_called()
    
    @patch('builtins.input')
    @patch('src.db.tui.ConsoleUI')
    def test_run_creates_ui_and_runs(self, mock_ui_class, mock_input):
        """Тест: создаётся UI и вызывается run()"""
        from src.db.tui import run
        
        mock_input.side_effect = ["1", "0"]
        mock_ui = MagicMock()
        mock_ui_class.return_value = mock_ui
        
        with patch('builtins.print'):
            run()
        
        mock_ui_class.assert_called_once()
        mock_ui.run.assert_called_once()
    
    @patch('builtins.input')
    @patch('src.db.tui.FileDatabase')
    def test_run_handles_file_database_error(self, mock_file_db, mock_input):
        """Тест: обработка ошибки при создании файловой БД"""
        from src.db.tui import run
        
        mock_input.side_effect = ["2", "data", "0"]
        mock_file_db.side_effect = FileDatabaseError("Cannot create directory")
        
        with patch('builtins.print') as mock_print:
            run()
            
            error_calls = [call for call in mock_print.call_args_list 
                          if call[0][0] and "ошибк" in str(call[0][0]).lower()]
            self.assertGreater(len(error_calls), 0)
    
    @patch('builtins.input')
    def test_run_unknown_command(self, mock_input):
        """Тест: неизвестная команда в главном меню"""
        mock_input.side_effect = ["999", "0"]
        ui = self._get_ui()
        
        with patch('builtins.print') as mock_print:
            ui.run()
            unknown_calls = [call for call in mock_print.call_args_list 
                           if call[0][0] and "Неизвестная команда" in str(call[0][0])]
            self.assertGreater(len(unknown_calls), 0)
    
    @patch('builtins.input')
    def test_run_all_menu_options(self, mock_input):
        """Тест: все пункты меню вызывают соответствующие методы"""
        mock_input.side_effect = ["1", "name=Test", "", "2", "3", "", "4", "1", "", "5", "1", "н", 
                                  "6", "NewTable", "7", "8", "1", "9", "id", "1", "10", "н", "0"]
        
        ui = self._get_ui()
        
        with patch.object(ui, '_add_record') as mock_add, \
             patch.object(ui, '_show_all_records') as mock_show, \
             patch.object(ui, '_find_records') as mock_find, \
             patch.object(ui, '_update_record') as mock_update, \
             patch.object(ui, '_delete_record') as mock_delete, \
             patch.object(ui, '_create_new_table') as mock_create, \
             patch.object(ui, '_show_tables') as mock_show_tables, \
             patch.object(ui, '_select_table') as mock_select, \
             patch.object(ui, '_sort_records') as mock_sort, \
             patch.object(ui, '_clear_table') as mock_clear, \
             patch('builtins.print'):
            
            ui.run()
            
            mock_add.assert_called()
            mock_show.assert_called()
            mock_find.assert_called()
            mock_update.assert_called()
            mock_delete.assert_called()
            mock_create.assert_called()
            mock_show_tables.assert_called()
            mock_select.assert_called()
            mock_sort.assert_called()
            mock_clear.assert_called()
    
    def test_show_tables_empty(self):
        """Тест: отображение таблиц когда их нет"""
        for table in self.db.list_tables():
            self.db.drop_table(table)
        ui = self._get_ui()
        ui._show_tables()
        self.assertIn("Нет таблиц", self.stdout.getvalue())
    
    def test_show_tables_with_data(self):
        """Тест: отображение таблиц с количеством записей"""
        ui = self._get_ui()
        ui._show_tables()
        output = self.stdout.getvalue()
        self.assertIn("TestTable", output)
        self.assertIn("записей:", output)


class TestConsoleUIWithFileDatabase(unittest.TestCase):
    """Тесты UI с использованием реальной файловой БД"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db = FileDatabase(data_dir=self.temp_dir)
        self.db.create_table("TestTable")
        self.stdout = StringIO()
        self.old_stdout = sys.stdout
        sys.stdout = self.stdout
    
    def tearDown(self):
        sys.stdout = self.old_stdout
        shutil.rmtree(self.temp_dir)
    
    def _get_ui(self):
        from src.db.tui import ConsoleUI
        ui = ConsoleUI(self.db)
        ui.current_table = self.db.get_table("TestTable")
        return ui
    
    def test_add_record_with_file_db(self):
        """Тест: добавление записи с файловой БД"""
        ui = self._get_ui()
        with patch('builtins.input', side_effect=["name=John", "age=25", ""]):
            ui._add_record()
        self.assertIn("Запись добавлена", self.stdout.getvalue())
        
        table = self.db.get_table("TestTable")
        self.assertEqual(len(table), 1)
        self.assertEqual(table.get(1).data["name"], "John")
    
    def test_persistence_through_ui(self):
        """Тест: данные сохраняются между операциями через UI"""
        ui = self._get_ui()
        
        with patch('builtins.input', side_effect=["name=Persistent", ""]):
            ui._add_record()
        
        new_ui = self._get_ui()
        
        self.assertEqual(len(new_ui.current_table), 1)
        self.assertEqual(new_ui.current_table.get(1).data["name"], "Persistent")


if __name__ == "__main__":
    unittest.main()