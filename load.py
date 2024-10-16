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

def insert_annotations(data_folder: str, config_path: str, sql_path: str) -> None:
    """
    Загружает данные аннотаций из файлов и вставляет их в таблицу базы данных.

    Args:
        data_folder (str): Путь к папке с файлами аннотаций.
        config_path (str): Путь к файлу конфигурации базы данных.
        sql_path (str): Путь к файлу с SQL запросом для вставки данных.
    """
    db_config = load_db_config(config_path)

    conn = connect_to_db(db_config)
    cursor = conn.cursor()

    insert_query = load_sql_query(sql_path)

    annotation_files = [os.path.join(data_folder, f'{i}.txt') for i in range(1, 5)]
    video_files = [os.path.join(data_folder, f'{i}.avi') for i in range(1, 5)]
    
    for i, annotation_file in enumerate(annotation_files):
        video_name = os.path.basename(video_files[i])
        with open(annotation_file, 'r') as f:
            for line in f:
                timestamp = float(line.strip())
                cursor.execute(insert_query, (timestamp, video_name))
                print(f"Inserted: {timestamp}, {video_name}")

    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    data_folder = "data"
    config_path = "./config/db_config.json"
    sql_path = "./sql/insert_annotation.sql"
    insert_annotations(data_folder, config_path, sql_path)
