# Dostaffkin Backend

Simple Express API for deliveries with PostgreSQL storage.

## Setup

1. Create PostgreSQL database:

```sql
CREATE DATABASE dostaffkin;
```

2. Copy `.env.example` to `.env` and update credentials:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/dostaffkin
DATABASE_SSL=false
PORT=3000
```

3. Start the backend:

```bash
npm run backend
```

The server creates the `deliveries` table automatically on startup.

## API

```http
POST /delivery/create
GET /delivery/info?id=1
GET /health
```
