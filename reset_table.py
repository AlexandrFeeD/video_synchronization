import psycopg2
import os
import json
from typing import Dict

def load_db_config(config_path: str) -> Dict[str, str]:
    """
    Загружает параметры подключения к базе данных из JSON файла.

    Args:
        config_path (str): Путь к файлу конфигурации базы данных.

    Returns:
        Dict[str, str]: Параметры подключения к базе данных.
    """
    with open(config_path, 'r') as file:
        return json.load(file)

def load_sql_query(query_path: str) -> str:
    """
    Загружает SQL запрос из файла.

    Args:
        query_path (str): Путь к файлу с SQL запросом.

    Returns:
        str: Строка с SQL запросом.
    """
    with open(query_path, 'r') as file:
        return file.read().strip()

def connect_to_db(config: Dict[str, str]) -> psycopg2.extensions.connection:
    """
    Устанавливает соединение с базой данных PostgreSQL.

    Args:
        config (Dict[str, str]): Параметры подключения к базе данных.

    Returns:
        psycopg2.extensions.connection: Объект подключения к базе данных.
    """
    return psycopg2.connect(
        dbname=config["dbname"],
        user=config["user"],
        password=config["password"],
        host=config["host"],
        port=config["port"]
    )

def recreate_table(config_path: str, sql_path: str) -> None:
    """
    Удаляет таблицу, если она существует, и создает новую таблицу.

    Args:
        config_path (str): Путь к файлу конфигурации базы данных.
        sql_path (str): Путь к файлу с SQL запросом для создания таблицы.
    """
    db_config = load_db_config(config_path)

    conn = connect_to_db(db_config)
    cursor = conn.cursor()

    recreate_table_sql = load_sql_query(sql_path)

    try:
        cursor.execute(recreate_table_sql)
        conn.commit()
        print("Таблица video_annotations успешно создана заново.")
    except Exception as e:
        conn.rollback()
        print(f"Ошибка при создании таблицы: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    config_path = "./config/db_config.json"
    sql_path = "./sql/recreate_table.sql"
    recreate_table(config_path, sql_path)
