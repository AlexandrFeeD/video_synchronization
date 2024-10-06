import psycopg2
import os

data_folder = "data"

# Подключение к базе данных PostgreSQL
conn = psycopg2.connect(
    dbname="video_sync",
    user="postgres",
    password="admin",
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

# Список файлов аннотаций и видео
annotation_files = [os.path.join(data_folder, f'{i}.txt') for i in range(1, 5)]
video_files = [os.path.join(data_folder, f'{i}.avi') for i in range(1, 5)]

# Функция для загрузки данных из файлов и вставки в таблицу
def insert_annotations():
    for i, annotation_file in enumerate(annotation_files):
        video_name = os.path.basename(video_files[i])
        with open(annotation_file, 'r') as f:
            for line in f:
                timestamp = float(line.strip())
                cursor.execute(
                    """
                    INSERT INTO video_annotations (timestamp, video_name)
                    VALUES (%s, %s)
                    """, (timestamp, video_name)
                )
                print(f"Inserted: {timestamp}, {video_name}")

    conn.commit()

# Запуск функции
insert_annotations()

cursor.close()
conn.close()
