require('dotenv').config();

const express = require('express');
const cors = require('cors');
const { Pool } = require('pg');

const app = express();
const PORT = process.env.PORT || 3000;
const DATABASE_URL = process.env.DATABASE_URL;

if (!DATABASE_URL) {
  throw new Error('DATABASE_URL is not set. Add it to .env before starting backend.');
}

const pool = new Pool({
  connectionString: DATABASE_URL,
  ssl: process.env.DATABASE_SSL === 'true' ? { rejectUnauthorized: false } : false,
});

app.use(cors());
app.use(express.json());

async function initDb() {
  await pool.query(`
    CREATE TABLE IF NOT EXISTS deliveries (
      id SERIAL PRIMARY KEY,
      customer JSONB NOT NULL,
      calculation JSONB NOT NULL,
      route JSONB NOT NULL,
      statuses JSONB NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
  `);
}

function addDays(date, days) {
  const result = new Date(date);
  result.setDate(result.getDate() + days);
  return result;
}

function formatDate(date) {
  return new Intl.DateTimeFormat('ru-RU').format(date);
}

function createStatuses(createdAt, duration) {
  const createdDate = new Date(createdAt);
  const safeDuration = Number.isFinite(duration) ? Math.max(1, duration) : 3;
  const statuses = [
    { type: 'created', label: 'Создан', date: formatDate(createdDate) },
    { type: 'in-way', label: 'В пути', date: formatDate(addDays(createdDate, 1)) },
  ];

  if (safeDuration <= 2) {
    statuses.push({
      type: 'ready',
      label: 'Готов к выдаче',
      date: formatDate(addDays(createdDate, safeDuration)),
    });
    return statuses;
  }

  statuses.push({
    type: 'in-way',
    label: 'В пути: сортировочный центр',
    date: formatDate(addDays(createdDate, Math.ceil(safeDuration / 2))),
  });
  statuses.push({
    type: 'ready',
    label: 'Готов к выдаче',
    date: formatDate(addDays(createdDate, safeDuration)),
  });

  return statuses;
}

app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

app.post('/delivery/create', async (req, res, next) => {
  try {
    const payload = req.body;
    const calculation = payload?.calculation;
    const customer = payload?.customer;

    if (!calculation?.from || !calculation?.to) {
      return res.status(400).json({ error: 'Не передан маршрут доставки' });
    }

    if (!customer?.name || !customer?.phone) {
      return res.status(400).json({ error: 'Не переданы контактные данные' });
    }

    const createdAt = payload.createdAt || new Date().toISOString();
    const route = {
      from: calculation.from,
      to: calculation.to,
    };
    const statuses = createStatuses(createdAt, Number(calculation.duration));

    const result = await pool.query(
      `
        INSERT INTO deliveries (customer, calculation, route, statuses, created_at)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id;
      `,
      [customer, calculation, route, statuses, createdAt],
    );

    res.status(201).json({ id: result.rows[0].id });
  } catch (error) {
    next(error);
  }
});

app.get('/delivery/info', async (req, res, next) => {
  try {
    const id = Number(req.query.id);

    if (!Number.isInteger(id) || id <= 0) {
      return res.status(400).json({ error: 'Введите корректный номер отправления' });
    }

    const result = await pool.query(
      `
        SELECT id, route, statuses
        FROM deliveries
        WHERE id = $1;
      `,
      [id],
    );
    const delivery = result.rows[0];

    if (!delivery) {
      return res.status(404).json({ error: 'Отправление не найдено' });
    }

    res.json({
      id: delivery.id,
      route: delivery.route,
      statuses: delivery.statuses,
    });
  } catch (error) {
    next(error);
  }
});

app.use((error, req, res, next) => {
  console.error(error);
  res.status(500).json({ error: 'Ошибка сервера' });
});

initDb()
  .then(() => {
    app.listen(PORT, () => {
      console.log(`Delivery API is running on http://localhost:${PORT}`);
    });
  })
  .catch((error) => {
    console.error('Failed to initialize database', error);
    process.exit(1);
  });
