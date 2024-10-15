# Синхронное Воспроизведение Видео

**_Приложение для синхронного воспроизведения нескольких видео с регулировкой скорости воспроизведения._**

_Выполнено:_

- GUI с синхронным воспроизведением 4х видео.
- Регулировка скорости воспроизведения: 0,2х – 1к/с, 1х – 5 к/с, 10х – 50 к/с, 200х – 1000 к/с.
- Отображение следующих кадров при остановленном воспроизведении.
- Метки времени добавлены прямо на каждый кадр. Метка подсвечивается красным цветом, если кадр старый.
- Автоматическое завершение воспроизведения с выводом уведомления и возможностью начать заново.

## Установка

1. Клонируйте репозиторий с GitHub:

```bash
git clone https://github.com/AlexandrFeeD/video_synchronization.git
```

2. Перейдите в директорию проекта:

```bash
cd video_synchronization
```

3. Создать виртуальное окружение:

```bash
python -m venv venv
```

4. Активировать виртуальное окружение:

```bash
source  ./venv/bin/activate
```

3. Установите необходимые библиотеки:

```bash
pip install -r requirements.txt
```

## Настройка базы данных

1. Убедитесь, что PostgreSQL настроен и запущен.

> Я использовал:
>
> - База данных: video_sync
> - Имя пользователя: postgres
> - Пароль: admin
> - Хост: localhost
> - Порт: 5432

2. Настройте подключение к базе данных в файле `db_config.json`. Пример структуры:

```json
{
  "dbname": "video_sync",
  "user": "postgres",
  "password": "admin",
  "host": "localhost",
  "port": "5432"
}
```

## Запуск

1. Поместите данные в папку data:

- Видео файлы: `1.avi`, `2.avi`, `3.avi`, `4.avi`
- Текстовые файлы аннотаций: `1.txt`, `2.txt`, `3.txt`, `4.txt`

2. Используйте `reset_table.py` для создания таблицы, либо пересоздания таблицы в базе данных.

```bash
python reset_table.py
```

3. Используйте `load.py` для загрузки данных аннотаций (временных меток) в базу данных:

```bash
python load.py
```

3. Запустите приложение:

```bash
python main.py
```
