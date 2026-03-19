# tests/test_memory.py
import unittest
from src.db.backend.memory import Database, StudentTable, Table
from src.db.backend.errors import InvalidAgeError, DuplicateIDError, StudentTableError


class TestTable(unittest.TestCase):
    """Тесты для базового класса Table"""
    
    def setUp(self):
        self.table = Table("Test")
    
    def test_table_init(self):
        """Тест инициализации таблицы"""
        self.assertEqual(self.table.name, "Test")
        self.assertEqual(self.table.count(), 0)
    
    def test_table_all(self):
        """Тест получения всех записей"""
        self.table._records.append((1, "test"))
        records = self.table.all()
        self.assertEqual(records, [(1, "test")])
    
    def test_table_all_returns_copy(self):
        """Тест, что all() возвращает копию"""
        self.table._records.append((1, "test"))
        records = self.table.all()
        records.append((2, "new"))
        self.assertEqual(len(self.table.all()), 1)  
    
    def test_table_count(self):
        """Тест подсчета записей"""
        self.assertEqual(self.table.count(), 0)
        self.table._records.append((1, "test"))
        self.assertEqual(self.table.count(), 1)
    
    def test_table_clear(self):
        """Тест очистки таблицы"""
        self.table._records.append((1, "test"))
        self.table._records.append((2, "test2"))
        self.assertEqual(self.table.count(), 2)
        self.table.clear()
        self.assertEqual(self.table.count(), 0)

    def test_table_all_empty(self):
        """Тест all() для пустой таблицы"""
        self.assertEqual(self.table.all(), [])

    def test_table_all_modification_doesnt_affect_original(self):
        """Тест, что изменение копии не влияет на оригинал"""
        self.table._records.append((1, "test"))
        records_copy = self.table.all()
        records_copy.clear()
        self.assertEqual(len(self.table.all()), 1)


class TestStudentTable(unittest.TestCase):
    """Тесты для таблицы студентов"""
    
    def setUp(self):
        self.table = StudentTable()
    
    def test_create_record_valid(self):
        """Тест создания валидной записи"""
        cases = [
            (1, "John", "Doe", 20, "M"),
            (2, "Jane", "Smith", 22, "F"),
            (3, "Alice", "Johnson", 19, "F"),
        ]
        
        for test_data in cases:
            with self.subTest(test_data=test_data):
                record = self.table.create_record(*test_data)
                self.assertEqual(record, test_data)
        
        self.assertEqual(self.table.count(), 3)
    
    def test_create_record_strip_spaces(self):
        """Тест удаления пробелов в строковых полях"""
        record = self.table.create_record(1, "  John  ", "  Doe  ", 20, "  M  ")
        self.assertEqual(record, (1, "John", "Doe", 20, "M"))
    
    def test_create_record_negative_age(self):
        """Тест создания записи с отрицательным возрастом"""
        cases = [
            (1, "John", "Doe", -1, "M"),
            (2, "Jane", "Smith", -5, "F"),
            (3, "Alice", "Johnson", -10, "F"),
        ]
        error_message = "Поле age не может быть отрицательным."
        
        for test_data in cases:
            with self.subTest(test_data=test_data):
                with self.assertRaises(InvalidAgeError) as context:
                    self.table.create_record(*test_data)
                
                self.assertEqual(str(context.exception), error_message)
                self.assertIsInstance(context.exception, StudentTableError)
        
        self.assertEqual(self.table.count(), 0)
    
    def test_create_record_zero_age(self):
        """Тест создания записи с нулевым возрастом (должно работать)"""
        record = self.table.create_record(1, "John", "Doe", 0, "M")
        self.assertEqual(record[3], 0)
    
    def test_create_record_duplicate_id(self):
        """Тест создания записи с дублирующимся ID"""
        self.table.create_record(1, "John", "Doe", 20, "M")
        
        with self.assertRaises(DuplicateIDError) as context:
            self.table.create_record(1, "Jane", "Smith", 22, "F")
        
        self.assertEqual(str(context.exception), "Запись с id=1 уже существует.")
        self.assertIsInstance(context.exception, StudentTableError)
        self.assertEqual(self.table.count(), 1)
    
    def test_select_record_no_filters(self):
        """Тест выборки всех записей без фильтров"""
        records = [
            (1, "John", "Doe", 20, "M"),
            (2, "Jane", "Smith", 22, "F"),
        ]
        
        for record in records:
            self.table.create_record(*record)
        
        result = self.table.select_record()
        self.assertEqual(len(result), 2)
        self.assertEqual(result, records)
    
    def test_select_record_with_all_none_filters(self):
        """Тест выборки когда все фильтры None"""
        self.table.create_record(1, "John", "Doe", 20, "M")
        result = self.table.select_record(
            student_id=None,
            first_name=None,
            second_name=None,
            age=None,
            sex=None
        )
        self.assertEqual(len(result), 1)
    
    def test_select_record_with_filters(self):
        """Тест выборки с фильтрами"""
        self.table.create_record(1, "John", "Doe", 20, "M")
        self.table.create_record(2, "Jane", "Smith", 22, "F")
        self.table.create_record(3, "John", "Smith", 25, "M")
        
        # Фильтр по ID
        result = self.table.select_record(student_id=1)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][1], "John")
        
        # Фильтр по имени
        result = self.table.select_record(first_name="John")
        self.assertEqual(len(result), 2)
        
        # Фильтр по фамилии
        result = self.table.select_record(second_name="Smith")
        self.assertEqual(len(result), 2)
        
        # Фильтр по возрасту
        result = self.table.select_record(age=20)
        self.assertEqual(len(result), 1)
        
        # Фильтр по полу
        result = self.table.select_record(sex="F")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][1], "Jane")
        
        # Комбинированный фильтр
        result = self.table.select_record(first_name="John", sex="M")
        self.assertEqual(len(result), 2)
        
        # Фильтр без совпадений
        result = self.table.select_record(age=99)
        self.assertEqual(len(result), 0)
    
    def test_update_record(self):
        """Тест обновления записи"""
        self.table.create_record(1, "John", "Doe", 20, "M")
        
        updated = self.table.update_record(1, first_name="Johnny", age=21)
        
        self.assertIsNotNone(updated)
        self.assertEqual(updated[1], "Johnny")
        self.assertEqual(updated[3], 21)
        self.assertEqual(updated[2], "Doe")  # Не менялось
        
        # Проверяем, что запись действительно обновилась
        record = self.table.get_by_id(1)
        self.assertEqual(record[1], "Johnny")
        self.assertEqual(record[3], 21)
    
    def test_update_record_not_found(self):
        """Тест обновления несуществующей записи (строка 114, 116)"""
        result = self.table.update_record(999, first_name="New")
        self.assertIsNone(result)
    
    def test_update_record_negative_age(self):
        """Тест обновления с отрицательным возрастом"""
        self.table.create_record(1, "John", "Doe", 20, "M")
        
        with self.assertRaises(InvalidAgeError):
            self.table.update_record(1, age=-5)
        
        # Проверяем, что запись не изменилась
        record = self.table.get_by_id(1)
        self.assertEqual(record[3], 20)
    
    def test_update_record_partial(self):
        """Тест частичного обновления"""
        self.table.create_record(1, "John", "Doe", 20, "M")
        
        # Обновляем только имя
        updated = self.table.update_record(1, first_name="Johnny")
        self.assertEqual(updated, (1, "Johnny", "Doe", 20, "M"))
        
        # Обновляем только возраст
        updated = self.table.update_record(1, age=25)
        self.assertEqual(updated, (1, "Johnny", "Doe", 25, "M"))
    
    def test_delete_record(self):
        """Тест удаления записи"""
        self.table.create_record(1, "John", "Doe", 20, "M")
        self.table.create_record(2, "Jane", "Smith", 22, "F")
        
        self.assertEqual(self.table.count(), 2)
        
        result = self.table.delete_record(1)
        
        self.assertTrue(result)
        self.assertEqual(self.table.count(), 1)
        self.assertIsNone(self.table.get_by_id(1))
        self.assertIsNotNone(self.table.get_by_id(2))
    
    def test_delete_record_not_found(self):
        """Тест удаления несуществующей записи (строка 161)"""
        result = self.table.delete_record(999)
        self.assertFalse(result)
    
    def test_get_by_id(self):
        """Тест получения записи по ID"""
        self.table.create_record(1, "John", "Doe", 20, "M")
        
        # Существующий ID
        record = self.table.get_by_id(1)
        self.assertIsNotNone(record)
        self.assertEqual(record[0], 1)
    
    def test_get_by_id_not_found(self):
        """Тест получения несуществующей записи (строка 166)"""
        record = self.table.get_by_id(999)
        self.assertIsNone(record)

    def test_update_record_no_changes(self):
        """Тест обновления без изменений"""
        self.table.create_record(1, "John", "Doe", 20, "M")
        
        # Обновляем с None для всех полей
        updated = self.table.update_record(1, None, None, None, None)
        
        self.assertIsNotNone(updated)
        self.assertEqual(updated, (1, "John", "Doe", 20, "M"))


class TestDatabase(unittest.TestCase):
    """Тесты для класса Database"""
    
    def setUp(self):
        self.db = Database()
    
    def test_init_default_tables(self):
        """Тест инициализации таблиц по умолчанию"""
        tables = self.db.list_tables()
        self.assertIn("Student", tables)
        self.assertIn("Teachers", tables)
        self.assertEqual(len(tables), 2)
    
    def test_create_table(self):
        """Тест создания новой таблицы"""
        result = self.db.create_table("NewTable")
        
        self.assertTrue(result)
        self.assertIn("NewTable", self.db.list_tables())
        
        table = self.db.get_table("NewTable")
        self.assertIsInstance(table, Table)
        self.assertEqual(table.name, "NewTable")
    
    def test_create_table_empty_name(self):
        """Тест создания таблицы с пустым именем (строка 183)"""
        with self.assertRaises(ValueError) as context:
            self.db.create_table("")
        self.assertEqual(str(context.exception), "Имя таблицы не может быть пустым")
        
        with self.assertRaises(ValueError):
            self.db.create_table("   ")
    
    def test_create_table_duplicate(self):
        """Тест создания дублирующейся таблицы (строка 247)"""
        self.db.create_table("Test")
        result = self.db.create_table("Test")
        self.assertFalse(result)
    
    def test_create_table_student_special(self):
        """Тест создания таблицы Student (должна быть StudentTable)"""
        self.db.create_table("Student")  
        table = self.db.get_table("Student")
        self.assertIsInstance(table, StudentTable)
    
    def test_get_student_table(self):
        """Тест получения таблицы Student"""
        table = self.db.get_table("Student")
        self.assertIsInstance(table, StudentTable)
        
        student_table = self.db.get_student_table()
        self.assertIsInstance(student_table, StudentTable)
        self.assertIs(table, student_table)
    
    def test_get_student_table_none(self):
        """Тест получения Student таблицы когда её нет"""
        # Создаем новую БД без таблиц
        db = Database()
        db._tables.clear()
        self.assertIsNone(db.get_student_table())
    
    def test_delete_table(self):
        """Тест удаления таблицы"""
        self.db.create_table("TempTable")
        self.assertIn("TempTable", self.db.list_tables())
        
        result = self.db.delete_table("TempTable")
        
        self.assertTrue(result)
        self.assertNotIn("TempTable", self.db.list_tables())
    
    def test_delete_table_not_found(self):
        """Тест удаления несуществующей таблицы (строка 221)"""
        result = self.db.delete_table("NonExistent")
        self.assertFalse(result)
    
    def test_delete_table_student_forbidden(self):
        """Тест запрета удаления таблицы Student"""
        with self.assertRaises(ValueError) as context:
            self.db.delete_table("Student")
        self.assertEqual(str(context.exception), "Таблицу Student нельзя удалить")
        
        # Проверяем, что таблица все еще существует
        self.assertIn("Student", self.db.list_tables())
    
    def test_clear_all(self):
        """Тест очистки всех таблиц (строка 224)"""
        # Добавляем данные
        student_table = self.db.get_student_table()
        student_table.create_record(1, "John", "Doe", 20, "M")
        self.db.create_table("Extra")
        
        # Очищаем
        self.db.clear_all()
        
        # Проверяем, что таблицы по умолчанию восстановлены
        tables = self.db.list_tables()
        self.assertIn("Student", tables)
        self.assertIn("Teachers", tables)
        self.assertEqual(len(tables), 2)
        
        # Проверяем, что данные очищены
        student_table = self.db.get_student_table()
        self.assertEqual(student_table.count(), 0)

    def test_get_table_nonexistent(self):
        """Тест получения несуществующей таблицы"""
        table = self.db.get_table("NonExistent")
        self.assertIsNone(table)

    def test_delete_table_nonexistent(self):
        """Тест удаления несуществующей таблицы (строка 221)"""
        result = self.db.delete_table("NonExistent")
        self.assertFalse(result)

    def test_clear_all_with_data(self):
        """Тест полной очистки с данными (строка 224)"""
        # Добавляем данные в разные таблицы
        student_table = self.db.get_student_table()
        student_table.create_record(1, "John", "Doe", 20, "M")
        
        teachers_table = self.db.get_table("Teachers")
        teachers_table._records.append((1, "Teacher"))
        
        self.db.create_table("Extra")
        extra_table = self.db.get_table("Extra")
        extra_table._records.append((1, "Extra"))
        
        # Очищаем
        self.db.clear_all()
        
        # Проверяем
        self.assertEqual(self.db.get_student_table().count(), 0)
        self.assertEqual(len(self.db.get_table("Teachers")._records), 0)
        self.assertIsNone(self.db.get_table("Extra"))

    def test_get_student_table_none(self):
        """Тест получения Student таблицы когда её нет"""
        # Создаем новую БД и удаляем Student
        db = Database()
        db._tables.clear()  # Очищаем все таблицы
        db._tables["Teachers"] = Table("Teachers")  # Добавляем только Teachers
        
        self.assertIsNone(db.get_student_table())

class TestCompatibilityLayer(unittest.TestCase):
    """Тесты для слоя совместимости со старым API"""
    
    def setUp(self):
        from src.db.backend.memory import (
            create_record, select_record, update_record, delete_record,
            create_table, list_tables, get_table, delete_table, get_db
        )
        self.create_record = create_record
        self.select_record = select_record
        self.update_record = update_record
        self.delete_record = delete_record
        self.create_table = create_table
        self.list_tables = list_tables
        self.get_table = get_table
        self.delete_table = delete_table
        self.get_db = get_db
        
        # Очищаем базу перед каждым тестом
        db = self.get_db()
        db.clear_all()
    
    def test_create_record_compat(self):
        """Тест create_record из слоя совместимости"""
        record = self.create_record(1, "John", "Doe", 20, "M")
        self.assertEqual(record, (1, "John", "Doe", 20, "M"))
        
        # Проверяем, что запись действительно добавилась
        result = self.select_record(student_id=1)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], record)
    
    def test_select_record_compat(self):
        """Тест select_record из слоя совместимости"""
        self.create_record(1, "John", "Doe", 20, "M")
        self.create_record(2, "Jane", "Smith", 22, "F")
        
        all_records = self.select_record()
        self.assertEqual(len(all_records), 2)
        
        filtered = self.select_record(first_name="John")
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0][1], "John")
    
    def test_update_record_compat(self):
        """Тест update_record из слоя совместимости"""
        self.create_record(1, "John", "Doe", 20, "M")
        
        updated = self.update_record(1, first_name="Johnny")
        self.assertIsNotNone(updated)
        self.assertEqual(updated[1], "Johnny")
        
        result = self.select_record(student_id=1)
        self.assertEqual(result[0][1], "Johnny")
    
    def test_delete_record_compat(self):
        """Тест delete_record из слоя совместимости"""
        self.create_record(1, "John", "Doe", 20, "M")
        
        result = self.delete_record(1)
        self.assertTrue(result)
        self.assertEqual(len(self.select_record()), 0)
    
    def test_table_operations_compat(self):
        """Тест операций с таблицами из слоя совместимости"""
        result = self.create_table("TestTable")
        self.assertTrue(result)
        
        tables = self.list_tables()
        self.assertIn("TestTable", tables)
        
        table = self.get_table("TestTable")
        self.assertIsNotNone(table)
        
        result = self.delete_table("TestTable")
        self.assertTrue(result)
        self.assertNotIn("TestTable", self.list_tables())


if __name__ == "__main__":
    unittest.main()