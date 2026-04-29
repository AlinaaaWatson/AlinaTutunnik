"""Тесты для memory.py (ООП версия)"""
import sys
import os

# Добавляем папку src в путь поиска модулей
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import unittest
from db.backend.memory import Database, Table, StudentTable, Record
from db.backend.errors import InvalidAgeError, DuplicateIDError, RecordNotFoundError

class TestTable(unittest.TestCase):
    """Тесты для базового класса Table"""
    
    def setUp(self):
        self.table = Table("Test")
    
    def test_table_init(self):
        """Тест инициализации таблицы"""
        self.assertEqual(self.table.name, "Test")
        self.assertEqual(self.table.count(), 0)
        self.assertEqual(len(self.table), 0)
    
    def test_insert_record(self):
        """Тест добавления записи"""
        record = self.table.insert({"name": "John", "age": 25})
        self.assertEqual(record.id, 1)
        self.assertEqual(record.data["name"], "John")
        self.assertEqual(self.table.count(), 1)
        self.assertEqual(len(self.table), 1)
    
    def test_insert_multiple_records(self):
        """Тест добавления нескольких записей"""
        r1 = self.table.insert({"name": "John"})
        r2 = self.table.insert({"name": "Jane"})
        r3 = self.table.insert({"name": "Bob"})
        
        self.assertEqual(r1.id, 1)
        self.assertEqual(r2.id, 2)
        self.assertEqual(r3.id, 3)
        self.assertEqual(self.table.count(), 3)
    
    def test_get_record(self):
        """Тест получения записи по ID"""
        record = self.table.insert({"name": "John"})
        retrieved = self.table.get(1)
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, record.id)
        self.assertEqual(retrieved.data["name"], "John")
    
    def test_get_nonexistent_record(self):
        """Тест получения несуществующей записи"""
        retrieved = self.table.get(999)
        self.assertIsNone(retrieved)
    
    def test_update_record(self):
        """Тест обновления записи"""
        self.table.insert({"name": "John", "age": 20})
        updated = self.table.update(1, {"age": 25, "city": "Moscow"})
        
        self.assertEqual(updated.data["age"], 25)
        self.assertEqual(updated.data["city"], "Moscow")
        self.assertEqual(updated.data["name"], "John")
    
    def test_update_nonexistent_record(self):
        """Тест обновления несуществующей записи"""
        with self.assertRaises(RecordNotFoundError):
            self.table.update(999, {"name": "Test"})
    
    def test_delete_record(self):
        """Тест удаления записи"""
        self.table.insert({"name": "John"})
        self.table.insert({"name": "Jane"})
        self.assertEqual(self.table.count(), 2)
        
        result = self.table.delete(1)
        self.assertTrue(result)
        self.assertEqual(self.table.count(), 1)
        self.assertIsNone(self.table.get(1))
    
    def test_delete_nonexistent_record(self):
        """Тест удаления несуществующей записи"""
        result = self.table.delete(999)
        self.assertFalse(result)
    
    def test_find_records(self):
        """Тест поиска записей"""
        self.table.insert({"name": "John", "age": 25})
        self.table.insert({"name": "Jane", "age": 25})
        self.table.insert({"name": "Bob", "age": 30})
        
        results = self.table.find(age=25)
        self.assertEqual(len(results), 2)
        
        results = self.table.find(name="Bob")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].data["name"], "Bob")
        
        results = self.table.find(age=99)
        self.assertEqual(len(results), 0)
    
    def test_sort_by_id(self):
        """Тест сортировки по ID"""
        self.table.insert({"name": "Zebra"})
        self.table.insert({"name": "Apple"})
        self.table.insert({"name": "Cat"})
        
        sorted_asc = self.table.sort("id", reverse=False)
        self.assertEqual(sorted_asc[0].id, 1)
        self.assertEqual(sorted_asc[1].id, 2)
        self.assertEqual(sorted_asc[2].id, 3)
        
        sorted_desc = self.table.sort("id", reverse=True)
        self.assertEqual(sorted_desc[0].id, 3)
        self.assertEqual(sorted_desc[1].id, 2)
        self.assertEqual(sorted_desc[2].id, 1)
    
    def test_sort_by_field(self):
        """Тест сортировки по полю"""
        self.table.insert({"name": "Zebra", "age": 30})
        self.table.insert({"name": "Apple", "age": 20})
        self.table.insert({"name": "Cat", "age": 25})
        
        sorted_asc = self.table.sort("name", reverse=False)
        self.assertEqual([r.data["name"] for r in sorted_asc], ["Apple", "Cat", "Zebra"])
        
        sorted_desc = self.table.sort("age", reverse=True)
        self.assertEqual([r.data["age"] for r in sorted_desc], [30, 25, 20])
    
    def test_clear_table(self):
        """Тест очистки таблицы"""
        self.table.insert({"name": "John"})
        self.table.insert({"name": "Jane"})
        self.assertEqual(self.table.count(), 2)
        
        self.table.clear()
        self.assertEqual(self.table.count(), 0)
        self.assertEqual(len(self.table), 0)
        self.assertEqual(self.table.all(), [])
    
    def test_all_records(self):
        """Тест получения всех записей"""
        self.assertEqual(self.table.all(), [])
        
        r1 = self.table.insert({"name": "John"})
        r2 = self.table.insert({"name": "Jane"})
        
        all_records = self.table.all()
        self.assertEqual(len(all_records), 2)
        self.assertIn(r1, all_records)
        self.assertIn(r2, all_records)
    
    def test_iteration(self):
        """Тест итерации по таблице"""
        self.table.insert({"name": "John"})
        self.table.insert({"name": "Jane"})
        
        ids = []
        for record in self.table:
            ids.append(record.id)
        
        self.assertEqual(ids, [1, 2])


class TestStudentTable(unittest.TestCase):
    """Тесты для таблицы студентов"""
    
    def setUp(self):
        self.table = StudentTable()
    
    def test_insert_valid_student(self):
        """Тест добавления валидного студента"""
        record = self.table.insert({
            "first_name": "John",
            "second_name": "Doe",
            "age": 20,
            "sex": "M"
        })
        
        self.assertEqual(record.id, 1)
        self.assertEqual(record.data["first_name"], "John")
        self.assertEqual(record.data["age"], 20)
        self.assertEqual(self.table.count(), 1)
    
    def test_insert_negative_age(self):
        """Тест добавления с отрицательным возрастом"""
        with self.assertRaises(InvalidAgeError):
            self.table.insert({
                "first_name": "John",
                "second_name": "Doe",
                "age": -5,
                "sex": "M"
            })
    
    def test_insert_invalid_age_too_high(self):
        """Тест добавления со слишком большим возрастом"""
        with self.assertRaises(InvalidAgeError):
            self.table.insert({
                "first_name": "John",
                "second_name": "Doe",
                "age": 200,
                "sex": "M"
            })
    
    def test_update_student_age_valid(self):
        """Тест обновления возраста студента"""
        self.table.insert({
            "first_name": "John",
            "second_name": "Doe",
            "age": 20,
            "sex": "M"
        })
        
        updated = self.table.update(1, {"age": 25})
        self.assertEqual(updated.data["age"], 25)
    
    def test_update_student_age_invalid(self):
        """Тест обновления с некорректным возрастом"""
        self.table.insert({
            "first_name": "John",
            "second_name": "Doe",
            "age": 20,
            "sex": "M"
        })
        
        with self.assertRaises(InvalidAgeError):
            self.table.update(1, {"age": -10})
        
        # Проверяем, что возраст не изменился
        record = self.table.get(1)
        self.assertEqual(record.data["age"], 20)


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
        table = self.db.create_table("NewTable")
        
        self.assertEqual(table.name, "NewTable")
        self.assertIn("NewTable", self.db.list_tables())
        
        retrieved = self.db.get_table("NewTable")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "NewTable")
    
    def test_create_table_empty_name(self):
        """Тест создания таблицы с пустым именем"""
        with self.assertRaises(ValueError):
            self.db.create_table("")
        
        with self.assertRaises(ValueError):
            self.db.create_table("   ")
    
    def test_create_table_duplicate(self):
        """Тест создания дублирующейся таблицы"""
        self.db.create_table("Test")
        with self.assertRaises(ValueError):
            self.db.create_table("Test")
    
    
    def test_get_table(self):
        """Тест получения таблицы"""
        self.db.create_table("Users")
        table = self.db.get_table("Users")
        self.assertIsNotNone(table)
        self.assertEqual(table.name, "Users")
        
        none_table = self.db.get_table("NonExistent")
        self.assertIsNone(none_table)
    
    def test_drop_table(self):
        """Тест удаления таблицы"""
        self.db.create_table("TempTable")
        self.assertIn("TempTable", self.db.list_tables())
        
        result = self.db.drop_table("TempTable")
        self.assertTrue(result)
        self.assertNotIn("TempTable", self.db.list_tables())
    
    def test_drop_table_not_found(self):
        """Тест удаления несуществующей таблицы"""
        result = self.db.drop_table("NonExistent")
        self.assertFalse(result)
    
    def test_drop_student_table_allowed(self):
        """Тест удаления таблицы Student (теперь разрешено)"""
        # Student можно удалить
        result = self.db.drop_table("Student")
        self.assertTrue(result)
        self.assertNotIn("Student", self.db.list_tables())


class TestRecord(unittest.TestCase):
    """Тесты для класса Record"""
    
    def test_record_init(self):
        """Тест инициализации записи"""
        record = Record(1, {"name": "John", "age": 25})
        self.assertEqual(record.id, 1)
        self.assertEqual(record.data["name"], "John")
        self.assertEqual(record.data["age"], 25)
    
    def test_record_to_dict(self):
        """Тест преобразования в словарь"""
        record = Record(1, {"name": "John", "age": 25})
        as_dict = record.to_dict()
        self.assertEqual(as_dict, {"id": 1, "name": "John", "age": 25})
    
    def test_record_getitem(self):
        """Тест доступа через квадратные скобки"""
        record = Record(1, {"name": "John", "age": 25})
        self.assertEqual(record["id"], 1)
        self.assertEqual(record["name"], "John")
        self.assertEqual(record["age"], 25)
    
    def test_record_setitem(self):
        """Тест установки значений через квадратные скобки"""
        record = Record(1, {"name": "John"})
        record["name"] = "Jane"
        record["age"] = 30
        
        self.assertEqual(record.data["name"], "Jane")
        self.assertEqual(record.data["age"], 30)
    
    def test_record_setitem_id(self):
        """Тест изменения ID"""
        record = Record(1, {"name": "John"})
        record["id"] = 100
        self.assertEqual(record.id, 100)
    
    def test_record_repr(self):
        """Тест строкового представления"""
        record = Record(1, {"name": "John"})
        repr_str = repr(record)
        self.assertIn("id=1", repr_str)
        self.assertIn("John", repr_str)


if __name__ == "__main__":
    unittest.main()