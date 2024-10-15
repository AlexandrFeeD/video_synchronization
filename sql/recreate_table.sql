-- SQL запрос для удаления таблицы, если она существует
DROP TABLE IF EXISTS video_annotations;

-- SQL запрос для создания таблицы
CREATE TABLE video_annotations (
    id SERIAL PRIMARY KEY,
    timestamp DECIMAL,
    video_name VARCHAR(255)
);