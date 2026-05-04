-- Минимальная схема для smoke-теста: бот подхватывает любые таблицы из public.
-- Добавьте свои колонки под анкеты или создайте таблицы через миграции.

CREATE TABLE IF NOT EXISTS demo_anketa (
    id SERIAL PRIMARY KEY,
    tg_user_id BIGINT,
    payload JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE demo_anketa IS 'Пример: бот может писать сюда ответы формы (адаптируйте имена полей).';
