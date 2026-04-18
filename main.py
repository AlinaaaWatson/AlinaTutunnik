
from src.db.backend.memory import (
    Database, StudentTable, Table,
    create_record, select_record, update_record, delete_record,
    create_table, list_tables, get_table, get_db
)
from src.db.backend.errors import InvalidAgeError, DuplicateIDError, StudentTableError


def _print_menu() -> None:
    """Отображение главного меню"""
    print("\n" + "="*50)
    print("           БАЗА ДАННЫХ СТУДЕНТОВ")
    print("="*50)
    print("1. Добавить запись")
    print("2. Показать все записи")
    print("3. Найти записи по фильтру")
    print("4. Обновить запись")
    print("5. Удалить запись")
    print("6. Создать новую таблицу")
    print("7. Показать все таблицы")
    print("8. Информация о таблицах")
    print("0. Выход")
    print("-"*50)


def _print_tables_info() -> None:
    """Показать детальную информацию о всех таблицах"""
    print("\n--- Информация о таблицах ---")
    db = get_db()
    tables = db.list_tables()
    
    for table_name in tables:
        table = db.get_table(table_name)
        count = table.count() if table else 0
        print(f"{table_name}: {count} записей")
        
        # Для таблицы студентов показываем примеры
        if table_name == "Student" and count > 0:
            print("   Примеры записей:")
            records = table.all()[:3]  # Первые 3 записи
            for record in records:
                print(f"   ID:{record[0]}, {record[1]} {record[2]}, {record[3]} лет")


def _create_new_table() -> None:
    """Создание новой таблицы"""
    print("\n--- Создание новой таблицы ---")
    
    db = get_db()
    print("Существующие таблицы:", ", ".join(db.list_tables()))

    table_name = input("Введите имя новой таблицы: ").strip()

    try:
        if create_table(table_name):
            print(f"Таблица '{table_name}' успешно создана")
        else:
            print(f"Таблица '{table_name}' уже существует")
    except ValueError as exc:
        print(f"Ошибка: {exc}")


def _show_tables() -> None:
    """Показать все таблицы"""
    print("\n--- Доступные таблицы ---")
    db = get_db()
    tables = db.list_tables()
    
    if not tables:
        print("Нет доступных таблиц")
        return
    
    for i, table_name in enumerate(tables, 1):
        table = db.get_table(table_name)
        count = table.count() if table else 0
        table_type = "Студенты" if table_name == "Student" else "Обычная"
        print(f"{i}. {table_name} - {table_type} (записей: {count})")


def _read_int(prompt: str) -> int:
    """
    Чтение целочисленного значения из консоли.
    
    Args:
        prompt: Приглашение для ввода
        
    Returns:
        Введенное целое число
    """
    while True:
        raw = input(prompt).strip()
        try:
            return int(raw)
        except ValueError:
            print("Ошибка: введите целое число.")


def _read_optional_int(prompt: str) -> int | None:
    """
    Чтение необязательного целочисленного значения.
    
    Args:
        prompt: Приглашение для ввода
        
    Returns:
        Введенное число или None, если ввод пустой
    """
    while True:
        raw = input(prompt).strip()
        if raw == "":
            return None
        try:
            return int(raw)
        except ValueError:
            print("Ошибка: введите целое число или оставьте поле пустым.")


def _print_records(records: list[tuple]) -> None:
    """
    Вывод списка записей в форматированном виде.
    
    Args:
        records: Список записей для вывода
    """
    if not records:
        print("📭 Записи не найдены.")
        return
    
    print(f"\nНайдено записей: {len(records)}")
    print("-" * 60)
    for record in records:
        print(f"ID: {record[0]:<3} | {record[1]:<10} {record[2]:<10} | Возраст: {record[3]:<3} | Пол: {record[4]}")
    print("-" * 60)


def _add_student() -> None:
    """Добавление новой записи"""
    print("\n--- Добавление новой записи ---")

    try:
        student_id = _read_int("ID студента: ")
        first_name = input("Имя: ").strip()
        if not first_name:
            print("Имя не может быть пустым")
            return
            
        second_name = input("Фамилия: ").strip()
        if not second_name:
            print("Фамилия не может быть пустой")
            return
            
        age = _read_int("Возраст: ")
        sex = input("Пол (M/F): ").strip().upper()
        if sex not in ['M', 'F']:
            print("Пол должен быть M или F")
            return

        # Используем функцию совместимости
        record = create_record(student_id, first_name, second_name, age, sex)

        print(f"\nЗапись успешно добавлена:")
        print(f"   ID: {record[0]}, {record[1]} {record[2]}, {record[3]} лет, пол: {record[4]}")

    except InvalidAgeError as exc:
        print(f"Ошибка валидации возраста: {exc}")
    except DuplicateIDError as exc:
        print(f"Ошибка: {exc}")
    except ValueError as exc:
        print(f"Ошибка ввода: {exc}")
    except Exception as exc:
        print(f"Непредвиденная ошибка: {exc}")


def _show_all_students() -> None:
    """Показать все записи"""
    print("\n--- Все записи ---")
    records = select_record()
    _print_records(records)


def _find_students_by_filter() -> None:
    """Поиск записей по фильтру"""
    print("\n--- Поиск по фильтру ---")
    print("(Enter = пропустить поле)")

    try:
        student_id = _read_optional_int("ID: ")
        first_name = input("Имя: ").strip() or None
        second_name = input("Фамилия: ").strip() or None
        age = _read_optional_int("Возраст: ")
        sex = input("Пол (M/F): ").strip().upper() or None
        if sex and sex not in ['M', 'F']:
            print("Пол должен быть M или F")
            return

        records = select_record(
            student_id=student_id,
            first_name=first_name,
            second_name=second_name,
            age=age,
            sex=sex,
        )

        _print_records(records)

    except Exception as exc:
        print(f"Ошибка при поиске: {exc}")


def _update_student() -> None:
    """Обновление записи"""
    print("\n--- Обновление записи ---")

    try:
        student_id = _read_int("ID записи для обновления: ")

        # Проверяем существование записи
        existing = select_record(student_id=student_id)
        if not existing:
            print(f"Запись с ID={student_id} не найдена")
            return

        print("\nТекущие данные:")
        record = existing[0]
        print(f"   ID: {record[0]}")
        print(f"   Имя: {record[1]}")
        print(f"   Фамилия: {record[2]}")
        print(f"   Возраст: {record[3]}")
        print(f"   Пол: {record[4]}")
        print("\n(Оставьте поле пустым, чтобы не менять)")

        # Чтение новых значений
        first_name = input("Новое имя (Enter - без изменений): ").strip()
        first_name = first_name if first_name else None

        second_name = input("Новая фамилия (Enter - без изменений): ").strip()
        second_name = second_name if second_name else None

        age_input = input("Новый возраст (Enter - без изменений): ").strip()
        age = int(age_input) if age_input else None

        sex = input("Новый пол (M/F) (Enter - без изменений): ").strip().upper()
        if sex and sex not in ['M', 'F']:
            print("Пол должен быть M или F")
            return
        sex = sex if sex else None

        # Обновление записи
        updated = update_record(
            student_id,
            first_name=first_name,
            second_name=second_name,
            age=age,
            sex=sex
        )

        if updated:
            print(f"\nЗапись обновлена:")
            print(f"   ID: {updated[0]}, {updated[1]} {updated[2]}, {updated[3]} лет, пол: {updated[4]}")
        else:
            print("Не удалось обновить запись")

    except InvalidAgeError as exc:
        print(f"Ошибка валидации возраста: {exc}")
    except ValueError as exc:
        print(f"Ошибка ввода: {exc}")
    except Exception as exc:
        print(f"Непредвиденная ошибка: {exc}")


def _delete_student() -> None:
    """Удаление записи"""
    print("\n--- Удаление записи ---")

    try:
        student_id = _read_int("ID записи для удаления: ")

        # Показываем запись перед удалением
        existing = select_record(student_id=student_id)
        if not existing:
            print(f"Запись с ID={student_id} не найдена")
            return

        print("\nЗапись для удаления:")
        record = existing[0]
        print(f"   ID: {record[0]}, {record[1]} {record[2]}, {record[3]} лет, пол: {record[4]}")

        confirm = input("\nВы уверены? (д/н): ").strip().lower()
        if confirm in ['д', 'yes', 'y', 'да']:
            deleted = delete_record(student_id)
            if deleted:
                print(f"Запись с ID={student_id} удалена")
            else:
                print(f"Не удалось удалить запись")
        else:
            print("Удаление отменено")

    except Exception as exc:
        print(f"Ошибка при удалении: {exc}")


def run() -> None:
    """
    Запускает основной цикл текстового пользовательского интерфейса.
    """
    print("="*50)
    print("Добро пожаловать в систему управления базой данных студентов!")
    print("="*50)
    
    # Показываем информацию о таблицах при старте
    db = get_db()
    tables = db.list_tables()
    print(f"\nДоступные таблицы: {', '.join(tables)}")
    print(f"Всего записей в Student: {db.get_student_table().count() if db.get_student_table() else 0}")

    while True:
        _print_menu()
        
        action = input("Выберите действие: ").strip()

        if action == "1":
            _add_student()

        elif action == "2":
            _show_all_students()

        elif action == "3":
            _find_students_by_filter()

        elif action == "4":
            _update_student()

        elif action == "5":
            _delete_student()

        elif action == "6":
            _create_new_table()

        elif action == "7":
            _show_tables()
            
        elif action == "8":
            _print_tables_info()

        elif action == "0":
            print("\nСпасибо за использование системы! До свидания!")
            break

        else:
            print("Неизвестная команда. Пожалуйста, выберите действие от 0 до 8.")

        input("\nНажмите Enter для продолжения...")


if __name__ == "__main__":
    run()