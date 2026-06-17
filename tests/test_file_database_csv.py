import sys
import os
import tempfile
import shutil
import unittest
import csv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.db.backend.file_database_csv import CSVDatabase, CSVTable, CSVStudentTable
from src.db.backend.errors import InvalidAgeError, FileDatabaseError, RecordNotFoundError


class TestCSVDatabase(unittest.TestCase):
    """Тесты для CSV-базы данных"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db = CSVDatabase(data_dir=self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_create_table(self):
        table = self.db.create_table("Users")
        self.assertEqual(table.name, "Users")
        self.assertIn("Users", self.db.list_tables())
        file_path = os.path.join(self.temp_dir, "Users.csv")
        self.assertTrue(os.path.exists(file_path))
    
    def test_create_student_table(self):
        table = self.db.create_table("Student")
        self.assertIsInstance(table, CSVStudentTable)
        self.assertEqual(table.name, "Student")
    
    def test_persistence_after_reload(self):
        self.db.create_table("PersistTest")
        table = self.db.get_table("PersistTest")
        record = table.insert({"name": "Test User", "age": 30})
        
        new_db = CSVDatabase(data_dir=self.temp_dir)
        loaded_table = new_db.get_table("PersistTest")
        self.assertIsNotNone(loaded_table)
        self.assertEqual(len(loaded_table), 1)
        loaded_record = loaded_table.get(record.id)
        self.assertEqual(loaded_record.data["name"], "Test User")
        self.assertEqual(loaded_record.data["age"], 30)
    
    def test_insert_saves_to_csv(self):
        self.db.create_table("SaveTest")
        table = self.db.get_table("SaveTest")
        table.insert({"name": "John", "age": 25})
        
        file_path = os.path.join(self.temp_dir, "SaveTest.csv")
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['name'], "John")
        self.assertEqual(int(rows[0]['age']), 25)
        self.assertEqual(int(rows[0]['id']), 1)
    
    def test_update_saves_to_csv(self):
        self.db.create_table("UpdateTest")
        table = self.db.get_table("UpdateTest")
        table.insert({"name": "Old"})
        table.update(1, {"name": "New"})
        
        with open(os.path.join(self.temp_dir, "UpdateTest.csv"), 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        self.assertEqual(rows[0]['name'], "New")
    
    def test_delete_saves_to_csv(self):
        self.db.create_table("DeleteTest")
        table = self.db.get_table("DeleteTest")
        table.insert({"value": "test"})
        table.delete(1)
        
        with open(os.path.join(self.temp_dir, "DeleteTest.csv"), 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        self.assertEqual(len(rows), 0)
    
    def test_drop_table_removes_file(self):
        self.db.create_table("ToDrop")
        file_path = os.path.join(self.temp_dir, "ToDrop.csv")
        self.assertTrue(os.path.exists(file_path))
        
        result = self.db.drop_table("ToDrop")
        self.assertTrue(result)
        self.assertFalse(os.path.exists(file_path))
        self.assertNotIn("ToDrop", self.db.list_tables())
    
    def test_create_duplicate_table(self):
        self.db.create_table("Unique")
        with self.assertRaises(ValueError):
            self.db.create_table("Unique")
    
    def test_empty_table_name(self):
        with self.assertRaises(ValueError):
            self.db.create_table("")
    
    def test_student_age_validation(self):
        self.db.create_table("Student")
        table = self.db.get_table("Student")
        
        with self.assertRaises(InvalidAgeError):
            table.insert({"first_name": "Bad", "second_name": "Age", "age": -5, "sex": "M"})
        
        with self.assertRaises(InvalidAgeError):
            table.insert({"first_name": "Too", "second_name": "Old", "age": 200, "sex": "M"})
        
        record = table.insert({"first_name": "Good", "second_name": "Age", "age": 25, "sex": "M"})
        self.assertEqual(record.data["age"], 25)
    
    def test_multiple_tables(self):
        self.db.create_table("TableA")
        self.db.create_table("TableB")
        self.db.create_table("TableC")
        
        tables = self.db.list_tables()
        self.assertEqual(len(tables), 3)
    
    def test_find_records(self):
        self.db.create_table("FindTest")
        table = self.db.get_table("FindTest")
        table.insert({"name": "John", "age": 25})
        table.insert({"name": "Jane", "age": 25})
        table.insert({"name": "Bob", "age": 30})
        
        results = table.find(age=25)
        self.assertEqual(len(results), 2)
        
        results = table.find(name="Bob")
        self.assertEqual(len(results), 1)
    
    def test_sort_records(self):
        self.db.create_table("SortTest")
        table = self.db.get_table("SortTest")
        table.insert({"name": "Zebra", "age": 30})
        table.insert({"name": "Apple", "age": 20})
        table.insert({"name": "Cat", "age": 25})
        
        sorted_asc = table.sort("name")
        self.assertEqual([r.data["name"] for r in sorted_asc], ["Apple", "Cat", "Zebra"])
        
        sorted_desc = table.sort("age", reverse=True)
        self.assertEqual([r.data["age"] for r in sorted_desc], [30, 25, 20])
    
    def test_clear_table(self):
        self.db.create_table("ClearTest")
        table = self.db.get_table("ClearTest")
        table.insert({"name": "John"})
        table.insert({"name": "Jane"})
        self.assertEqual(len(table), 2)
        
        table.clear()
        self.assertEqual(len(table), 0)
        
        # Проверяем, что файл очистился
        new_db = CSVDatabase(data_dir=self.temp_dir)
        new_table = new_db.get_table("ClearTest")
        self.assertEqual(len(new_table), 0)


class TestCSVTable(unittest.TestCase):
    """Тесты для CSVTable"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_csv_table_init_creates_file(self):
        table = CSVTable("InitTest", self.temp_dir)
        file_path = os.path.join(self.temp_dir, "InitTest.csv")
        self.assertTrue(os.path.exists(file_path))
    
    def test_csv_table_loads_existing_data(self):
        table1 = CSVTable("LoadTest", self.temp_dir)
        table1.insert({"value": "persisted"})
        
        table2 = CSVTable("LoadTest", self.temp_dir)
        self.assertEqual(len(table2), 1)
        self.assertEqual(table2.get(1).data["value"], "persisted")
    
    def test_csv_handles_different_types(self):
        table = CSVTable("TypesTest", self.temp_dir)
        table.insert({
            "string_field": "hello",
            "int_field": 42,
            "float_field": 3.14,
            "bool_field": True
        })
        
        # Перезагружаем и проверяем типы
        new_table = CSVTable("TypesTest", self.temp_dir)
        record = new_table.get(1)
        self.assertEqual(record.data["string_field"], "hello")
        self.assertEqual(record.data["int_field"], 42)
        self.assertEqual(record.data["float_field"], 3.14)
        self.assertEqual(record.data["bool_field"], True)


class TestCSVTableExtended(unittest.TestCase):
    """Расширенные тесты для CSVTable"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_csv_table_basic_operations(self):
        """Тест базовых операций CSVTable"""
        table = CSVTable("BasicTest", self.temp_dir)
        
        # insert
        record = table.insert({"name": "John", "age": 25})
        self.assertEqual(record.id, 1)
        
        # get
        self.assertEqual(table.get(1).data["name"], "John")
        self.assertIsNone(table.get(999))
        
        # len и count
        self.assertEqual(len(table), 1)
        self.assertEqual(table.count(), 1)
        
        # all
        self.assertEqual(len(table.all()), 1)
        
        # update
        table.update(1, {"age": 30})
        self.assertEqual(table.get(1).data["age"], 30)
        
        # delete
        table.delete(1)
        self.assertEqual(len(table), 0)
        
        # clear
        table.insert({"name": "Test"})
        table.clear()
        self.assertEqual(len(table), 0)
    
    def test_csv_table_find_and_sort(self):
        """Тест find и sort для CSVTable"""
        table = CSVTable("FindSortTest", self.temp_dir)
        table.insert({"name": "Zebra", "age": 30})
        table.insert({"name": "Apple", "age": 20})
        table.insert({"name": "Cat", "age": 25})
        
        # find
        results = table.find(age=25)
        self.assertEqual(len(results), 1)
        
        results = table.find()
        self.assertEqual(len(results), 3)
        
        # sort
        sorted_by_name = table.sort("name")
        self.assertEqual([r.data["name"] for r in sorted_by_name], ["Apple", "Cat", "Zebra"])
        
        sorted_by_age_desc = table.sort("age", reverse=True)
        self.assertEqual([r.data["age"] for r in sorted_by_age_desc], [30, 25, 20])
    
    def test_csv_table_student_validation(self):
        """Тест студенческой CSV таблицы"""
        table = CSVStudentTable(self.temp_dir)
        
        # Валидный студент
        record = table.insert({"name": "John", "age": 20})
        self.assertEqual(record.data["age"], 20)
        
        # Невалидный возраст
        with self.assertRaises(InvalidAgeError):
            table.insert({"name": "Bad", "age": -5})
        
        # Обновление
        table.update(1, {"age": 25})
        self.assertEqual(table.get(1).data["age"], 25)
        
        with self.assertRaises(InvalidAgeError):
            table.update(1, {"age": -10})
    
    def test_csv_database_operations(self):
        """Тест операций CSVDatabase"""
        db = CSVDatabase(data_dir=self.temp_dir)
        
        # Создание таблиц
        table1 = db.create_table("Table1")
        table2 = db.create_table("Table2")
        
        self.assertIn("Table1", db.list_tables())
        self.assertIn("Table2", db.list_tables())
        
        # Получение таблиц
        self.assertIsNotNone(db.get_table("Table1"))
        self.assertIsNone(db.get_table("NonExistent"))
        
        # Удаление таблицы
        db.drop_table("Table1")
        self.assertNotIn("Table1", db.list_tables())
        
        # Студенческая таблица
        student = db.create_table("Student")
        self.assertIsInstance(student, CSVStudentTable)

    def test_csv_error_handling(self):
        """Тест обработки ошибок CSV - повреждённый файл"""
        # Создаём повреждённый CSV файл
        file_path = os.path.join(self.temp_dir, "BadTable.csv")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("corrupted,csv,file\nno,headers")
        
        # Должна создаться пустая таблица без ошибки
        table = CSVTable("BadTable", self.temp_dir)
        self.assertEqual(len(table), 0)
        self.assertEqual(table._next_id, 1)
    
    def test_csv_missing_file(self):
        """Тест: загрузка несуществующего файла создаёт пустую таблицу"""
        table = CSVTable("NonExistent", self.temp_dir)
        self.assertEqual(len(table), 0)
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, "NonExistent.csv")))
    
    def test_csv_parse_value_edge_cases(self):
        """Тест парсинга значений CSV"""
        table = CSVTable("ParseTest", self.temp_dir)
        
        # Тест через реальную вставку и перезагрузку
        table.insert({
            "empty": "",
            "true_bool": True,
            "false_bool": False,
            "int_zero": 0,
            "float_zero": 0.0
        })
        
        # Перезагружаем и проверяем
        new_table = CSVTable("ParseTest", self.temp_dir)
        record = new_table.get(1)
        
        self.assertIsNone(record.data.get("empty"))
        self.assertEqual(record.data["true_bool"], True)
        self.assertEqual(record.data["false_bool"], False)
        self.assertEqual(record.data["int_zero"], 0)
        self.assertEqual(record.data["float_zero"], 0.0)
    
    def test_csv_update_headers(self):
        """Тест обновления заголовков при добавлении новых полей"""
        table = CSVTable("HeadersTest", self.temp_dir)
        
        # Первая запись - создаёт заголовки
        table.insert({"name": "John", "age": 25})
        
        # Вторая запись с новым полем - должно обновить заголовки
        table.insert({"name": "Jane", "age": 30, "city": "Moscow"})
        
        # Перезагружаем и проверяем
        new_table = CSVTable("HeadersTest", self.temp_dir)
        self.assertEqual(len(new_table), 2)
        self.assertEqual(new_table.get(2).data["city"], "Moscow")
    
    def test_csv_drop_table_error(self):
        """Тест удаления таблицы с ошибкой"""
        db = CSVDatabase(data_dir=self.temp_dir)
        db.create_table("ToDrop")
        
        # Удаляем файл вручную
        file_path = os.path.join(self.temp_dir, "ToDrop.csv")
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # drop_table должен всё равно удалить таблицу из памяти
        result = db.drop_table("ToDrop")
        self.assertTrue(result)
        self.assertNotIn("ToDrop", db.list_tables())


class TestCSVTableErrorHandling(unittest.TestCase):
    """Тесты для обработки ошибок CSVTable"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        try:
            shutil.rmtree(self.temp_dir)
        except PermissionError:
            pass  # Игнорируем ошибки доступа при удалении
    
    def test_csv_load_corrupted_file(self):
        """Тест загрузки повреждённого CSV файла"""
        file_path = os.path.join(self.temp_dir, "Corrupted.csv")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("corrupted,csv,file\nno,headers")
        
        table = CSVTable("Corrupted", self.temp_dir)
        self.assertEqual(len(table), 0)
        self.assertEqual(table._next_id, 1)
    
    def test_csv_parse_value_edge_cases(self):
        """Тест парсинга значений CSV"""
        table = CSVTable("ParseTest", self.temp_dir)
        
        table.insert({
            "empty": "",
            "true_bool": True,
            "false_bool": False,
            "int_zero": 0,
            "float_zero": 0.0,
            "string_number": "123abc"
        })
        
        new_table = CSVTable("ParseTest", self.temp_dir)
        record = new_table.get(1)
        
        self.assertIsNone(record.data.get("empty"))
        self.assertEqual(record.data["true_bool"], True)
        self.assertEqual(record.data["false_bool"], False)
        self.assertEqual(record.data["int_zero"], 0)
        self.assertEqual(record.data["float_zero"], 0.0)
        self.assertEqual(record.data["string_number"], "123abc")
    
    def test_csv_update_headers_dynamic(self):
        """Тест динамического обновления заголовков"""
        table = CSVTable("HeadersTest", self.temp_dir)
        
        table.insert({"name": "John", "age": 25})
        table.insert({"name": "Jane", "age": 30, "city": "Moscow", "country": "Russia"})
        table.insert({"name": "Bob", "age": 35, "city": "SPB"})
        
        new_table = CSVTable("HeadersTest", self.temp_dir)
        self.assertEqual(len(new_table), 3)
        self.assertEqual(new_table.get(2).data["city"], "Moscow")
        self.assertEqual(new_table.get(2).data["country"], "Russia")
        self.assertEqual(new_table.get(3).data["city"], "SPB")
        self.assertIsNone(new_table.get(3).data.get("country"))
    
    def test_csv_table_all_methods(self):
        """Тест всех методов таблицы"""
        table = CSVTable("AllMethodsTest", self.temp_dir)
        
        self.assertEqual(len(table), 0)
        self.assertEqual(table.count(), 0)
        self.assertEqual(table.all(), [])
        
        table.insert({"name": "John"})
        table.insert({"name": "Jane"})
        
        self.assertEqual(len(table), 2)
        self.assertEqual(table.count(), 2)
        self.assertEqual(len(table.all()), 2)
        
        records = list(table)
        self.assertEqual(len(records), 2)
    
    def test_csv_find_with_no_criteria(self):
        """Тест find без критериев"""
        table = CSVTable("FindAllTest", self.temp_dir)
        table.insert({"name": "John"})
        table.insert({"name": "Jane"})
        
        results = table.find()
        self.assertEqual(len(results), 2)
    
    def test_csv_find_with_nonexistent_field(self):
        """Тест find с несуществующим полем"""
        table = CSVTable("FindNonexistentTest", self.temp_dir)
        table.insert({"name": "John"})
        
        results = table.find(age=25)
        self.assertEqual(len(results), 0)
    
    def test_csv_sort_empty_table(self):
        """Тест сортировки пустой таблицы"""
        table = CSVTable("SortEmptyTest", self.temp_dir)
        sorted_records = table.sort("any_field")
        self.assertEqual(sorted_records, [])
    
    def test_csv_clear_empty_table(self):
        """Тест очистки пустой таблицы"""
        table = CSVTable("ClearEmptyTest", self.temp_dir)
        table.clear()
        self.assertEqual(len(table), 0)
    
    def test_csv_delete_nonexistent(self):
        """Тест удаления несуществующей записи"""
        table = CSVTable("DeleteNonexistentTest", self.temp_dir)
        result = table.delete(999)
        self.assertFalse(result)
    
    def test_csv_update_nonexistent(self):
        """Тест обновления несуществующей записи"""
        table = CSVTable("UpdateNonexistentTest", self.temp_dir)
        with self.assertRaises(RecordNotFoundError):
            table.update(999, {"name": "Test"})
    
    def test_csv_database_create_duplicate(self):
        """Тест создания дублирующейся таблицы"""
        db = CSVDatabase(data_dir=self.temp_dir)
        db.create_table("Unique")
        with self.assertRaises(ValueError):
            db.create_table("Unique")
    
    def test_csv_database_empty_name(self):
        """Тест создания таблицы с пустым именем"""
        db = CSVDatabase(data_dir=self.temp_dir)
        with self.assertRaises(ValueError):
            db.create_table("")
    
    def test_csv_database_get_nonexistent(self):
        """Тест получения несуществующей таблицы"""
        db = CSVDatabase(data_dir=self.temp_dir)
        table = db.get_table("NonExistent")
        self.assertIsNone(table)
    
    def test_csv_database_drop_table(self):
        """Тест удаления таблицы"""
        db = CSVDatabase(data_dir=self.temp_dir)
        db.create_table("ToDrop")
        self.assertIn("ToDrop", db.list_tables())
        
        result = db.drop_table("ToDrop")
        self.assertTrue(result)
        self.assertNotIn("ToDrop", db.list_tables())

if __name__ == "__main__":
    unittest.main()