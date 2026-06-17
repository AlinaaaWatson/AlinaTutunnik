import sys
import os
import tempfile
import shutil
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.db.backend.file_database import FileDatabase, FileTable, FileStudentTable
from src.db.backend.errors import InvalidAgeError, RecordNotFoundError


class TestFileDatabaseMinimal(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_create_table(self):
        """Тест создания таблицы"""
        db = FileDatabase(data_dir=self.temp_dir)
        table = db.create_table("Users")
        self.assertEqual(table.name, "Users")
        self.assertIn("Users", db.list_tables())
    
    def test_create_student_table(self):
        """Тест создания таблицы Student"""
        db = FileDatabase(data_dir=self.temp_dir)
        table = db.create_table("Student")
        self.assertEqual(table.name, "Student")
    
    def test_get_table(self):
        """Тест получения таблицы"""
        db = FileDatabase(data_dir=self.temp_dir)
        db.create_table("Users")
        table = db.get_table("Users")
        self.assertIsNotNone(table)
    
    def test_drop_table(self):
        """Тест удаления таблицы"""
        db = FileDatabase(data_dir=self.temp_dir)
        db.create_table("ToDrop")
        self.assertIn("ToDrop", db.list_tables())
        result = db.drop_table("ToDrop")
        self.assertTrue(result)
        self.assertNotIn("ToDrop", db.list_tables())


class TestFileDatabaseCoverage(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_filetable_len_and_iter(self):
        """Тест __len__ и __iter__"""
        table = FileTable("TestTable", self.temp_dir)
        self.assertEqual(len(table), 0)
        
        table.insert({"name": "John"})
        table.insert({"name": "Jane"})
        
        # __iter__
        records = list(table)
        self.assertEqual(len(records), 2)
        
        # count
        self.assertEqual(table.count(), 2)
        
        # all
        self.assertEqual(len(table.all()), 2)
    
    def test_filetable_get_methods(self):
        """Тест get и get_nonexistent"""
        table = FileTable("GetTest", self.temp_dir)
        table.insert({"name": "John"})
        
        self.assertEqual(table.get(1).data["name"], "John")
        self.assertIsNone(table.get(999))
    
    def test_filetable_update_and_delete(self):
        """Тест update и delete"""
        table = FileTable("UpdateDeleteTest", self.temp_dir)
        table.insert({"name": "John", "age": 20})
        
        updated = table.update(1, {"age": 25})
        self.assertEqual(updated.data["age"], 25)
        
        result = table.delete(1)
        self.assertTrue(result)
        self.assertEqual(len(table), 0)
        
        result = table.delete(999)
        self.assertFalse(result)
    
    def test_filetable_find_methods(self):
        """Тест find"""
        table = FileTable("FindTest", self.temp_dir)
        table.insert({"name": "John", "age": 25})
        table.insert({"name": "Jane", "age": 25})
        table.insert({"name": "Bob", "age": 30})
        
        results = table.find(age=25)
        self.assertEqual(len(results), 2)
        
        results = table.find()
        self.assertEqual(len(results), 3)
        
        results = table.find(name="Bob")
        self.assertEqual(len(results), 1)
    
    def test_filetable_sort_methods(self):
        """Тест sort"""
        table = FileTable("SortTest", self.temp_dir)
        table.insert({"name": "Zebra", "age": 30})
        table.insert({"name": "Apple", "age": 20})
        table.insert({"name": "Cat", "age": 25})
        
        sorted_by_name = table.sort("name")
        self.assertEqual([r.data["name"] for r in sorted_by_name], ["Apple", "Cat", "Zebra"])
        
        sorted_by_age_desc = table.sort("age", reverse=True)
        self.assertEqual([r.data["age"] for r in sorted_by_age_desc], [30, 25, 20])
        
        empty_table = FileTable("EmptySort", self.temp_dir)
        self.assertEqual(empty_table.sort("any"), [])
    
    def test_filetable_clear_and_empty(self):
        """Тест clear"""
        table = FileTable("ClearTest", self.temp_dir)
        table.insert({"name": "John"})
        table.insert({"name": "Jane"})
        self.assertEqual(len(table), 2)
        
        table.clear()
        self.assertEqual(len(table), 0)
    
    def test_filetable_with_complex_data(self):
        """Тест с разными типами данных"""
        table = FileTable("ComplexTest", self.temp_dir)
        table.insert({
            "string": "hello",
            "integer": 42,
            "float": 3.14,
            "boolean": True,
            "null": None
        })
        
        record = table.get(1)
        self.assertEqual(record.data["string"], "hello")
        self.assertEqual(record.data["integer"], 42)
        self.assertEqual(record.data["float"], 3.14)
        self.assertEqual(record.data["boolean"], True)
        self.assertIsNone(record.data["null"])
    
    def test_filetable_reload_persistence(self):
        """Тест сохранения и загрузки"""
        table1 = FileTable("PersistTest", self.temp_dir)
        table1.insert({"name": "John", "age": 25})
        table1.insert({"name": "Jane", "age": 30})
        
        table2 = FileTable("PersistTest", self.temp_dir)
        self.assertEqual(len(table2), 2)
        self.assertEqual(table2.get(1).data["name"], "John")
        self.assertEqual(table2.get(2).data["name"], "Jane")
    
    def test_filetable_student_validation(self):
        """Тест студенческой таблицы"""
        table = FileStudentTable(self.temp_dir)
        
        # Валидный студент
        record = table.insert({"name": "John", "age": 20})
        self.assertEqual(record.data["age"], 20)
        
        # Невалидный возраст
        with self.assertRaises(InvalidAgeError):
            table.insert({"name": "Bad", "age": -5})
        
        with self.assertRaises(InvalidAgeError):
            table.insert({"name": "Old", "age": 200})
        
        # Обновление с валидным возрастом
        table.update(1, {"age": 25})
        self.assertEqual(table.get(1).data["age"], 25)
        
        # Обновление с невалидным возрастом
        with self.assertRaises(InvalidAgeError):
            table.update(1, {"age": -10})
    
    def test_filetable_database_operations(self):
        """Тест операций с базой данных"""
        db = FileDatabase(data_dir=self.temp_dir)
        
        initial_count = len(db.list_tables())
        
        db.create_table("Table1")
        db.create_table("Table2")
        
        self.assertIn("Table1", db.list_tables())
        self.assertIn("Table2", db.list_tables())
        self.assertEqual(len(db.list_tables()), initial_count + 2)
        
        self.assertIsNotNone(db.get_table("Table1"))
        self.assertIsNone(db.get_table("NonExistent"))
        
        db.drop_table("Table1")
        self.assertNotIn("Table1", db.list_tables())
        
        result = db.drop_table("NonExistent")
        self.assertFalse(result)
    
    def test_filetable_save_all(self):
        """Тест save_all"""
        db = FileDatabase(data_dir=self.temp_dir)
        db.create_table("SaveTest1")
        db.create_table("SaveTest2")
        
        db.save_all()
        
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, "SaveTest1.json")))
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, "SaveTest2.json")))
    
    def test_filetable_name_property(self):
        """Тест name свойства"""
        table = FileTable("NameTest", self.temp_dir)
        self.assertEqual(table.name, "NameTest")
    
    def test_filetable_file_path(self):
        """Тест _get_file_path"""
        table = FileTable("PathTest", self.temp_dir)
        expected = os.path.join(self.temp_dir, "PathTest.json")
        self.assertEqual(table._get_file_path(), expected)
    
    def test_filetable_update_nonexistent_raises_error(self):
        """Тест обновления несуществующей записи"""
        table = FileTable("UpdateErrorTest", self.temp_dir)
        with self.assertRaises(RecordNotFoundError):
            table.update(999, {"name": "Test"})
    
    def test_filetable_load_nonexistent_file(self):
        """Тест загрузки несуществующего файла"""
        table = FileTable("NewTable", self.temp_dir)
        self.assertEqual(len(table), 0)
        self.assertEqual(table._next_id, 1)

    def test_update_persistence_after_reload(self):
        """Тест: update сохраняется после перезагрузки"""
        table1 = FileTable("UpdatePersistTest", self.temp_dir)
        table1.insert({"name": "John", "age": 20})
        table1.update(1, {"age": 25})
        
        table2 = FileTable("UpdatePersistTest", self.temp_dir)
        record = table2.get(1)
        self.assertEqual(record.data["age"], 25)

if __name__ == "__main__":
    unittest.main()