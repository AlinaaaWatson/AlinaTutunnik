# src/db/backend/memory.py
from typing import Optional, List, Tuple, Dict, Any
from .errors import StudentTableError, DuplicateIDError, InvalidAgeError

# Type aliases
StudentRecord = Tuple[int, str, str, int, str]


class Table:
    """Базовый класс для всех таблиц"""
    
    def __init__(self, name: str) -> None:
        self.name = name
        self._records: List[Tuple] = []
    
    def all(self) -> List[Tuple]:
        """Возвращает копию всех записей"""
        return self._records.copy()
    
    def count(self) -> int:
        """Возвращает количество записей"""
        return len(self._records)
    
    def clear(self) -> None:
        """Очищает таблицу"""
        self._records.clear()


class StudentTable(Table):
    """Таблица студентов с CRUD операциями"""
    
    def __init__(self) -> None:
        super().__init__("Student")
    
    def create_record(
        self,
        student_id: int,
        first_name: str,
        second_name: str,
        age: int,
        sex: str,
    ) -> StudentRecord:
        """
        Создаёт новую запись и добавляет её в таблицу Student.
        
        Args:
            student_id: Уникальный идентификатор
            first_name: Имя
            second_name: Фамилия
            age: Возраст
            sex: Пол
            
        Returns:
            Созданная запись
            
        Raises:
            InvalidAgeError: Если возраст отрицательный
            DuplicateIDError: Если ID уже существует
        """
        # Проверка корректности возраста
        if age < 0:
            raise InvalidAgeError("Поле age не может быть отрицательным.")
        
        # Проверка уникальности идентификатора
        if any(record[0] == student_id for record in self._records):
            raise DuplicateIDError(f"Запись с id={student_id} уже существует.")
        
        # Формирование и добавление новой записи
        new_record: StudentRecord = (
            student_id,
            first_name.strip(),
            second_name.strip(),
            age,
            sex.strip(),
        )
        
        self._records.append(new_record)
        return new_record
    
    def select_record(
        self,
        student_id: Optional[int] = None,
        first_name: Optional[str] = None,
        second_name: Optional[str] = None,
        age: Optional[int] = None,
        sex: Optional[str] = None,
    ) -> List[StudentRecord]:
        """
        Выполняет выборку записей по фильтрам.
        
        Args:
            student_id: Фильтр по ID
            first_name: Фильтр по имени
            second_name: Фильтр по фамилии
            age: Фильтр по возрасту
            sex: Фильтр по полу
            
        Returns:
            Список записей, удовлетворяющих фильтрам
        """
        # Если фильтры не заданы, возвращаем все записи
        if all(param is None for param in [student_id, first_name, second_name, age, sex]):
            return self._records.copy()
        
        result: List[StudentRecord] = []
        
        for record in self._records:
            # Проверка соответствия каждому фильтру
            if student_id is not None and record[0] != student_id:
                continue
            if first_name is not None and record[1] != first_name:
                continue
            if second_name is not None and record[2] != second_name:
                continue
            if age is not None and record[3] != age:
                continue
            if sex is not None and record[4] != sex:
                continue
            
            result.append(record)
        
        return result
    
    def update_record(
        self,
        student_id: int,
        first_name: Optional[str] = None,
        second_name: Optional[str] = None,
        age: Optional[int] = None,
        sex: Optional[str] = None,
    ) -> Optional[StudentRecord]:
        """
        Обновляет запись с указанным student_id.
        
        Args:
            student_id: ID записи для обновления
            first_name: Новое имя (None - не менять)
            second_name: Новая фамилия (None - не менять)
            age: Новый возраст (None - не менять)
            sex: Новый пол (None - не менять)
            
        Returns:
            Обновленная запись или None, если запись не найдена
            
        Raises:
            InvalidAgeError: Если новый возраст отрицательный
        """
        for i, record in enumerate(self._records):
            if record[0] == student_id:
                # Создаем обновленную запись
                new_record: StudentRecord = (
                    student_id,
                    first_name if first_name is not None else record[1],
                    second_name if second_name is not None else record[2],
                    age if age is not None else record[3],
                    sex if sex is not None else record[4],
                )
                
                # Валидация нового возраста
                if new_record[3] < 0:
                    raise InvalidAgeError("Поле age не может быть отрицательным.")
                
                self._records[i] = new_record
                return new_record
        
        return None
    
    def delete_record(self, student_id: int) -> bool:
        """
        Удаляет запись с указанным student_id.
        
        Args:
            student_id: ID записи для удаления
            
        Returns:
            True если запись удалена, False если не найдена
        """
        for i, record in enumerate(self._records):
            if record[0] == student_id:
                del self._records[i]
                return True
        
        return False
    
    def get_by_id(self, student_id: int) -> Optional[StudentRecord]:
        """Возвращает запись по ID или None, если запись не найдена"""
        for record in self._records:
            if record[0] == student_id:
                return record
        return None


class Database:
    """Управление несколькими таблицами"""
    
    def __init__(self) -> None:
        self._tables: Dict[str, Table] = {}
        self._init_default_tables()
    
    def _init_default_tables(self) -> None:
        """Инициализация таблиц по умолчанию"""
        self.create_table("Student")
        self.create_table("Teachers")
    
    def create_table(self, table_name: str) -> bool:
        """
        Создает новую таблицу.
        
        Args:
            table_name: Имя таблицы
            
        Returns:
            True если создана, False если уже существует
            
        Raises:
            ValueError: Если имя таблицы пустое
        """
        table_name = table_name.strip()
        
        if not table_name:
            raise ValueError("Имя таблицы не может быть пустым")
        
        if table_name in self._tables:
            return False
        
        # Создаем соответствующую таблицу
        if table_name == "Student":
            self._tables[table_name] = StudentTable()
        else:
            self._tables[table_name] = Table(table_name)
        
        return True
    
    def list_tables(self) -> List[str]:
        """Возвращает список всех таблиц"""
        return list(self._tables.keys())
    
    def get_table(self, table_name: str) -> Optional[Table]:
        """Возвращает таблицу по имени или None, если таблица не найдена"""
        return self._tables.get(table_name)
    
    def get_student_table(self) -> Optional[StudentTable]:
        """Возвращает таблицу Student (специализированный метод)"""
        table = self._tables.get("Student")
        if isinstance(table, StudentTable):
            return table
        return None
    
    def delete_table(self, table_name: str) -> bool:
        """
        Удаляет таблицу.
        
        Args:
            table_name: Имя таблицы для удаления
            
        Returns:
            True если удалена, False если не найдена
            
        Raises:
            ValueError: Если пытаются удалить таблицу Student
        """
        if table_name == "Student":
            raise ValueError("Таблицу Student нельзя удалить")
        
        if table_name in self._tables:
            del self._tables[table_name]
            return True
        
        return False
    
    def clear_all(self) -> None:
        """Очищает все таблицы (для тестов)"""
        self._tables.clear()
        self._init_default_tables()


# Глобальный экземпляр базы данных (для обратной совместимости)
_DATABASE = Database()

# Функции для обратной совместимости с существующим кодом
def get_db() -> Database:
    """Возвращает глобальный экземпляр базы данных"""
    return _DATABASE


# Совместимость со старым API (функциональный интерфейс)
def create_record(
    student_id: int,
    first_name: str,
    second_name: str,
    age: int,
    sex: str,
) -> StudentRecord:
    """Совместимость со старым кодом"""
    student_table = _DATABASE.get_student_table()
    if not student_table:
        _DATABASE.create_table("Student")
        student_table = _DATABASE.get_student_table()
    return student_table.create_record(student_id, first_name, second_name, age, sex)


def select_record(
    student_id: Optional[int] = None,
    first_name: Optional[str] = None,
    second_name: Optional[str] = None,
    age: Optional[int] = None,
    sex: Optional[str] = None,
) -> List[StudentRecord]:
    """Совместимость со старым кодом"""
    student_table = _DATABASE.get_student_table()
    if not student_table:
        return []
    return student_table.select_record(
        student_id=student_id,
        first_name=first_name,
        second_name=second_name,
        age=age,
        sex=sex
    )


def update_record(
    student_id: int,
    first_name: Optional[str] = None,
    second_name: Optional[str] = None,
    age: Optional[int] = None,
    sex: Optional[str] = None,
) -> Optional[StudentRecord]:
    """Совместимость со старым кодом"""
    student_table = _DATABASE.get_student_table()
    if not student_table:
        return None
    return student_table.update_record(
        student_id,
        first_name=first_name,
        second_name=second_name,
        age=age,
        sex=sex
    )


def delete_record(student_id: int) -> bool:
    """Совместимость со старым кодом"""
    student_table = _DATABASE.get_student_table()
    if not student_table:
        return False
    return student_table.delete_record(student_id)


def create_table(table_name: str) -> bool:
    """Совместимость со старым кодом"""
    return _DATABASE.create_table(table_name)


def list_tables() -> List[str]:
    """Совместимость со старым кодом"""
    return _DATABASE.list_tables()


def get_table(table_name: str) -> Optional[Table]:
    """Совместимость со старым кодом"""
    return _DATABASE.get_table(table_name)


def delete_table(table_name: str) -> bool:
    """Совместимость со старым кодом"""
    return _DATABASE.delete_table(table_name)


# Для обратной совместимости с кодом, который обращается напрямую к Student
def _get_student_list() -> List[StudentRecord]:
    """Внутренняя функция для доступа к списку Student"""
    student_table = _DATABASE.get_student_table()
    if student_table:
        return student_table._records
    return []


# Совместимость с кодом, который использует Student как список
Student = _get_student_list()
init_database = lambda: None  # Для совместимости
