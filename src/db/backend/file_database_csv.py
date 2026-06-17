"""Backend для работы с таблицами на диске в формате CSV"""

import os
import csv
from typing import Optional, List, Dict, Any, Set
from .memory import Table, StudentTable, Record, Database
from .errors import FileDatabaseError, InvalidAgeError, RecordNotFoundError


class CSVTable(Table):
    """Таблица с возможностью сохранения/загрузки из CSV-файла"""
    
    def __init__(self, name: str, data_dir: str = "data"):
        self.name = name
        self.data_dir = data_dir
        self._records: Dict[int, Record] = {}
        self._next_id = 1
        self._file_path = os.path.join(data_dir, f"{name}.csv")
        self._headers: Set[str] = set()
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
        """Загружает данные таблицы из CSV-файла"""
        if not os.path.exists(self._file_path):
            self._save_to_file()
            return
        
        try:
            with open(self._file_path, 'r', encoding='utf-8', newline='') as f:
                reader = csv.DictReader(f)
                
                if reader.fieldnames:
                    self._headers = set(reader.fieldnames)
                
                self._records.clear()
                max_id = 0
                
                for row in reader:
                    try:
                        record_id = int(row.get('id', 0))
                        if record_id == 0:
                            continue
                        
                        data = {k: self._parse_value(v) for k, v in row.items() if k != 'id'}
                        
                        record = Record(record_id, data)
                        self._records[record_id] = record
                        
                        if record_id > max_id:
                            max_id = record_id
                    except Exception as e:
                        raise FileDatabaseError(f"Ошибка чтения строки CSV в {self._file_path}: {e}")
                
                self._next_id = max_id + 1 if max_id > 0 else 1
                
        except FileNotFoundError:
            self._save_to_file()
        except csv.Error as e:
            raise FileDatabaseError(f"Ошибка парсинга CSV файла {self._file_path}: {e}")
        except Exception as e:
            raise FileDatabaseError(f"Ошибка загрузки таблицы {self.name}: {e}")
    
    def _parse_value(self, value: str) -> Any:
        """Преобразует строку из CSV в значение нужного типа"""
        if not value:
            return None
        
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            pass
        
        if value.lower() == 'true':
            return True
        if value.lower() == 'false':
            return False
        
        return value
    
    def _format_value(self, value: Any) -> str:
        """Преобразует значение в строку для CSV"""
        if value is None:
            return ''
        return str(value)
    
    def _update_headers(self, data: Dict[str, Any]) -> None:
        """Обновляет список заголовков новыми полями"""
        for key in data.keys():
            self._headers.add(key)
    
    def _save_to_file(self) -> None:
        """Сохраняет данные таблицы в CSV-файл с атомарной записью"""
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            
            all_fields = ['id'] + sorted([h for h in self._headers if h != 'id'])
            
            # ВРЕМЕННЫЙ ФАЙЛ для атомарной записи
            temp_file = self._file_path + '.tmp'
            
            # Записываем во временный файл
            with open(temp_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=all_fields)
                writer.writeheader()
                
                for record in self._records.values():
                    row = {'id': record.id}
                    row.update(record.data)
                    row = {k: self._format_value(v) for k, v in row.items()}
                    writer.writerow(row)
            
            # АТОМАРНАЯ ЗАМЕНА (только после успешной записи)
            os.replace(temp_file, self._file_path)
            
        except PermissionError as e:
            raise FileDatabaseError(f"Нет доступа к файлу {self._file_path}: {e}")
        except OSError as e:
            raise FileDatabaseError(f"Ошибка файловой системы при сохранении {self.name}: {e}")
        except Exception as e:
            raise FileDatabaseError(f"Ошибка сохранения таблицы {self.name}: {e}")
    
    def insert(self, data: Dict[str, Any]) -> Record:
        self._update_headers(data)
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
        """Обновляет запись с откатом при ошибке"""
        if record_id not in self._records:
            raise RecordNotFoundError(f"Запись с ID {record_id} не найдена")
        
        self._update_headers(data)
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
        self._headers.clear()
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


class CSVStudentTable(StudentTable, CSVTable):
    """CSV-версия таблицы студентов с валидацией"""
    
    def __init__(self, data_dir: str = "data"):
        CSVTable.__init__(self, "Student", data_dir)
    
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


class CSVDatabase(Database):
    
    def __init__(self, data_dir: str = "data_csv"):
        self.data_dir = data_dir
        self._tables: Dict[str, CSVTable] = {}
        try:
            os.makedirs(self.data_dir, exist_ok=True)
        except PermissionError as e:
            raise FileDatabaseError(f"Нет прав на создание директории {data_dir}: {e}")
        except OSError as e:
            raise FileDatabaseError(f"Ошибка создания директории {data_dir}: {e}")
        
        self._load_all_tables()
    
    def _get_table_path(self, table_name: str) -> str:
        return os.path.join(self.data_dir, f"{table_name}.csv")
    
    def _is_student_table(self, table_name: str) -> bool:
        return table_name == "Student"
    
    def _load_all_tables(self) -> None:
        if not os.path.exists(self.data_dir):
            return
        
        for filename in os.listdir(self.data_dir):
            if filename.endswith(".csv"):
                table_name = filename[:-4]
                try:
                    if self._is_student_table(table_name):
                        self._tables[table_name] = CSVStudentTable(self.data_dir)
                    else:
                        self._tables[table_name] = CSVTable(table_name, self.data_dir)
                except Exception as e:
                    print(f"Предупреждение: не удалось загрузить таблицу {table_name}: {e}")
    
    def create_table(self, table_name: str) -> CSVTable:
        table_name = table_name.strip()
        
        if not table_name:
            raise ValueError("Имя таблицы не может быть пустым")
        
        if table_name in self._tables:
            raise ValueError(f"Таблица '{table_name}' уже существует")
        
        if self._is_student_table(table_name):
            table = CSVStudentTable(self.data_dir)
        else:
            table = CSVTable(table_name, self.data_dir)
        
        self._tables[table_name] = table
        return table
    
    def get_table(self, table_name: str) -> Optional[CSVTable]:
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