import sqlite3
import sys
from datetime import datetime, timedelta


def get_habit_stats(cursor, start_timestamp, end_timestamp):
    # Получаем данные о привычках
    cursor.execute("SELECT id, name FROM Habits WHERE archived = 0")
    habits = {id: name for id, name in cursor.fetchall()}

    # Выборка данных за определенный период
    cursor.execute("""
        SELECT habit, value FROM Repetitions
        WHERE timestamp BETWEEN ? AND ?
    """, (start_timestamp, end_timestamp))
    repetitions = cursor.fetchall()

    # Анализ данных
    habit_stats = {habit: {'total': 0, 'count': 0} for habit in habits.keys()}
    for habit_id, value in repetitions:
        if habit_id in habit_stats:
            adjusted_value = value / 1000
            if habits[habit_id] == "Норма по калориям" and adjusted_value < 10:
                adjusted_value *= 1000
            if habit_id == 2:
                print(f'{habit_id} --- {adjusted_value}')
            habit_stats[habit_id]['total'] += adjusted_value
            habit_stats[habit_id]['count'] += 1

    print(habit_stats)
    print("\n================================")

    # Вывод результатов
    results = {}
    for habit_id, stats in habit_stats.items():
        if stats['count'] > 0:
            average = round(stats['total'] / stats['count'], 1)
        else:
            average = 0
        total = round(stats['total'], 1)
        results[habits[habit_id]] = {'Average': average, 'Total': total}

    return results


def analyze_current_week(db_path, start_date_str=None, end_date_str=None):
    if not start_date_str or not end_date_str:
        raise ValueError("Start and end dates must be provided in 'dd-mm-yyyy' format.")

    try:
        start_date = datetime.strptime(start_date_str, '%d-%m-%Y')
        end_date = datetime.strptime(end_date_str, '%d-%m-%Y') + timedelta(days=1)

    except ValueError as e:
        raise ValueError("Invalid date format. Please use 'dd-mm-yyyy' format.") from e

    print(f'{start_date=}')
    print(f'{end_date=}')

    # Конвертируем даты в миллисекунды
    start_timestamp = int(start_date.timestamp() * 1000)
    end_timestamp = int(end_date.timestamp() * 1000)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    results = get_habit_stats(cursor, start_timestamp, end_timestamp)
    conn.close()

    return results


def analyze_all_before(db_path, date_before):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Преобразование даты из строки в Timestamp
    end_date = datetime.strptime(date_before, "%d-%m-%Y")
    end_timestamp = int(end_date.timestamp() * 1000)

    # Установка временных рамок с начала эпохи Unix до указанной даты
    start_timestamp = 0

    results = get_habit_stats(cursor, start_timestamp, end_timestamp)

    conn.close()
    return results


def analyze_and_summarize(current_week_data, all_time_data, habits_where_more_is_worse, habits_without_total):
    summary = []
    for habit, current_data in current_week_data.items():
        all_time_avg = all_time_data.get(habit, {}).get('Average', 0)
        current_avg = current_data.get('Average', 0)
        current_total = current_data.get('Total', 0)

        if habit in habits_where_more_is_worse:
            better = current_avg < all_time_avg
        else:
            better = current_avg > all_time_avg

        if better:
            status = 'лучше'
            emoji = '😄'
        elif current_avg == all_time_avg:
            status = 'осталось как есть'
            emoji = '='
        else:
            status = 'хуже'
            emoji = '💔'


        if habit in habits_without_total:
            summary.append(f"{emoji}: {habit}, {status}, было: {all_time_avg}, стало: {current_avg}")
        else:
            summary.append(f"{emoji}: {habit}, {status}, было: {all_time_avg}, стало: {current_avg}, total: {round(all_time_avg * 7, 1)} VS {current_total}")

    return '\n'.join(summary)

def define_monday_sunday():
    today = datetime.now()

    # Находим ближайший понедельник в прошлом
    # Если сегодня понедельник, вычитаем 7 дней
    if today.weekday() == 0:
        last_monday = today - timedelta(days=7)
    else:
        last_monday = today - timedelta(days=today.weekday())

    # Находим ближайшее воскресенье в будущем от найденного понедельника
    next_sunday = last_monday + timedelta(days=6)

    # Форматируем даты
    date_monday = last_monday.strftime('%d-%m-%Y')
    date_sunday = next_sunday.strftime('%d-%m-%Y')

    return (date_monday, date_sunday)



db_current_name = 'Loop_2024-01-15.db'


date_monday, date_sunday = define_monday_sunday()
print(f"{date_monday=}, {date_sunday=}")

current_week_data = analyze_current_week(db_current_name, date_monday, date_sunday)
all_time_data = analyze_all_before(db_current_name, date_before=date_sunday)


# Вывод результатов
print("Данные за текущую неделю:")
for habit, data in current_week_data.items():
    print(f"Habit: {habit}, Average: {data['Average']}, Total: {data['Total']}")

print("\nДанные за все время:")
for habit, data in all_time_data.items():
    print(f"Habit: {habit}, Average: {data['Average']}, Total: {data['Total']}")


# Пример использования
habits_where_more_is_worse = ['Норма по калориям', 'Вес']  # Привычки, где больше значит хуже
habits_without_total = ['Вес', 'Норма по калориям', 'Уровень осознанности', 'Ум', 'Физика', 'Общая оценка']
result = analyze_and_summarize(current_week_data, all_time_data, habits_where_more_is_worse, habits_without_total)
print('==================================')
print(result)
