# tests/test_tui.py
import unittest
from unittest.mock import patch, call, MagicMock
import sys
from io import StringIO
from src.db import tui
from src.db.backend.errors import InvalidAgeError, DuplicateIDError


class TestTUI(unittest.TestCase):
    """Тесты для пользовательского интерфейса"""
    
    def setUp(self):
        # Перенаправляем stdout для проверки вывода
        self.stdout = StringIO()
        self.old_stdout = sys.stdout
        sys.stdout = self.stdout
    
    def tearDown(self):
        # Восстанавливаем stdout
        sys.stdout = self.old_stdout
    
    # ===== Тесты для _read_int =====
    @patch('src.db.tui.input')
    def test_read_int_valid(self, mock_input):
        """Тест _read_int с валидным вводом"""
        mock_input.return_value = "42"
        result = tui._read_int("Введите число: ")
        self.assertEqual(result, 42)
    
    @patch('src.db.tui.input')
    def test_read_int_invalid_then_valid(self, mock_input):
        """Тест _read_int с невалидным, потом валидным вводом (строки 52-56)"""
        mock_input.side_effect = ["abc", "42"]
        result = tui._read_int("Введите число: ")
        self.assertEqual(result, 42)
        # Проверяем, что было сообщение об ошибке
        output = self.stdout.getvalue()
        self.assertIn("Ошибка: введите целое число", output)
    
    # ===== Тесты для _read_optional_int =====
    @patch('src.db.tui.input')
    def test_read_optional_int_empty(self, mock_input):
        """Тест _read_optional_int с пустым вводом"""
        mock_input.return_value = ""
        result = tui._read_optional_int("Введите число: ")
        self.assertIsNone(result)
    
    @patch('src.db.tui.input')
    def test_read_optional_int_valid(self, mock_input):
        """Тест _read_optional_int с валидным вводом"""
        mock_input.return_value = "42"
        result = tui._read_optional_int("Введите число: ")
        self.assertEqual(result, 42)
    
    @patch('src.db.tui.input')
    def test_read_optional_int_invalid(self, mock_input):
        """Тест _read_optional_int с невалидным вводом (строки 92-93)"""
        mock_input.side_effect = ["abc", "42"]
        result = tui._read_optional_int("Введите число: ")
        self.assertEqual(result, 42)
        output = self.stdout.getvalue()
        self.assertIn("Ошибка: введите целое число", output)
    
    # ===== Тесты для _print_records =====
    @patch('src.db.tui.print')
    def test_print_records_empty(self, mock_print):
        """Тест _print_records с пустым списком"""
        tui._print_records([])
        mock_print.assert_called_with("Записи не найдены.")
    
    @patch('src.db.tui.print')
    def test_print_records_with_data(self, mock_print):
        """Тест _print_records с данными"""
        records = [(1, "John", "Doe", 20, "M"), (2, "Jane", "Smith", 22, "F")]
        tui._print_records(records)
        self.assertEqual(mock_print.call_count, 2)
    
    # ===== Тесты для _add_student =====
    @patch('src.db.tui._read_int')
    @patch('src.db.tui.input')
    @patch('src.db.tui.create_record')
    @patch('src.db.tui.print')
    def test_add_student_success(self, mock_print, mock_create, mock_input, mock_read_int):
        """Тест успешного добавления студента"""
        mock_read_int.side_effect = [1, 20]
        mock_input.side_effect = ["John", "Doe", "M"]
        mock_create.return_value = (1, "John", "Doe", 20, "M")
        
        tui._add_student()
        
        mock_create.assert_called_with(1, "John", "Doe", 20, "M")
        
        expected_text = "Запись добавлена: (1, 'John', 'Doe', 20, 'M')"
        found = False
        for call_args in mock_print.call_args_list:
            args = call_args[0]
            if args and expected_text in args[0]:
                found = True
                break
        self.assertTrue(found, f"Текст '{expected_text}' не найден")
    
    @patch('src.db.tui._read_int')
    @patch('src.db.tui.input')
    @patch('src.db.tui.create_record')
    @patch('src.db.tui.print')
    def test_add_student_duplicate_error(self, mock_print, mock_create, mock_input, mock_read_int):
        """Тест добавления студента с дублирующимся ID (строки 73, 82-88)"""
        mock_read_int.side_effect = [1, 20]
        mock_input.side_effect = ["John", "Doe", "M"]
        
        def raise_error(*args, **kwargs):
            raise DuplicateIDError("Запись с id=1 уже существует.")
        
        mock_create.side_effect = raise_error
        tui._add_student()
        
        mock_create.assert_called_once()
        
        expected_text = "Запись с id=1 уже существует"
        found = False
        for call_args in mock_print.call_args_list:
            args = call_args[0]
            if args and expected_text in args[0]:
                found = True
                break
        self.assertTrue(found, f"Текст '{expected_text}' не найден")
    
    @patch('src.db.tui._read_int')
    @patch('src.db.tui.input')
    @patch('src.db.tui.create_record')
    @patch('src.db.tui.print')
    def test_add_student_invalid_age(self, mock_print, mock_create, mock_input, mock_read_int):
        """Тест добавления студента с невалидным возрастом"""
        mock_read_int.side_effect = [1, -5]
        mock_input.side_effect = ["John", "Doe", "M"]
        
        def raise_error(*args, **kwargs):
            raise InvalidAgeError("Поле age не может быть отрицательным.")
        
        mock_create.side_effect = raise_error
        tui._add_student()
        
        mock_create.assert_called_once()
        
        expected_text = "Поле age не может быть отрицательным"
        found = False
        for call_args in mock_print.call_args_list:
            args = call_args[0]
            if args and expected_text in args[0]:
                found = True
                break
        self.assertTrue(found, f"Текст '{expected_text}' не найден")
    
    @patch('src.db.tui._read_int')
    @patch('src.db.tui.input')
    @patch('src.db.tui.create_record')
    @patch('src.db.tui.print')
    def test_add_student_value_error(self, mock_print, mock_create, mock_input, mock_read_int):
        """Тест добавления студента с другой ошибкой (строки 98-107)"""
        mock_read_int.side_effect = [1, 20]
        mock_input.side_effect = ["John", "Doe", "M"]
        
        def raise_error(*args, **kwargs):
            raise ValueError("Другая ошибка")
        
        mock_create.side_effect = raise_error
        tui._add_student()
        
        mock_create.assert_called_once()
        
        expected_text = "Другая ошибка"
        found = False
        for call_args in mock_print.call_args_list:
            args = call_args[0]
            if args and expected_text in args[0]:
                found = True
                break
        self.assertTrue(found, f"Текст '{expected_text}' не найден")
    
    # ===== Тесты для _show_all_students =====
    @patch('src.db.tui.select_record')
    @patch('src.db.tui._print_records')
    def test_show_all_students(self, mock_print_records, mock_select):
        """Тест показа всех студентов"""
        mock_select.return_value = [(1, "John", "Doe", 20, "M")]
        
        tui._show_all_students()
        
        mock_select.assert_called_once()
        mock_print_records.assert_called_once_with(mock_select.return_value)
    
    # ===== Тесты для _find_students_by_filter =====
    @patch('src.db.tui._read_optional_int')
    @patch('src.db.tui.input')
    @patch('src.db.tui.select_record')
    @patch('src.db.tui._print_records')
    def test_find_students_by_filter(self, mock_print, mock_select, mock_input, mock_read_opt):
        """Тест поиска студентов по фильтру"""
        mock_read_opt.side_effect = [1, 20]
        mock_input.side_effect = ["John", "Doe", "M"]
        
        tui._find_students_by_filter()
        
        mock_select.assert_called_once()
        mock_print.assert_called_once()
    
    @patch('src.db.tui._read_optional_int')
    @patch('src.db.tui.input')
    @patch('src.db.tui.select_record')
    @patch('src.db.tui._print_records')
    def test_find_students_by_filter_empty(self, mock_print, mock_select, mock_input, mock_read_opt):
        """Тест поиска с пустыми фильтрами (строки 111-131)"""
        mock_read_opt.return_value = None
        mock_input.return_value = ""
        
        tui._find_students_by_filter()
        
        mock_select.assert_called_once()
        mock_print.assert_called_once()
    
    # ===== Тесты для _update_student =====
    @patch('src.db.tui._read_int')
    @patch('src.db.tui.select_record')
    @patch('src.db.tui.print')
    def test_update_student_not_found(self, mock_print, mock_select, mock_read_int):
        """Тест обновления несуществующего студента"""
        mock_read_int.return_value = 999
        mock_select.return_value = []
        
        tui._update_student()
        
        expected_text = "Запись с id=999 не найдена"
        found = False
        for call_args in mock_print.call_args_list:
            args = call_args[0]
            if args and expected_text in args[0]:
                found = True
                break
        self.assertTrue(found, f"Текст '{expected_text}' не найден")
    
    @patch('src.db.tui._read_int')
    @patch('src.db.tui.input')
    @patch('src.db.tui.select_record')
    @patch('src.db.tui.update_record')
    @patch('src.db.tui.print')
    def test_update_student_success(self, mock_print, mock_update, mock_select, mock_input, mock_read_int):
        """Тест успешного обновления студента (строки 142-143, 167-171)"""
        mock_read_int.return_value = 1
        mock_select.return_value = [(1, "John", "Doe", 20, "M")]
        mock_input.side_effect = ["Johnny", "", "21", ""]
        mock_update.return_value = (1, "Johnny", "Doe", 21, "M")
        
        tui._update_student()
        
        mock_update.assert_called_with(1, "Johnny", None, 21, None)
        
        expected_text = "Запись обновлена: (1, 'Johnny', 'Doe', 21, 'M')"
        found = False
        for call_args in mock_print.call_args_list:
            args = call_args[0]
            if args and expected_text in args[0]:
                found = True
                break
        self.assertTrue(found, f"Текст '{expected_text}' не найден")
    
    @patch('src.db.tui._read_int')
    @patch('src.db.tui.input')
    @patch('src.db.tui.select_record')
    @patch('src.db.tui.update_record')
    @patch('src.db.tui.print')
    def test_update_student_invalid_age(self, mock_print, mock_update, mock_select, mock_input, mock_read_int):
        """Тест обновления с невалидным возрастом (строки 175-195)"""
        mock_read_int.return_value = 1
        mock_select.return_value = [(1, "John", "Doe", 20, "M")]
        mock_input.side_effect = ["", "", "-5", ""]
        
        def raise_error(*args, **kwargs):
            raise InvalidAgeError("Поле age не может быть отрицательным.")
        
        mock_update.side_effect = raise_error
        
        tui._update_student()
        
        expected_text = "Поле age не может быть отрицательным"
        found = False
        for call_args in mock_print.call_args_list:
            args = call_args[0]
            if args and expected_text in args[0]:
                found = True
                break
        self.assertTrue(found, f"Текст '{expected_text}' не найден")
    
    # ===== Тесты для _delete_student =====
    @patch('src.db.tui._read_int')
    @patch('src.db.tui.select_record')
    @patch('src.db.tui.input')
    @patch('src.db.tui.delete_record')
    @patch('src.db.tui.print')
    def test_delete_student_success(self, mock_print, mock_delete, mock_input, mock_select, mock_read_int):
        """Тест успешного удаления студента"""
        mock_read_int.return_value = 1
        mock_select.return_value = [(1, "John", "Doe", 20, "M")]
        mock_input.return_value = "д"
        mock_delete.return_value = True
        
        tui._delete_student()
        
        mock_delete.assert_called_with(1)
        
        expected_text = "Запись с id=1 удалена"
        found = False
        for call_args in mock_print.call_args_list:
            args = call_args[0]
            if args and expected_text in args[0]:
                found = True
                break
        self.assertTrue(found, f"Текст '{expected_text}' не найден")
    
    @patch('src.db.tui._read_int')
    @patch('src.db.tui.select_record')
    @patch('src.db.tui.input')
    @patch('src.db.tui.print')
    def test_delete_student_cancel(self, mock_print, mock_input, mock_select, mock_read_int):
        """Тест отмены удаления студента"""
        mock_read_int.return_value = 1
        mock_select.return_value = [(1, "John", "Doe", 20, "M")]
        mock_input.return_value = "н"
        
        tui._delete_student()
        
        mock_print.assert_called_with("Удаление отменено")
    
    @patch('src.db.tui._read_int')
    @patch('src.db.tui.select_record')
    @patch('src.db.tui.input')
    @patch('src.db.tui.delete_record')
    @patch('src.db.tui.print')
    def test_delete_student_not_found(self, mock_print, mock_delete, mock_input, mock_select, mock_read_int):
        """Тест удаления несуществующего студента (строки 215, 218)"""
        mock_read_int.return_value = 999
        mock_select.return_value = []
        
        tui._delete_student()
        
        expected_text = "Запись с id=999 не найдена"
        found = False
        for call_args in mock_print.call_args_list:
            args = call_args[0]
            if args and expected_text in args[0]:
                found = True
                break
        self.assertTrue(found, f"Текст '{expected_text}' не найден")
    
    @patch('src.db.tui._read_int')
    @patch('src.db.tui.select_record')
    @patch('src.db.tui.input')
    @patch('src.db.tui.delete_record')
    @patch('src.db.tui.print')
    def test_delete_student_failed(self, mock_print, mock_delete, mock_input, mock_select, mock_read_int):
        """Тест неудачного удаления (строки 221, 224)"""
        mock_read_int.return_value = 1
        mock_select.return_value = [(1, "John", "Doe", 20, "M")]
        mock_input.return_value = "д"
        mock_delete.return_value = False
        
        tui._delete_student()
        
        expected_text = "Не удалось удалить запись"
        found = False
        for call_args in mock_print.call_args_list:
            args = call_args[0]
            if args and expected_text in args[0]:
                found = True
                break
        self.assertTrue(found, f"Текст '{expected_text}' не найден")
    
    # ===== Тесты для _show_tables =====
    @patch('src.db.tui.list_tables')
    @patch('src.db.tui.get_table')
    @patch('src.db.tui.print')
    def test_show_tables(self, mock_print, mock_get_table, mock_list_tables):
        """Тест показа всех таблиц (строки 35-39)"""
        mock_list_tables.return_value = ["Student", "Teachers"]
        mock_get_table.side_effect = [[(1, "John")], []]
        
        tui._show_tables()
        
        self.assertTrue(mock_print.call_count >= 3)
    
    @patch('src.db.tui.list_tables')
    @patch('src.db.tui.get_table')
    @patch('src.db.tui.print')
    def test_show_tables_empty(self, mock_print, mock_get_table, mock_list_tables):
        """Тест показа пустых таблиц"""
        mock_list_tables.return_value = []
        
        tui._show_tables()
        
        # Не должно быть ошибок
        self.assertTrue(True)
    
    # ===== Тесты для _create_new_table =====
    @patch('src.db.tui.list_tables')
    @patch('src.db.tui.input')
    @patch('src.db.tui.create_table')
    @patch('src.db.tui.print')
    def test_create_new_table_success(self, mock_print, mock_create, mock_input, mock_list):
        """Тест успешного создания таблицы (строки 22-30)"""
        mock_list.return_value = ["Student", "Teachers"]
        mock_input.return_value = "NewTable"
        mock_create.return_value = True
        
        tui._create_new_table()
        
        mock_create.assert_called_with("NewTable")
    
    @patch('src.db.tui.list_tables')
    @patch('src.db.tui.input')
    @patch('src.db.tui.create_table')
    @patch('src.db.tui.print')
    def test_create_new_table_value_error(self, mock_print, mock_create, mock_input, mock_list):
        """Тест создания таблицы с ошибкой"""
        mock_list.return_value = ["Student", "Teachers"]
        mock_input.return_value = ""
        mock_create.side_effect = ValueError("Имя таблицы не может быть пустым")
        
        tui._create_new_table()
        
        expected_text = "Имя таблицы не может быть пустым"
        found = False
        for call_args in mock_print.call_args_list:
            args = call_args[0]
            if args and expected_text in args[0]:
                found = True
                break
        self.assertTrue(found, f"Текст '{expected_text}' не найден")
    
    @patch('src.db.tui.list_tables')
    @patch('src.db.tui.input')
    @patch('src.db.tui.create_table')
    @patch('src.db.tui.print')
    def test_create_new_table_duplicate(self, mock_print, mock_create, mock_input, mock_list):
        """Тест создания дублирующейся таблицы"""
        mock_list.return_value = ["Student", "Teachers", "NewTable"]
        mock_input.return_value = "NewTable"
        mock_create.return_value = False
        
        tui._create_new_table()
        
        # Не должно быть ошибок
        self.assertTrue(True)
    
    # ===== Тесты для _print_menu =====
    @patch('src.db.tui.print')
    def test_print_menu(self, mock_print):
        """Тест печати меню (строки 9-17)"""
        tui._print_menu()
        
        # Должно быть несколько вызовов print
        self.assertTrue(mock_print.call_count >= 8)
    
    # ===== Тесты для run =====
    @patch('src.db.tui._print_menu')
    @patch('src.db.tui.input')
    @patch('src.db.tui._add_student')
    def test_run_add_student(self, mock_add, mock_input, mock_menu):
        """Тест run с выбором 1 (строки 227, 230)"""
        mock_input.side_effect = ["1", "0"]
        
        with patch('src.db.tui.print'):
            tui.run()
        
        mock_add.assert_called_once()
    
    @patch('src.db.tui._print_menu')
    @patch('src.db.tui.input')
    @patch('src.db.tui._show_all_students')
    def test_run_show_all(self, mock_show, mock_input, mock_menu):
        """Тест run с выбором 2"""
        mock_input.side_effect = ["2", "0"]
        
        with patch('src.db.tui.print'):
            tui.run()
        
        mock_show.assert_called_once()
    
    @patch('src.db.tui._print_menu')
    @patch('src.db.tui.input')
    @patch('src.db.tui._find_students_by_filter')
    def test_run_find(self, mock_find, mock_input, mock_menu):
        """Тест run с выбором 3"""
        mock_input.side_effect = ["3", "0"]
        
        with patch('src.db.tui.print'):
            tui.run()
        
        mock_find.assert_called_once()
    
    @patch('src.db.tui._print_menu')
    @patch('src.db.tui.input')
    @patch('src.db.tui._update_student')
    def test_run_update(self, mock_update, mock_input, mock_menu):
        """Тест run с выбором 4"""
        mock_input.side_effect = ["4", "0"]
        
        with patch('src.db.tui.print'):
            tui.run()
        
        mock_update.assert_called_once()
    
    @patch('src.db.tui._print_menu')
    @patch('src.db.tui.input')
    @patch('src.db.tui._delete_student')
    def test_run_delete(self, mock_delete, mock_input, mock_menu):
        """Тест run с выбором 5"""
        mock_input.side_effect = ["5", "0"]
        
        with patch('src.db.tui.print'):
            tui.run()
        
        mock_delete.assert_called_once()
    
    @patch('src.db.tui._print_menu')
    @patch('src.db.tui.input')
    @patch('src.db.tui._create_new_table')
    def test_run_create_table(self, mock_create, mock_input, mock_menu):
        """Тест run с выбором 6"""
        mock_input.side_effect = ["6", "0"]
        
        with patch('src.db.tui.print'):
            tui.run()
        
        mock_create.assert_called_once()
    
    @patch('src.db.tui._print_menu')
    @patch('src.db.tui.input')
    @patch('src.db.tui._show_tables')
    def test_run_show_tables(self, mock_show_tables, mock_input, mock_menu):
        """Тест run с выбором 7 (строки 233)"""
        mock_input.side_effect = ["7", "0"]
        
        with patch('src.db.tui.print'):
            tui.run()
        
        mock_show_tables.assert_called_once()
    
    @patch('src.db.tui._print_menu')
    @patch('src.db.tui.input')
    def test_run_invalid_choice(self, mock_input, mock_menu):
        """Тест run с неверным выбором"""
        mock_input.side_effect = ["99", "0"]
        
        with patch('src.db.tui.print') as mock_print:
            tui.run()
            
            error_found = False
            exit_found = False
            for call_args in mock_print.call_args_list:
                args = call_args[0]
                if args:
                    if "Неизвестная команда" in args[0]:
                        error_found = True
                    if "Выход из программы" in args[0]:
                        exit_found = True
            
            self.assertTrue(error_found, "Сообщение об ошибке не найдено")
            self.assertTrue(exit_found, "Сообщение о выходе не найдено")
    
    @patch('src.db.tui._print_menu')
    @patch('src.db.tui.input')
    def test_run_exit(self, mock_input, mock_menu):
        """Тест выхода из программы"""
        mock_input.return_value = "0"
        
        with patch('src.db.tui.print') as mock_print:
            tui.run()
            
            exit_found = False
            for call_args in mock_print.call_args_list:
                args = call_args[0]
                if args and "Выход из программы" in args[0]:
                    exit_found = True
                    break
            
            self.assertTrue(exit_found, "Сообщение о выходе не найдено")

if __name__ == "__main__":
    unittest.main()