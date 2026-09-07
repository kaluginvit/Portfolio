/**
 * demoAdapter.ts — in-memory CRUD mock for VITE_DEMO_MODE=true.
 *
 * Provides the same get/post/patch/put/delete interface as axios
 * but operates entirely against synthetic seed data in browser memory.
 * No real API calls are made.
 */
import type { Client, Deal, Task, Paginated, GoogleSettings } from '../types'

const DEMO_MSG = 'Demo Mode — Google integration disabled.'
const SEED_TS = '2026-09-08T00:00:00Z'

const ts = () => new Date().toISOString()

// ── Seed data ─────────────────────────────────────────────────────────────────

let clients: Client[] = [
  { id: 1, name: 'Анна Соколова',     email: 'anna@techstart.ru',      phone: '+7 921 100-01-01', company: 'TechStart',    status: 'active',   created_at: SEED_TS, updated_at: SEED_TS },
  { id: 2, name: 'Михаил Громов',     email: 'm.gromov@finbridge.ru',  phone: '+7 912 200-02-02', company: 'FinBridge',    status: 'active',   created_at: SEED_TS, updated_at: SEED_TS },
  { id: 3, name: 'Ольга Иванова',     email: 'o.ivanova@cloudsync.io', phone: '+7 903 300-03-03', company: 'CloudSync',    status: 'active',   created_at: SEED_TS, updated_at: SEED_TS },
  { id: 4, name: 'Дмитрий Волков',    email: 'd.volkov@digitallab.ru', phone: null,               company: 'DigitalLab',   status: 'active',   created_at: SEED_TS, updated_at: SEED_TS },
  { id: 5, name: 'Екатерина Смирнова',email: 'kate@retailmax.ru',      phone: '+7 916 400-04-04', company: 'RetailMax',    status: 'active',   created_at: SEED_TS, updated_at: SEED_TS },
  { id: 6, name: 'Артём Петров',      email: 'a.petrov@agro-invest.ru',phone: '+7 925 500-05-05', company: 'АгроИнвест',  status: 'active',   created_at: SEED_TS, updated_at: SEED_TS },
  { id: 7, name: 'Наталья Чернова',   email: 'n.chernova@media.ru',    phone: null,               company: 'MediaGroup',   status: 'archived', created_at: SEED_TS, updated_at: SEED_TS },
  { id: 8, name: 'Сергей Белов',      email: 's.belov@construkt.ru',   phone: '+7 911 600-06-06', company: 'КонструктПро', status: 'archived', created_at: SEED_TS, updated_at: SEED_TS },
  { id: 9, name: 'Марина Козлова',    email: 'marina@healthbridge.ru', phone: '+7 906 700-07-07', company: 'HealthBridge', status: 'active',   created_at: SEED_TS, updated_at: SEED_TS },
  { id: 10,name: 'Павел Орлов',       email: 'p.orlov@softdev.ru',     phone: '+7 929 800-08-08', company: 'SoftDev',      status: 'active',   created_at: SEED_TS, updated_at: SEED_TS },
]

let deals: Deal[] = [
  { id: 1,  title: 'CRM внедрение',                     amount: 850000,  currency: 'RUB', stage: 'proposal',  client_id: 1,  opened_at: '2026-01-15', expected_close: '2026-03-31', created_at: SEED_TS, updated_at: SEED_TS },
  { id: 2,  title: 'API интеграция',                    amount: 320000,  currency: 'RUB', stage: 'won',       client_id: 2,  opened_at: '2026-02-01', expected_close: '2026-04-30', created_at: SEED_TS, updated_at: SEED_TS },
  { id: 3,  title: 'Облачная миграция',                 amount: 1200000, currency: 'RUB', stage: 'qualified', client_id: 3,  opened_at: '2026-03-10', expected_close: '2026-09-30', created_at: SEED_TS, updated_at: SEED_TS },
  { id: 4,  title: 'Разработка мобильного приложения',  amount: 450000,  currency: 'RUB', stage: 'lead',      client_id: 4,  opened_at: '2026-04-05', expected_close: null,         created_at: SEED_TS, updated_at: SEED_TS },
  { id: 5,  title: 'E-commerce платформа',              amount: 2100000, currency: 'RUB', stage: 'proposal',  client_id: 5,  opened_at: '2026-01-20', expected_close: '2026-12-31', created_at: SEED_TS, updated_at: SEED_TS },
  { id: 6,  title: 'Автоматизация склада',              amount: 680000,  currency: 'RUB', stage: 'qualified', client_id: 6,  opened_at: '2026-05-01', expected_close: '2026-10-15', created_at: SEED_TS, updated_at: SEED_TS },
  { id: 7,  title: 'Редизайн портала',                  amount: 190000,  currency: 'RUB', stage: 'won',       client_id: 7,  opened_at: '2025-11-15', expected_close: '2026-01-31', created_at: SEED_TS, updated_at: SEED_TS },
  { id: 8,  title: 'BI дашборд',                        amount: 380000,  currency: 'RUB', stage: 'lost',      client_id: 8,  opened_at: '2026-02-20', expected_close: '2026-05-30', created_at: SEED_TS, updated_at: SEED_TS },
  { id: 9,  title: 'Телемедицина платформа',            amount: 950000,  currency: 'RUB', stage: 'proposal',  client_id: 9,  opened_at: '2026-04-15', expected_close: '2026-11-30', created_at: SEED_TS, updated_at: SEED_TS },
  { id: 10, title: 'SaaS MVP',                          amount: 560000,  currency: 'RUB', stage: 'qualified', client_id: 10, opened_at: '2026-06-01', expected_close: '2026-12-31', created_at: SEED_TS, updated_at: SEED_TS },
]

let tasks: Task[] = [
  { id: 1,  title: 'Провести демо продукта',          description: 'Подготовить презентацию и сценарий', due_date: '2026-09-15', priority: 'high',   done: false, client_id: 1,    deal_id: 1,    created_at: SEED_TS, updated_at: SEED_TS },
  { id: 2,  title: 'Подготовить КП',                  description: 'Коммерческое предложение — CloudSync', due_date: '2026-09-20', priority: 'high',   done: false, client_id: 3,    deal_id: 3,    created_at: SEED_TS, updated_at: SEED_TS },
  { id: 3,  title: 'Звонок с техдиректором',          description: null,                                  due_date: '2026-09-10', priority: 'medium', done: true,  client_id: 2,    deal_id: 2,    created_at: SEED_TS, updated_at: SEED_TS },
  { id: 4,  title: 'Отправить договор на подпись',    description: 'E-commerce — RetailMax',             due_date: '2026-09-08', priority: 'high',   done: false, client_id: 5,    deal_id: 5,    created_at: SEED_TS, updated_at: SEED_TS },
  { id: 5,  title: 'Обновить записи в CRM',           description: null,                                  due_date: '2026-09-30', priority: 'low',    done: false, client_id: null, deal_id: null, created_at: SEED_TS, updated_at: SEED_TS },
  { id: 6,  title: 'Согласовать ТЗ',                  description: 'Мобильное приложение DigitalLab',    due_date: '2026-09-25', priority: 'medium', done: false, client_id: 4,    deal_id: 4,    created_at: SEED_TS, updated_at: SEED_TS },
  { id: 7,  title: 'Проверить статус платежа',        description: null,                                  due_date: '2026-08-31', priority: 'medium', done: true,  client_id: 7,    deal_id: 7,    created_at: SEED_TS, updated_at: SEED_TS },
  { id: 8,  title: 'Встреча с командой разработки',   description: 'Телемедицина — HealthBridge',        due_date: '2026-10-05', priority: 'high',   done: false, client_id: 9,    deal_id: 9,    created_at: SEED_TS, updated_at: SEED_TS },
  { id: 9,  title: 'Аудит текущих процессов',         description: 'Автоматизация склада — АгроИнвест',  due_date: '2026-09-22', priority: 'medium', done: false, client_id: 6,    deal_id: 6,    created_at: SEED_TS, updated_at: SEED_TS },
  { id: 10, title: 'Закрыть квартальный отчёт',       description: null,                                  due_date: '2026-09-28', priority: 'low',    done: false, client_id: null, deal_id: null, created_at: SEED_TS, updated_at: SEED_TS },
]

let nextClientId = 11
let nextDealId   = 11
let nextTaskId   = 11

// ── Helpers ────────────────────────────────────────────────────────────────────

type Params = Record<string, unknown>

function paginate<T>(items: T[], skip: number, limit: number): Paginated<T> {
  return { total: items.length, skip, limit, items: items.slice(skip, skip + limit) }
}

function matchQ(haystack: string, q: string): boolean {
  return haystack.toLowerCase().includes(q.toLowerCase())
}

// ── Clients ───────────────────────────────────────────────────────────────────

function listClients(p: Params): Paginated<Client> {
  const q      = String(p.q ?? '')
  const status = String(p.status ?? '')
  const skip   = Number(p.skip  ?? 0)
  const limit  = Number(p.limit ?? 20)
  let r = clients
  if (q)      r = r.filter(c => matchQ(c.name, q) || matchQ(c.email ?? '', q) || matchQ(c.company ?? '', q))
  if (status) r = r.filter(c => c.status === status)
  return paginate(r, skip, limit)
}

function createClient(d: Partial<Client>): Client {
  const c: Client = { id: nextClientId++, name: d.name ?? '', email: d.email ?? null, phone: d.phone ?? null, company: d.company ?? null, status: d.status ?? 'active', created_at: ts(), updated_at: ts() }
  clients.push(c)
  return c
}

function updateClient(id: number, d: Partial<Client>): Client {
  const i = clients.findIndex(c => c.id === id)
  if (i === -1) throw new Error(`Client ${id} not found`)
  clients[i] = { ...clients[i], ...d, id, updated_at: ts() }
  return clients[i]
}

function removeClient(id: number): void { clients = clients.filter(c => c.id !== id) }

// ── Deals ─────────────────────────────────────────────────────────────────────

function listDeals(p: Params): Paginated<Deal> {
  const q     = String(p.q ?? '')
  const stage = String(p.stage ?? '')
  const skip  = Number(p.skip  ?? 0)
  const limit = Number(p.limit ?? 20)
  let r = deals
  if (q)     r = r.filter(d => matchQ(d.title, q))
  if (stage) r = r.filter(d => d.stage === stage)
  return paginate(r, skip, limit)
}

function createDeal(d: Partial<Deal>): Deal {
  const deal: Deal = { id: nextDealId++, title: d.title ?? '', amount: d.amount ?? 0, currency: d.currency ?? 'RUB', stage: d.stage ?? 'lead', client_id: d.client_id ?? null, opened_at: d.opened_at ?? null, expected_close: d.expected_close ?? null, created_at: ts(), updated_at: ts() }
  deals.push(deal)
  return deal
}

function updateDeal(id: number, d: Partial<Deal>): Deal {
  const i = deals.findIndex(x => x.id === id)
  if (i === -1) throw new Error(`Deal ${id} not found`)
  deals[i] = { ...deals[i], ...d, id, updated_at: ts() }
  return deals[i]
}

function removeDeal(id: number): void { deals = deals.filter(d => d.id !== id) }

// ── Tasks ─────────────────────────────────────────────────────────────────────

function listTasks(p: Params): Paginated<Task> {
  const q        = String(p.q ?? '')
  const priority = String(p.priority ?? '')
  const doneRaw  = p.done
  const skip     = Number(p.skip  ?? 0)
  const limit    = Number(p.limit ?? 20)
  let r = tasks
  if (q)        r = r.filter(t => matchQ(t.title, q))
  if (priority) r = r.filter(t => t.priority === priority)
  if (doneRaw !== undefined) {
    const doneVal = doneRaw === true || doneRaw === 'true'
    r = r.filter(t => t.done === doneVal)
  }
  return paginate(r, skip, limit)
}

function createTask(d: Partial<Task>): Task {
  const t: Task = { id: nextTaskId++, title: d.title ?? '', description: d.description ?? null, due_date: d.due_date ?? null, priority: d.priority ?? 'medium', done: d.done ?? false, client_id: d.client_id ?? null, deal_id: d.deal_id ?? null, created_at: ts(), updated_at: ts() }
  tasks.push(t)
  return t
}

function updateTask(id: number, d: Partial<Task>): Task {
  const i = tasks.findIndex(t => t.id === id)
  if (i === -1) throw new Error(`Task ${id} not found`)
  tasks[i] = { ...tasks[i], ...d, id, updated_at: ts() }
  return tasks[i]
}

function removeTask(id: number): void { tasks = tasks.filter(t => t.id !== id) }

// ── URL dispatch ──────────────────────────────────────────────────────────────

export function demoGet<T>(url: string, config?: { params?: Params }): Promise<{ data: T }> {
  const p = config?.params ?? {}
  let data: unknown

  if      (url === '/clients')           data = listClients(p)
  else if (url === '/deals')             data = listDeals(p)
  else if (url === '/tasks')             data = listTasks(p)
  else if (url === '/settings/google')   data = { client_secret_path: null, parent_folder_id: null, google_token_path: null, has_valid_token_guess: false } satisfies GoogleSettings
  else if (url === '/auth/google/url')   return Promise.reject(new Error(DEMO_MSG))
  else                                   return Promise.reject(new Error(`Demo: unhandled GET ${url}`))

  return Promise.resolve({ data: data as unknown as T })
}

export function demoPost<T>(url: string, body?: unknown): Promise<{ data: T }> {
  let data: unknown

  if      (url === '/clients')                    data = createClient(body as Partial<Client>)
  else if (url === '/deals')                      data = createDeal(body as Partial<Deal>)
  else if (url === '/tasks')                      data = createTask(body as Partial<Task>)
  else if (url.startsWith('/reports/export/'))    return Promise.reject(new Error(DEMO_MSG))
  else                                            return Promise.reject(new Error(`Demo: unhandled POST ${url}`))

  return Promise.resolve({ data: data as unknown as T })
}

export function demoPatch<T>(url: string, body?: unknown): Promise<{ data: T }> {
  const m = url.match(/^\/(\w+)\/(\d+)$/)
  if (!m) return Promise.reject(new Error(`Demo: unhandled PATCH ${url}`))
  const id = Number(m[2])
  let data: unknown

  if      (m[1] === 'clients') data = updateClient(id, body as Partial<Client>)
  else if (m[1] === 'deals')   data = updateDeal(id, body as Partial<Deal>)
  else if (m[1] === 'tasks')   data = updateTask(id, body as Partial<Task>)
  else return Promise.reject(new Error(`Demo: unhandled PATCH ${url}`))

  return Promise.resolve({ data: data as unknown as T })
}

export function demoPut<T>(url: string): Promise<{ data: T }> {
  if (url === '/settings/google') return Promise.resolve({ data: undefined as unknown as T })
  return Promise.reject(new Error(`Demo: unhandled PUT ${url}`))
}

export function demoDelete<T>(url: string): Promise<{ data: T }> {
  const m = url.match(/^\/(\w+)\/(\d+)$/)
  if (!m) return Promise.reject(new Error(`Demo: unhandled DELETE ${url}`))
  const id = Number(m[2])

  if      (m[1] === 'clients') removeClient(id)
  else if (m[1] === 'deals')   removeDeal(id)
  else if (m[1] === 'tasks')   removeTask(id)
  else return Promise.reject(new Error(`Demo: unhandled DELETE ${url}`))

  return Promise.resolve({ data: undefined as unknown as T })
}
