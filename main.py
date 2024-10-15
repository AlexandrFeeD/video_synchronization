import tkinter as tk
import cv2
from PIL import Image, ImageTk
import psycopg2
import time
from decimal import Decimal
import bisect
import os
import json
from typing import List, Dict, Tuple

def load_db_config(file_path: str) -> Dict[str, str]:
    """
    Загружает параметры подключения к базе данных из JSON файла.

    Args:
        file_path (str): Путь к JSON файлу.

    Returns:
        Dict[str, str]: Параметры подключения к базе данных.
    """
    with open(file_path, 'r') as file:
        config = json.load(file)
    return config

def load_sql_query(file_path: str) -> str:
    """
    Загружает SQL запрос из файла.

    Args:
        file_path (str): Путь к SQL файлу.

    Returns:
        str: Строка с SQL запросом.
    """
    with open(file_path, 'r') as file:
        query = file.read().strip()
    return query

def load_annotations(db_config: Dict[str, str], sql_query: str) -> List[Tuple[Decimal, str]]:
    """
    Загружает аннотации из базы данных.

    Args:
        db_config (Dict[str, str]): Параметры подключения к базе данных.
        sql_query (str): SQL запрос.

    Returns:
        List[Tuple[Decimal, str]]: Список аннотаций в виде кортежей (timestamp, video_name).
    """
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute(sql_query)
    annotations = cursor.fetchall()
    cursor.close()
    conn.close()
    return annotations

def get_index_min_timestamp(annotation_list: List[Decimal], current_timestamp: Decimal) -> int:
    """
    Возвращает индекс ближайшего элемента в списке аннотаций с помощью бинарного поиска.

    Args:
        annotation_list (List[Decimal]): Список аннотаций (timestamps).
        current_timestamp (Decimal): Текущий временной момент.

    Returns:
        int: Индекс ближайшего элемента в списке.
    """
    idx = bisect.bisect_left(annotation_list, current_timestamp)
    
    if idx == 0:
        return 0
    if idx == len(annotation_list):
        return len(annotation_list) - 1
    before = annotation_list[idx - 1]
    after = annotation_list[idx]
    
    return idx - 1 if abs(current_timestamp - before) < abs(after - current_timestamp) else idx

def parse_video(video_path: str) -> List[cv2.Mat]:
    """
    Читает видеофайл и загружает его кадры в память.

    Args:
        video_path (str): Путь к видеофайлу.

    Returns:
        List[cv2.Mat]: Список кадров из видео.
    """
    cap = cv2.VideoCapture(video_path)
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()
    return frames

class VideoSyncPlayer:
    def __init__(self, root: tk.Tk, video_paths: List[str], annotations: List[Tuple[Decimal, str]]) -> None:
        """
        Инициализация класса синхронного воспроизведения видео.

        Args:
            root (tk.Tk): Главный объект окна.
            video_paths (List[str]): Список путей к видеофайлам.
            annotations (List[Tuple[Decimal, str]]): Список аннотаций (timestamp, video_name).
        """
        self.root = root
        self.root.title("Синхронное воспроизведение видео")
        self.root.resizable(False, False)

        # Список путей к видеофайлам
        self.video_paths = [video_paths[3], video_paths[0], video_paths[2], video_paths[1]]

        # Распарсим все видео и сохраним кадры в память
        self.frames_list = [parse_video(path) for path in self.video_paths]

        # Список аннотаций (по видео)
        self.annotations: Dict[str, List[Decimal]] = {os.path.basename(name): [] for name in video_paths}
        for timestamp, video_name in annotations:
            self.annotations[video_name].append(timestamp)

        # Частота кадров и скорость
        self.frame_rate = 5
        self.delay = 1000 // self.frame_rate
        self.speed_options = {"0.2x": 1, "1x": 5, "10x": 50, "200x": 1000}
        
        # Флаг для состояния воспроизведения
        self.playing = False

        # Текущий временной момент
        self.current_time = min(self.annotations[os.path.basename(video)][0] for video in self.video_paths)

        # Флаг для завершения
        self.completed = False

        # Создаем контейнеры для отображения видео и меток
        self.labels = [tk.Label(root) for _ in self.video_paths]
        self.timestamp_labels = [tk.Label(root) for _ in self.video_paths]

        # Размещаем метки для видео и временные метки в сетке (2х2)
        for i in range(2):
            for j in range(2):
                idx = i * 2 + j
                self.labels[idx].grid(row=i, column=j)
                self.timestamp_labels[idx].grid(row=i + 2, column=j)

        # Выпадающий список для выбора скорости
        self.speed_var = tk.StringVar(value="1x")
        self.speed_menu = tk.OptionMenu(root, self.speed_var, *self.speed_options.keys(), command=self.change_speed)

        # Кнопки управления
        self.start_button = tk.Button(root, text="Старт", command=self.start_videos)
        self.stop_button = tk.Button(root, text="Стоп", command=self.stop_videos)
        self.next_frame_button = tk.Button(root, text="Следующий кадр", command=self.show_next_frame, state=tk.DISABLED)
        self.restart_button = tk.Button(root, text="Заново", command=self.restart)
        self.finish_label = tk.Label(root, text="", font=("Arial", 20))

        self.start_button.config(font=("Arial", 20))
        self.start_button.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        self.sync_videos()

    def change_speed(self, selection: str) -> None:
        """
        Изменение скорости воспроизведения на основе выбора пользователя.

        Args:
            selection (str): Выбранная скорость.
        """
        self.frame_rate = self.speed_options[selection]
        self.delay = 1000 // self.frame_rate

    def update_frame(self, video_name: str, i: int) -> None:
        """
        Обновляет кадр для заданного видео.

        Args:
            video_name (str): Имя видеофайла.
            i (int): Индекс видео в списке.
        """
        frame_index = get_index_min_timestamp(self.annotations[video_name], self.current_time)
        frame = self.frames_list[i][frame_index]

        is_old = self.annotations[video_name][frame_index] < self.current_time
        timestamp_text = f"{video_name} Timestamp: {self.annotations[video_name][frame_index]}"
        color = (0, 0, 255) if is_old else (0, 0, 0)
        frame = cv2.putText(cv2.resize(frame, (512, 300)), timestamp_text, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_image = ImageTk.PhotoImage(Image.fromarray(frame))
        self.labels[i].config(image=frame_image)
        self.labels[i].image = frame_image

    def sync_videos(self) -> None:
        """
        Синхронизирует воспроизведение всех видео.
        """
        if self.playing:
            for i, video_name in enumerate([os.path.basename(p) for p in self.video_paths]):
                self.update_frame(video_name, i)

            if all(self.current_time >= max(self.annotations[os.path.basename(p)]) for p in self.video_paths):
                self.playing = False
                self.finish_label.config(text="Завершено", fg="green")
                self.finish_label.grid(row=2, column=0, columnspan=2)
                self.restart_button.grid(row=3, column=0, columnspan=2)
            else:
                self.current_time += Decimal('0.200')
                self.root.after(self.delay, self.sync_videos)

    def show_next_frame(self) -> None:
        """
        Отображает следующий кадр при остановленном воспроизведении.
        """
        if not self.playing:
            for i, video_name in enumerate([os.path.basename(p) for p in self.video_paths]):
                self.update_frame(video_name, i)
            self.current_time += Decimal('0.200')

    def start_videos(self) -> None:
        """
        Начинает воспроизведение видео.
        """
        if not self.playing:
            self.playing = True
            self.start_button.place_forget()
            self.start_button.config(font=("Arial", 10))
            self.start_button.grid(row=2, column=0, pady=10)
            self.speed_menu.grid(row=3, column=0, pady=10)
            self.stop_button.grid(row=2, column=1, pady=10)
            self.next_frame_button.grid(row=3, column=1, pady=10)
            self.next_frame_button.config(state=tk.DISABLED)
            self.sync_videos()

    def stop_videos(self) -> None:
        """
        Останавливает воспроизведение видео.
        """
        if self.playing:
            self.playing = False
            self.next_frame_button.config(state=tk.NORMAL)

    def restart(self) -> None:
        """
        Перезапускает воспроизведение с начала.
        """
        self.finish_label.config(text="")
        self.restart_button.grid_forget()
        self.current_time = min(self.annotations[os.path.basename(video)][0] for video in self.video_paths)
        self.playing = False
        self.start_videos()

if __name__ == "__main__":
    root = tk.Tk()

    db_config = load_db_config("./config/db_config.json")
    sql_query = load_sql_query("./sql/queries.sql")
    data_folder = "data"
    video_files = [os.path.join(data_folder, f'{i}.avi') for i in range(1, 5)]  # 1.avi, 2.avi, 3.avi, 4.avi
    annotations = load_annotations(db_config, sql_query)

    player = VideoSyncPlayer(root, video_files, annotations)
    root.geometry("1050x800")
    root.mainloop()
