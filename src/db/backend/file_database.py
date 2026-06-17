"""Backend для работы с таблицами на диске (JSON)"""

import os
import json
import logging
from typing import Optional, List, Dict, Any
from .memory import Table, StudentTable, Record, Database
from .errors import FileDatabaseError, RecordNotFoundError, InvalidAgeError

logger = logging.getLogger(__name__)


class FileTable(Table):
    """Таблица с возможностью сохранения/загрузки из файла"""
    
    def __init__(self, name: str, data_dir: str = "data"):
        self.name = name
        self.data_dir = data_dir
        self._records: Dict[int, Record] = {}
        self._next_id = 1
        self._file_path = os.path.join(data_dir, f"{name}.json")
        self._load_from_file()
    
    def __len__(self) -> int:
        return len(self._records)
    
    def __iter__(self):
        return iter(self._records.values())
    
    def all(self) -> List[Record]:
        return list(self._records.values())
    
    def count(self) -> int:
        return len(self._records)
    
    def _get_file_path(self) -> str:
        return self._file_path
    
    def _load_from_file(self) -> None:
        """Загружает данные таблицы из JSON-файла с обработкой ошибок"""
        if not os.path.exists(self._file_path):
            self._save_to_file()
            return
        
        try:
            with open(self._file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, dict):
                raise FileDatabaseError(f"Некорректная структура файла {self._file_path}: ожидался словарь")
            
            if 'records' not in data:
                raise FileDatabaseError(f"Некорректный формат файла {self._file_path}: отсутствует ключ 'records'")
            
            if not isinstance(data['records'], list):
                raise FileDatabaseError(f"Некорректный формат файла {self._file_path}: 'records' должен быть списком")
            
            self._records.clear()
            for record_data in data.get('records', []):
                try:
                    if not isinstance(record_data, dict) or 'id' not in record_data or 'data' not in record_data:
                        logger.warning(f"Пропущена некорректная запись в {self._file_path}: {record_data}")
                        continue
                    record = Record(record_data['id'], record_data['data'])
                    self._records[record.id] = record
                except Exception as e:
                    logger.warning(f"Ошибка восстановления записи в {self._file_path}: {e}")
            
            self._next_id = data.get('next_id', max(self._records.keys()) + 1 if self._records else 1)
            
        except json.JSONDecodeError as e:
            logger.warning(f"Ошибка чтения JSON из файла {self._file_path}: {e}. Создана пустая таблица.")
            self._records.clear()
            self._next_id = 1
            self._save_to_file()
        except FileDatabaseError:
            raise
        except Exception as e:
            raise FileDatabaseError(f"Ошибка загрузки таблицы {self.name}: {e}")
    
    def _save_to_file(self) -> None:
        """Сохраняет данные таблицы в JSON-файл с атомарной записью"""
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            
            all_fields = set()
            for record in self._records.values():
                all_fields.update(record.data.keys())
            
            data = {
                'name': self.name,
                'next_id': self._next_id,
                'fields': list(all_fields),
                'records': [
                    {'id': record.id, 'data': record.data}
                    for record in self._records.values()
                ]
            }
            
            temp_file = self._file_path + '.tmp'
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            
            os.replace(temp_file, self._file_path)
                
        except FileDatabaseError:
            raise
        except PermissionError as e:
            raise FileDatabaseError(f"Нет доступа к файлу {self._file_path}: {e}")
        except OSError as e:
            raise FileDatabaseError(f"Ошибка файловой системы при сохранении {self.name}: {e}")
        except Exception as e:
            raise FileDatabaseError(f"Ошибка сохранения таблицы {self.name}: {e}")
    
    def insert(self, data: Dict[str, Any]) -> Record:
        new_id = self._next_id
        record = Record(new_id, data.copy())
        
        old_records = self._records.copy()
        old_next_id = self._next_id
        
        try:
            self._records[new_id] = record
            self._next_id = new_id + 1
            self._save_to_file()
            return record
        except Exception as e:
            self._records = old_records
            self._next_id = old_next_id
            raise FileDatabaseError(f"Ошибка сохранения записи: {e}")
    
    def get(self, record_id: int) -> Optional[Record]:
        return self._records.get(record_id)
    
    def update(self, record_id: int, data: Dict[str, Any]) -> Record:
        if record_id not in self._records:
            raise RecordNotFoundError(f"Запись с ID {record_id} не найдена")
        
        record = self._records[record_id]
        old_data = record.data.copy()
        
        try:
            record.data.update(data)
            self._save_to_file() 
            return record
        except Exception as e:
            record.data = old_data
            raise FileDatabaseError(f"Ошибка обновления записи: {e}")
    
    def delete(self, record_id: int) -> bool:
        if record_id in self._records:
            del self._records[record_id]
            self._save_to_file()
            return True
        return False
    
    def clear(self) -> None:
        self._records.clear()
        self._next_id = 1
        self._save_to_file()
    
    def find(self, **kwargs) -> List[Record]:
        results = []
        for record in self._records.values():
            match = True
            for key, value in kwargs.items():
                if record.data.get(key) != value:
                    match = False
                    break
            if match:
                results.append(record)
        return results
    
    def sort(self, field: str, reverse: bool = False) -> List[Record]:
        records = self.all()
        
        def get_key(record: Record) -> Any:
            if field == 'id':
                return record.id
            return record.data.get(field)
        
        try:
            return sorted(records, key=get_key, reverse=reverse)
        except TypeError as e:
            raise TypeError(f"Не удалось отсортировать по полю '{field}': {e}")


class FileStudentTable(StudentTable, FileTable):
    """Файловая версия таблицы студентов с валидацией"""
    
    def __init__(self, data_dir: str = "data"):
        FileTable.__init__(self, "Student", data_dir)
    
    def insert(self, data: Dict[str, Any]) -> Record:
        if 'age' in data:
            age = data['age']
            if not isinstance(age, int) or age < 0 or age > 150:
                raise InvalidAgeError(f"Некорректный возраст: {age}")
        return super().insert(data)
    
    def update(self, record_id: int, data: Dict[str, Any]) -> Record:
        if 'age' in data:
            age = data['age']
            if not isinstance(age, int) or age < 0 or age > 150:
                raise InvalidAgeError(f"Некорректный возраст: {age}")
        return super().update(record_id, data)


class FileDatabase(Database):
    """Файловая база данных, сохраняющая таблицы на диск в формате JSON"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self._tables: Dict[str, FileTable] = {}
        try:
            os.makedirs(self.data_dir, exist_ok=True)
        except PermissionError as e:
            raise FileDatabaseError(f"Нет прав на создание директории {data_dir}: {e}")
        except OSError as e:
            raise FileDatabaseError(f"Ошибка создания директории {data_dir}: {e}")
        
        self._load_all_tables()
    
    def _get_table_path(self, table_name: str) -> str:
        return os.path.join(self.data_dir, f"{table_name}.json")
    
    def _is_student_table(self, table_name: str) -> bool:
        return table_name == "Student"
    
    def _load_all_tables(self) -> None:
        if not os.path.exists(self.data_dir):
            return
        
        for filename in os.listdir(self.data_dir):
            if filename.endswith(".json"):
                table_name = filename[:-5]
                try:
                    if self._is_student_table(table_name):
                        self._tables[table_name] = FileStudentTable(self.data_dir)
                    else:
                        self._tables[table_name] = FileTable(table_name, self.data_dir)
                except Exception as e:
                    logger.error(f"Не удалось загрузить таблицу {table_name}: {e}")
    
    def create_table(self, table_name: str) -> FileTable:
        table_name = table_name.strip()
        
        if not table_name:
            raise ValueError("Имя таблицы не может быть пустым")
        
        if table_name in self._tables:
            raise ValueError(f"Таблица '{table_name}' уже существует")
        
        if self._is_student_table(table_name):
            table = FileStudentTable(self.data_dir)
        else:
            table = FileTable(table_name, self.data_dir)
        
        self._tables[table_name] = table
        return table
    
    def get_table(self, table_name: str) -> Optional[FileTable]:
        return self._tables.get(table_name)
    
    def list_tables(self) -> List[str]:
        return list(self._tables.keys())
    
    def drop_table(self, table_name: str) -> bool:
        if table_name not in self._tables:
            return False
        
        file_path = self._get_table_path(table_name)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                raise FileDatabaseError(f"Не удалось удалить файл {file_path}: {e}")
        
        del self._tables[table_name]
        return True
    
    def save_all(self) -> None:
        for table in self._tables.values():
            table._save_to_file()