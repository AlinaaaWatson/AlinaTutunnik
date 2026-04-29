"""Backend для работы с таблицами в памяти"""
from typing import Optional, List, Dict, Any
from .errors import DuplicateIDError, InvalidAgeError, RecordNotFoundError


class Record:
    """Класс для одной записи"""
    
    def __init__(self, record_id: int, data: Dict[str, Any]):
        self.id = record_id
        self.data = data.copy()
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует запись в словарь"""
        return {'id': self.id, **self.data}
    
    def __getitem__(self, key: str) -> Any:
        """Позволяет обращаться как record['field']"""
        if key == 'id':
            return self.id
        return self.data.get(key)
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Позволяет устанавливать значение как record['field'] = value"""
        if key == 'id':
            self.id = value
        else:
            self.data[key] = value
    
    def __repr__(self) -> str:
        return f"Record(id={self.id}, data={self.data})"


class Table:
    """Базовый класс таблицы с полной CRUD функциональностью"""
    
    def __init__(self, name: str):
        self.name = name
        self._records: Dict[int, Record] = {}
        self._next_id = 1
    
    def __len__(self) -> int:
        """Поддержка len(table)"""
        return len(self._records)
    
    def __iter__(self):
        """Поддержка итерации по таблице"""
        return iter(self._records.values())
    
    def all(self) -> List[Record]:
        """Вернуть все записи"""
        return list(self._records.values())
    
    def count(self) -> int:
        """Вернуть количество записей"""
        return len(self._records)
    
    def clear(self) -> None:
        """Очистить таблицу"""
        self._records.clear()
        self._next_id = 1
    
    def insert(self, data: Dict[str, Any]) -> Record:
        """
        Добавить новую запись
        
        Args:
            data: Словарь с данными записи
            
        Returns:
            Созданная запись
        """
        record_id = self._next_id
        self._next_id += 1
        record = Record(record_id, data)
        self._records[record_id] = record
        return record
    
    def get(self, record_id: int) -> Optional[Record]:
        """
        Получить запись по ID
        
        Args:
            record_id: ID записи
            
        Returns:
            Запись или None если не найдена
        """
        return self._records.get(record_id)
    
    def update(self, record_id: int, data: Dict[str, Any]) -> Record:
        """
        Обновить запись
        
        Args:
            record_id: ID записи для обновления
            data: Новые данные (будут объединены с существующими)
            
        Returns:
            Обновленная запись
            
        Raises:
            RecordNotFoundError: Если запись не найдена
        """
        if record_id not in self._records:
            raise RecordNotFoundError(f"Запись с ID {record_id} не найдена")
        
        record = self._records[record_id]
        record.data.update(data)
        return record
    
    def delete(self, record_id: int) -> bool:
        """
        Удалить запись
        
        Args:
            record_id: ID записи для удаления
            
        Returns:
            True если запись удалена, False если не найдена
        """
        if record_id in self._records:
            del self._records[record_id]
            return True
        return False
    
    def find(self, **kwargs) -> List[Record]:
        """
        Найти записи по критериям
        
        Args:
            **kwargs: Поля и значения для поиска (например, name="John", age=25)
            
        Returns:
            Список записей, удовлетворяющих критериям
        """
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
        """
        Сортировка записей по полю
        
        Args:
            field: Имя поля для сортировки (или 'id' для сортировки по ID)
            reverse: False - по возрастанию, True - по убыванию
            
        Returns:
            Отсортированный список записей
        """
        records = self.all()
        
        def get_key(record: Record) -> Any:
            if field == 'id':
                return record.id
            return record.data.get(field)
        
        return sorted(records, key=get_key, reverse=reverse)


class StudentTable(Table):
    """Специализированная таблица для студентов с валидацией"""
    
    def __init__(self):
        super().__init__("Student")
    
    def insert(self, data: Dict[str, Any]) -> Record:
        """
        Добавить запись студента с валидацией
        
        Args:
            data: Должен содержать поля: first_name, second_name, age, sex
            
        Returns:
            Созданная запись
            
        Raises:
            InvalidAgeError: Если возраст некорректный
        """
        # Валидация возраста
        if 'age' in data:
            age = data['age']
            if not isinstance(age, int) or age < 0 or age > 150:
                raise InvalidAgeError(f"Некорректный возраст: {age}")
        
        return super().insert(data)
    
    def update(self, record_id: int, data: Dict[str, Any]) -> Record:
        """
        Обновить запись студента с валидацией
        
        Raises:
            InvalidAgeError: Если возраст некорректный
        """
        if 'age' in data:
            age = data['age']
            if not isinstance(age, int) or age < 0 or age > 150:
                raise InvalidAgeError(f"Некорректный возраст: {age}")
        
        return super().update(record_id, data)


class Database:
    """Управление несколькими таблицами"""
    
    def __init__(self):
        self._tables: Dict[str, Table] = {}
        self._init_default_tables()
    
    def _init_default_tables(self) -> None:
        """Инициализация таблиц по умолчанию"""
        self.create_table("Student")
        self.create_table("Teachers")
    
    def create_table(self, table_name: str) -> Table:
        """
        Создает новую таблицу
        
        Args:
            table_name: Имя таблицы
            
        Returns:
            Созданная таблица
            
        Raises:
            ValueError: Если имя таблицы пустое
            ValueError: Если таблица уже существует
        """
        table_name = table_name.strip()
        
        if not table_name:
            raise ValueError("Имя таблицы не может быть пустым")
        
        if table_name in self._tables:
            raise ValueError(f"Таблица '{table_name}' уже существует")
        
        # Создаем соответствующую таблицу
        if table_name == "Student":
            table = StudentTable()
        else:
            table = Table(table_name)
        
        self._tables[table_name] = table
        return table
    
    def get_table(self, table_name: str) -> Optional[Table]:
        """Возвращает таблицу по имени или None, если таблица не найдена"""
        return self._tables.get(table_name)
    
    def list_tables(self) -> List[str]:
        """Возвращает список всех таблиц"""
        return list(self._tables.keys())
    
    def drop_table(self, table_name: str) -> bool:
        """
        Удаляет таблицу
        
        Args:
            table_name: Имя таблицы для удаления
            
        Returns:
            True если удалена, False если не найдена
        """
        if table_name in self._tables:
            del self._tables[table_name]
            return True
        return False