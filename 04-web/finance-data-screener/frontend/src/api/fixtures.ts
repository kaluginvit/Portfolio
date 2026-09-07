import type { Dataset, DataRecord, AuditRun, QueryResponse, PlanResponse } from "../types";

export const DATASETS: Dataset[] = [
  {
    id: "demo-cbr",
    name: "Курсы ЦБ РФ",
    query: "Курсы доллара, евро и других валют по данным ЦБ РФ",
    source: "cbr",
    created_at: "2026-09-07T09:00:00Z",
    records_count: 10,
  },
  {
    id: "demo-moex",
    name: "Акции MOEX — Топ-10",
    query: "Топ акций Московской биржи по объёму торгов",
    source: "moex",
    created_at: "2026-09-07T09:05:00Z",
    records_count: 10,
  },
];

const CBR_RAW = [
  { CharCode: "USD", Nominal: 1, Name: "Доллар США",       Value: 89.50 },
  { CharCode: "EUR", Nominal: 1, Name: "Евро",              Value: 97.83 },
  { CharCode: "CNY", Nominal: 10,Name: "Китайских юаней",   Value: 123.45 },
  { CharCode: "GBP", Nominal: 1, Name: "Фунт стерлингов",   Value: 114.20 },
  { CharCode: "JPY", Nominal: 100,Name:"Японских иен",      Value: 59.80 },
  { CharCode: "CHF", Nominal: 1, Name: "Швейцарский франк", Value: 102.10 },
  { CharCode: "HKD", Nominal: 10,Name: "Гонконгских долл.", Value: 114.60 },
  { CharCode: "KZT", Nominal: 100,Name:"Казахстанских тенге",Value: 18.90 },
  { CharCode: "BYR", Nominal: 1, Name: "Белорусский рубль", Value: 27.40 },
  { CharCode: "TRY", Nominal: 10,Name: "Турецких лир",      Value: 26.30 },
];

const MOEX_RAW = [
  { SECID: "SBER",  SHORTNAME: "Сбербанк",    LAST: 255.50, VOLTODAY: 45678901,  VALTODAY: 11665417655 },
  { SECID: "GAZP",  SHORTNAME: "Газпром",      LAST: 158.20, VOLTODAY: 23456789,  VALTODAY:  3712364218 },
  { SECID: "LKOH",  SHORTNAME: "Лукойл",       LAST: 7340.00,VOLTODAY: 1234567,   VALTODAY:  9059623800 },
  { SECID: "YNDX",  SHORTNAME: "Яндекс",       LAST: 4215.00,VOLTODAY: 3456789,   VALTODAY: 14572807635 },
  { SECID: "ROSN",  SHORTNAME: "Роснефть",     LAST: 567.80, VOLTODAY: 8765432,   VALTODAY:  4974571250 },
  { SECID: "NVTK",  SHORTNAME: "Новатэк",      LAST: 1123.40,VOLTODAY: 2345678,   VALTODAY:  2634874332 },
  { SECID: "GMKN",  SHORTNAME: "Норникель",    LAST: 15780.00,VOLTODAY: 456789,   VALTODAY:  7207780020 },
  { SECID: "POLY",  SHORTNAME: "Полюс",        LAST: 13250.00,VOLTODAY: 234567,   VALTODAY:  3108012150 },
  { SECID: "MAGN",  SHORTNAME: "ММК",          LAST: 42.30,  VOLTODAY: 56789012,  VALTODAY:  2401937208 },
  { SECID: "CHMF",  SHORTNAME: "Северсталь",   LAST: 1580.00,VOLTODAY: 1567890,   VALTODAY:  2477326200 },
];

function makeRecords(datasetId: string, rows: Record<string, unknown>[]): DataRecord[] {
  return rows.map((data, i) => ({
    id: `${datasetId}-r${i}`,
    source: datasetId === "demo-cbr" ? "cbr" : "moex",
    collected_at: "2026-09-07T09:00:00Z",
    data,
  }));
}

export const RECORDS: Record<string, DataRecord[]> = {
  "demo-cbr": makeRecords("demo-cbr", CBR_RAW),
  "demo-moex": makeRecords("demo-moex", MOEX_RAW),
};

export const AUDIT: AuditRun[] = [
  { id: "a1", endpoint: "/datasets",        method: "GET",  status_code: 200, duration_ms: 12,  created_at: "2026-09-07T09:00:01Z", request_body: null, response_summary: "2 datasets", error: null },
  { id: "a2", endpoint: "/datasets/demo-cbr/records", method: "GET", status_code: 200, duration_ms: 8, created_at: "2026-09-07T09:00:02Z", request_body: null, response_summary: "10 records (cbr)", error: null },
  { id: "a3", endpoint: "/datasets/demo-moex/records",method: "GET", status_code: 200, duration_ms: 9, created_at: "2026-09-07T09:00:03Z", request_body: null, response_summary: "10 records (moex)", error: null },
  { id: "a4", endpoint: "/ai/query",        method: "POST", status_code: 200, duration_ms: 310, created_at: "2026-09-07T09:01:00Z", request_body: { question: "Какой курс доллара?" }, response_summary: "89.50 руб.", error: null },
];

const QUERY_MAP: Array<{ keywords: string[]; datasetId: string; answer: string; records_used: number }> = [
  {
    keywords: ["доллар", "usd", "dollar"],
    datasetId: "demo-cbr",
    answer: "По данным ЦБ РФ, курс доллара США (USD) составляет 89.50 руб. Евро — 97.83 руб. Курсы зафиксированы на 07.09.2026.",
    records_used: 10,
  },
  {
    keywords: ["евро", "eur", "euro"],
    datasetId: "demo-cbr",
    answer: "По данным ЦБ РФ, курс евро (EUR) составляет 97.83 руб. Для сравнения, доллар США — 89.50 руб.",
    records_used: 10,
  },
  {
    keywords: ["сбер", "sber", "сбербанк"],
    datasetId: "demo-moex",
    answer: "Акции Сбербанка (SBER) торгуются по 255.50 руб. Объём торгов за день — 45.7 млн акций на сумму около 11.7 млрд руб.",
    records_used: 10,
  },
  {
    keywords: ["яндекс", "yndx", "yandex"],
    datasetId: "demo-moex",
    answer: "Акции Яндекса (YNDX) торгуются по 4215 руб. Объём торгов — 3.5 млн акций. Наибольший оборот среди эмитентов выборки.",
    records_used: 10,
  },
  {
    keywords: ["топ", "лучш", "рост", "объём", "объем", "volume"],
    datasetId: "demo-moex",
    answer: "Топ по объёму торгов: Сбербанк (SBER, 45.7 млн акций), ММК (MAGN, 56.8 млн), Газпром (GAZP, 23.5 млн). По обороту лидирует Яндекс — 14.6 млрд руб.",
    records_used: 10,
  },
];

export function resolveQuery(datasetId: string, question: string): QueryResponse {
  const q = question.toLowerCase();
  const match = QUERY_MAP.find(
    (m) => m.datasetId === datasetId && m.keywords.some((k) => q.includes(k))
  );
  if (match) {
    return { answer: match.answer, records_used: match.records_used, needs_review: false, review_reason: null };
  }
  const ds = DATASETS.find((d) => d.id === datasetId);
  return {
    answer: `По набору данных «${ds?.name ?? datasetId}» (${ds?.records_count ?? 0} записей): данные загружены в Demo Mode. Попробуйте вопросы из предложенных примеров.`,
    records_used: ds?.records_count ?? 0,
    needs_review: true,
    review_reason: "Demo Mode — ответ сформирован без LLM. Задайте конкретный вопрос о валютах или акциях.",
  };
}

export const DEMO_PLAN_RESPONSE: PlanResponse = {
  agent_run_id: "demo-agent-run",
  plan: {
    source: "cbr",
    api_url: "https://www.cbr.ru/scripts/XML_daily.asp",
    fields_to_keep: ["CharCode", "Nominal", "Name", "Value"],
    filters: {},
    confidence: "high",
    needs_review: false,
    plan_steps: [
      "Запросить XML-фид ЦБ РФ",
      "Извлечь курсы валют",
      "Сохранить в датасет",
    ],
  },
};
