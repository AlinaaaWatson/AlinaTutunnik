"""Текстовый пользовательский интерфейс"""

from typing import Optional, Dict, Any, List
import sys
import os

# Добавляем корневую директорию в путь для корректных импортов
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db.backend.memory import Database, Table, Record
from src.db.backend.errors import InvalidAgeError, RecordNotFoundError, FileDatabaseError
from src.db.backend.memory import Database as InMemoryDatabase
from src.db.backend.file_database import FileDatabase
from src.db.backend.file_database_csv import CSVDatabase


def parse_user_input(value: str) -> Any:
    """
    Преобразует строку пользователя в нужный тип (int/float/str/None/bool)
    
    Примеры:
        "42" -> 42
        "3.14" -> 3.14
        "" -> None
        "true" -> True
        "false" -> False
        "строка" -> "строка"
    """
    value = value.strip()
    if not value:
        return None
    
    if value.lower() == 'true':
        return True
    if value.lower() == 'false':
        return False
    
    try:
        if '.' in value:
            return float(value)
        return int(value)
    except ValueError:
        pass
    
    return value


class ConsoleUI:
    """Консольный интерфейс для работы с БД"""
    
    def __init__(self, database: Database):
        self.db = database
        self.current_table: Optional[Table] = None
    
    def run(self) -> None:
        """Главный цикл приложения"""
        while True:
            self._show_main_menu()
            action = input("Выберите действие: ").strip()
            
            if action == "1":
                self._add_record()
            elif action == "2":
                self._show_all_records()
            elif action == "3":
                self._find_records()
            elif action == "4":
                self._update_record()
            elif action == "5":
                self._delete_record()
            elif action == "6":
                self._create_new_table()
            elif action == "7":
                self._show_tables()
            elif action == "8":
                self._select_table()
            elif action == "9":
                self._sort_records()
            elif action == "10":
                self._clear_table()
            elif action == "0":
                print("Выход из программы.")
                break
            else:
                print("Неизвестная команда. Повторите ввод.")
    
    def _show_main_menu(self) -> None:
        print("\n" + "=" * 50)
        print("СИСТЕМА УПРАВЛЕНИЯ БАЗОЙ ДАННЫХ")
        print("=" * 50)
        if self.current_table is not None:
            print(f"Текущая таблица: {self.current_table.name} (записей: {len(self.current_table)})")
        else:
            print("Текущая таблица: не выбрана")
        print("-" * 50)
        print("1. Добавить запись")
        print("2. Показать все записи")
        print("3. Найти записи по фильтру")
        print("4. Обновить запись")
        print("5. Удалить запись")
        print("6. Создать новую таблицу")
        print("7. Показать все таблицы")
        print("8. Выбрать таблицу")
        print("9. Сортировать записи")
        print("10. Очистить таблицу")
        print("0. Выход")
        print("-" * 50)
    
    def _read_int(self, prompt: str, optional: bool = False) -> Optional[int]:
        while True:
            raw = input(prompt).strip()
            if optional and raw == "":
                return None
            try:
                return int(raw)
            except ValueError:
                print("Ошибка: введите целое число.")
    
    def _read_data_dict(self) -> Dict[str, Any]:
        print("Введите поля (формат: поле=значение, пустая строка для завершения):")
        data = {}
        while True:
            entry = input("> ").strip()
            if not entry:
                break
            if '=' in entry:
                key, value = entry.split('=', 1)
                key = key.strip()
                value = parse_user_input(value.strip())
                data[key] = value
            else:
                print("Неверный формат! Используйте: поле=значение")
        return data
    
    def _print_records(self, records: List[Record]) -> None:
        if not records:
            print("Записи не найдены.")
            return
        print(f"\n{'ID':<6} {'Данные':<50}")
        print("-" * 58)
        for record in records:
            print(f"{record.id:<6} {record.data}")
    
    def _add_record(self) -> None:
        if self.current_table is None:
            print("Ошибка: сначала выберите таблицу (пункт 8)")
            return
        print(f"\n--- Добавление записи в таблицу '{self.current_table.name}' ---")
        data = self._read_data_dict()
        if not data:
            print("Нет данных для добавления.")
            return
        try:
            record = self.current_table.insert(data)
            print(f"✓ Запись добавлена: ID={record.id}, данные={record.data}")
        except InvalidAgeError as exc:
            print(f"✗ Ошибка возраста: {exc}")
        except Exception as exc:
            print(f"✗ Ошибка при добавлении: {exc}")
    
    def _show_all_records(self) -> None:
        if self.current_table is None:
            print("Ошибка: сначала выберите таблицу (пункт 8)")
            return
        print(f"\n--- Все записи таблицы '{self.current_table.name}' ---")
        self._print_records(self.current_table.all())
    
    def _find_records(self) -> None:
        if self.current_table is None:
            print("Ошибка: сначала выберите таблицу (пункт 8)")
            return
        print("\n--- Поиск по фильтру ---")
        criteria = {}
        while True:
            entry = input("Введите фильтр (поле=значение) или Enter для поиска: ").strip()
            if not entry:
                break
            if '=' in entry:
                key, value = entry.split('=', 1)
                key = key.strip()
                value = parse_user_input(value.strip())
                criteria[key] = value
            else:
                print("Неверный формат!")
        try:
            results = self.current_table.find(**criteria) if criteria else self.current_table.all()
            print(f"\nНайдено записей: {len(results)}")
            self._print_records(results)
        except Exception as exc:
            print(f"✗ Ошибка при поиске: {exc}")
    
    def _update_record(self) -> None:
        if self.current_table is None:
            print("Ошибка: сначала выберите таблицу (пункт 8)")
            return
        print("\n--- Обновление записи ---")
        record_id = self._read_int("Введите ID записи: ")
        if record_id is None:
            return
        existing = self.current_table.get(record_id)
        if existing is None:
            print(f"✗ Запись с ID={record_id} не найдена")
            return
        print(f"Текущие данные: {existing.data}")
        new_data = {}
        for key in existing.data.keys():
            value = input(f"  {key} (было: {existing.data[key]}) -> ").strip()
            if value:
                value = parse_user_input(value)
                new_data[key] = value
        if not new_data:
            print("Нет изменений.")
            return
        try:
            updated = self.current_table.update(record_id, new_data)
            print(f"✓ Запись обновлена: {updated.data}")
        except RecordNotFoundError as exc:
            print(f"✗ {exc}")
        except InvalidAgeError as exc:
            print(f"✗ Ошибка возраста: {exc}")
        except Exception as exc:
            print(f"✗ Ошибка: {exc}")
    
    def _delete_record(self) -> None:
        if self.current_table is None:
            print("Ошибка: сначала выберите таблицу (пункт 8)")
            return
        print("\n--- Удаление записи ---")
        record_id = self._read_int("Введите ID записи: ")
        if record_id is None:
            return
        existing = self.current_table.get(record_id)
        if existing is None:
            print(f"✗ Запись с ID={record_id} не найдена")
            return
        confirm = input(f"Удалить {existing.data}? (д/н): ").strip().lower()
        if confirm in ['д', 'yes', 'y', 'да']:
            self.current_table.delete(record_id)
            print(f"✓ Запись с ID={record_id} удалена")
        else:
            print("Удаление отменено")
    
    def _create_new_table(self) -> None:
        name = input("Введите имя новой таблицы: ").strip()
        if not name:
            print("Ошибка: имя не может быть пустым")
            return
        try:
            self.db.create_table(name)
            print(f"✓ Таблица '{name}' создана")
        except ValueError as exc:
            print(f"✗ Ошибка: {exc}")
    
    def _show_tables(self) -> None:
        tables = self.db.list_tables()
        if not tables:
            print("Нет таблиц")
            return
        print("\n--- Список таблиц ---")
        for name in tables:
            table = self.db.get_table(name)
            count = len(table) if table else 0
            print(f"  {name} (записей: {count})")
    
    def _select_table(self) -> None:
        tables = self.db.list_tables()
        if not tables:
            print("Нет таблиц")
            return
        print("\n--- Выбор таблицы ---")
        for i, name in enumerate(tables, 1):
            table = self.db.get_table(name)
            count = len(table) if table else 0
            print(f"{i}. {name} (записей: {count})")
        try:
            choice = int(input("Выберите номер: "))
            if 1 <= choice <= len(tables):
                self.current_table = self.db.get_table(tables[choice-1])
                print(f"✓ Выбрана таблица: {self.current_table.name}")
            else:
                print("Неверный номер")
        except ValueError:
            print("Введите число")
    
    def _sort_records(self) -> None:
        if self.current_table is None:
            print("Ошибка: сначала выберите таблицу (пункт 8)")
            return
        records = self.current_table.all()
        if not records:
            print("Нет записей для сортировки")
            return
        fields = ['id'] + list(records[0].data.keys())
        print(f"\nДоступные поля для сортировки: {', '.join(fields)}")
        field = input("Введите поле для сортировки: ").strip()
        if field not in fields:
            print(f"Поле '{field}' не найдено")
            return
        print("1 - по возрастанию")
        print("2 - по убыванию")
        order = input("Выберите порядок: ").strip()
        reverse = (order == '2')
        
        try:
            sorted_records = self.current_table.sort(field, reverse)
            order_text = "возрастанию" if not reverse else "убыванию"
            print(f"\nОтсортированные записи по полю '{field}' (по {order_text}):")
            self._print_records(sorted_records)
        except TypeError as exc:
            print(f"✗ Ошибка сортировки: {exc}")
    
    def _clear_table(self) -> None:
        if self.current_table is None:
            print("Ошибка: сначала выберите таблицу (пункт 8)")
            return
        confirm = input(f"Вы уверены, что хотите очистить таблицу '{self.current_table.name}'? (д/н): ").strip().lower()
        if confirm in ['д', 'yes', 'y', 'да']:
            self.current_table.clear()
            print("Таблица очищена!")


def run() -> None:
    """Запуск приложения с выбором типа БД и формата хранения"""
    print("\nВыберите тип базы данных:")
    print("1. In-Memory (данные не сохраняются)")
    print("2. Файловая (JSON)")
    print("3. Файловая (CSV)")
    
    choice = input("Ваш выбор (1/2/3): ").strip()
    
    try:
        if choice == "2":
            data_dir = input("Введите путь для хранения JSON (Enter для 'data'): ").strip()
            if not data_dir:
                data_dir = "data"
            db = FileDatabase(data_dir=data_dir)
            print(f"Используется файловая БД (JSON). Данные хранятся в: {data_dir}")
        elif choice == "3":
            data_dir = input("Введите путь для хранения CSV (Enter для 'data_csv'): ").strip()
            if not data_dir:
                data_dir = "data_csv"
            db = CSVDatabase(data_dir=data_dir)
            print(f"Используется файловая БД (CSV). Данные хранятся в: {data_dir}")
        else:
            db = InMemoryDatabase()
            print("Используется in-memory БД. Данные НЕ сохранятся после выхода.")
    except FileDatabaseError as e:
        print(f"Ошибка при создании файловой БД: {e}")
        print("Запуск с in-memory БД...")
        db = InMemoryDatabase()
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        print("Запуск с in-memory БД...")
        db = InMemoryDatabase()
    
    ui = ConsoleUI(db)
    ui.run()


if __name__ == "__main__":
    run()