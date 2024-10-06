import tkinter as tk
import cv2
from PIL import Image, ImageTk
import psycopg2
import time
from decimal import Decimal
import bisect
import os

data_folder = "data"

# Параметры подключения к базе данных
DB_PARAMS = {
    'dbname': 'video_sync',
    'user': 'postgres',
    'password': 'admin',
    'host': 'localhost',
    'port': '5432'
}

# Подключаемся к базе данных
conn = psycopg2.connect(**DB_PARAMS)
cursor = conn.cursor()

# Получение аннотаций для всех видео
def load_annotations():
    cursor.execute("SELECT timestamp, video_name FROM video_annotations ORDER BY video_name, timestamp")
    return cursor.fetchall()

# Функция для бинарного поиска ближайшего timestamp
def get_index_min_timestamp(annotation_list, current_timestamp):
    
    # Используем bisect для бинарного поиска, возвращает индекс ближайшего элемента в списке аннотаций
    idx = bisect.bisect_left(annotation_list, current_timestamp)
    
    # Определяем, какой из двух ближайших индексов (idx или idx-1) ближе к текущему времени
    if idx == 0:
        return 0
    if idx == len(annotation_list):
        return len(annotation_list) - 1
    before = annotation_list[idx - 1]
    after = annotation_list[idx]
    
    # Возвращаем индекс ближайшего timestamp
    if abs(current_timestamp - before) < abs(after - current_timestamp):
        return idx - 1
    else:
        return idx

# Настройка GUI
class VideoSyncPlayer:
    def __init__(self, root, video_paths, annotations):
        self.root = root
        self.root.title("Синхронное воспроизведение видео")
        
        # Список путей к видеофайлам
        self.video_paths = video_paths
        self.cap_list = [cv2.VideoCapture(path) for path in self.video_paths]

        # Список аннотаций (по видео)
        self.annotations = {os.path.basename(name): [] for name in video_paths}
        for timestamp, video_name in annotations:
            self.annotations[video_name].append(timestamp)

        # Частота кадров и скорость
        self.frame_rate = 5
        self.delay = 1000 // self.frame_rate  # Задержка в миллисекундах между кадрами
        self.speed_options = {"0.2x": 1, "1x": 5, "10x": 50}
        
        # Флаг для состояния воспроизведения
        self.playing = True

        # Текущий временной момент
        self.current_time = min(self.annotations[os.path.basename(video)][0] for video in self.video_paths)

        # Создаем контейнеры для отображения видео и меток
        self.labels = [tk.Label(root) for _ in self.video_paths]
        self.timestamp_labels = [tk.Label(root, text="", font=("Arial", 12)) for _ in self.video_paths]

        # Размещаем метки для видео и временные метки в сетке (2х2)
        for i in range(2):
            for j in range(2):
                idx = i * 2 + j
                self.labels[idx].grid(row=i, column=j)
                self.timestamp_labels[idx].grid(row=i + 2, column=j)

        # Выпадающий список для выбора скорости
        self.speed_var = tk.StringVar(value="1x")
        self.speed_menu = tk.OptionMenu(root, self.speed_var, *self.speed_options.keys(), command=self.change_speed)
        self.speed_menu.grid(row=5, column=0, pady=10)

        # Кнопки управления
        self.start_button = tk.Button(root, text="Старт", command=self.start_videos)
        self.start_button.grid(row=4, column=0, pady=10)

        self.stop_button = tk.Button(root, text="Стоп", command=self.stop_videos)
        self.stop_button.grid(row=4, column=1, pady=10)

        # Кнопка для отображения следующего кадра
        self.next_frame_button = tk.Button(root, text="Следующий кадр", command=self.show_next_frame, state=tk.DISABLED)
        self.next_frame_button.grid(row=5, column=1, pady=10)

        # Запуск синхронного воспроизведения
        self.sync_videos()

    def change_speed(self, selection):
        
        #Изменение скорости воспроизведения на основе выбора пользователя.
        self.frame_rate = self.speed_options[selection]
        self.delay = 1000 // self.frame_rate  # Обновляем задержку между кадрами

    def sync_videos(self):
        if self.playing:
            for i, cap in enumerate(self.cap_list):
                video_name = os.path.basename(self.video_paths[i])
                
                # Получаем индекс ближайшего timestamp с помощью бинарного поиска
                frame_index = get_index_min_timestamp(self.annotations[video_name], self.current_time)
                
                # Устанавливаем текущий кадр на основе найденного индекса
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)

                ret, frame = cap.read()
                if ret:
                    # Преобразуем изображение для отображения в Tkinter
                    frame = cv2.resize(frame, (480, 320))  # Уменьшаем размер видео, чтобы поместить их на экран
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame_image = ImageTk.PhotoImage(Image.fromarray(frame))
                    self.labels[i].config(image=frame_image)
                    self.labels[i].image = frame_image

                    # Обновляем временные метки
                    current_timestamp = self.annotations[video_name][frame_index]
                    self.timestamp_labels[i].config(text=f"{video_name} Timestamp: {current_timestamp}")

            # Приводим шаг времени к Decimal и прибавляем
            self.current_time += Decimal('0.200')  # Шаг в Decimal
            self.root.after(self.delay, self.sync_videos)

    def show_next_frame(self):

        #Отображает следующий кадр при остановленном воспроизведении.
        if not self.playing:
            for i, cap in enumerate(self.cap_list):
                video_name = os.path.basename(self.video_paths[i])
                
                # Получаем индекс ближайшего timestamp
                frame_index = get_index_min_timestamp(self.annotations[video_name], self.current_time)
                
                # Устанавливаем текущий кадр на основе найденного индекса
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)

                ret, frame = cap.read()
                if ret:
                    # Преобразуем изображение для отображения в Tkinter
                    frame = cv2.resize(frame, (480, 320))  # Уменьшаем размер видео, чтобы поместить их на экран
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame_image = ImageTk.PhotoImage(Image.fromarray(frame))
                    self.labels[i].config(image=frame_image)
                    self.labels[i].image = frame_image

                    # Обновляем временные метки
                    current_timestamp = self.annotations[video_name][frame_index]
                    self.timestamp_labels[i].config(text=f"{video_name} Timestamp: {current_timestamp}")

            # Увеличиваем текущее время для следующего кадра
            self.current_time += Decimal('0.200')

    def start_videos(self):
        self.playing = True
        self.next_frame_button.config(state=tk.DISABLED)  # Отключаем кнопку следующего кадра
        self.sync_videos()

    def stop_videos(self):
        self.playing = False
        self.next_frame_button.config(state=tk.NORMAL)  # Включаем кнопку следующего кадра

# Загружаем аннотации
annotations = load_annotations()

# Запускаем GUI
if __name__ == "__main__":
    root = tk.Tk()

    # Пути к видеофайлам
    video_files = [os.path.join(data_folder, f'{i}.avi') for i in range(1, 5)]  # 1.avi, 2.avi, 3.avi, 4.avi

    # Инициализация синхронного воспроизведения
    player = VideoSyncPlayer(root, video_files, annotations)

    # Увеличиваем размер окна для размещения 4 видео и кнопок
    root.geometry("1100x800")  # Размер окна

    # Запуск главного цикла приложения
    root.mainloop()

# Закрытие подключения к базе данных
cursor.close()
conn.close()
