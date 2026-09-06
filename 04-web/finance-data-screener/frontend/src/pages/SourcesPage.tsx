const GROUPS = [
  {
    title: "Акции (MOEX)",
    color: "blue",
    items: [
      "Все акции с объёмом торгов > 1 млрд рублей",
      "Акции, выросшие сегодня (CHANGE > 0)",
      "Топ акций по объёму торгов",
      "Акции дороже 1000 рублей",
      "Все акции первого эшелона TQBR",
    ],
  },
  {
    title: "История цен (MOEX)",
    color: "indigo",
    items: [
      "История цен Сбербанка за последний месяц",
      "График акций Лукойл за 3 месяца",
      "Дневные свечи Газпрома с начала года",
      "Цены Яндекса за последние 2 недели",
      "Динамика акций Норникеля за квартал",
    ],
  },
  {
    title: "Облигации (MOEX)",
    color: "violet",
    items: [
      "Список государственных облигаций ОФЗ",
      "Облигации с доходностью > 10%",
      "Все ОФЗ на сегодня",
    ],
  },
  {
    title: "Индексы (MOEX)",
    color: "purple",
    items: [
      "Значение индекса IMOEX сегодня",
      "Все индексы Московской биржи",
      "Индекс РТС (RTSI)",
    ],
  },
  {
    title: "Дивиденды (MOEX)",
    color: "pink",
    items: [
      "Дивиденды Газпрома за все годы",
      "История выплат Сбербанка",
      "Дивиденды Лукойла",
      "Дивидендная история Норникеля",
    ],
  },
  {
    title: "Курсы валют (ЦБ РФ)",
    color: "green",
    items: [
      "Курс доллара и евро на сегодня",
      "Курс юаня",
      "Все курсы валют ЦБ РФ",
      "Курс фунта стерлингов",
      "Курс японской иены",
    ],
  },
  {
    title: "Новости (ТАСС)",
    color: "orange",
    items: [
      "Последние финансовые новости",
      "Новости рынка за сегодня",
      "Свежие новости экономики",
    ],
  },
];

const COLOR_MAP: Record<string, { dot: string; badge: string }> = {
  blue:   { dot: "bg-blue-400",   badge: "bg-blue-950/60 text-blue-300 border border-blue-800/40" },
  indigo: { dot: "bg-indigo-400", badge: "bg-indigo-950/60 text-indigo-300 border border-indigo-800/40" },
  violet: { dot: "bg-violet-400", badge: "bg-violet-950/60 text-violet-300 border border-violet-800/40" },
  purple: { dot: "bg-purple-400", badge: "bg-purple-950/60 text-purple-300 border border-purple-800/40" },
  pink:   { dot: "bg-pink-400",   badge: "bg-pink-950/60 text-pink-300 border border-pink-800/40" },
  green:  { dot: "bg-t-accent",   badge: "bg-emerald-950/60 text-t-accent border border-t-border" },
  orange: { dot: "bg-orange-400", badge: "bg-orange-950/60 text-orange-300 border border-orange-800/40" },
};

export default function SourcesPage() {
  return (
    <div>
      <div className="mb-6">
        <h1 className="font-mono text-t-text text-lg font-semibold">// Что можно спросить</h1>
        <p className="font-mono text-t-muted text-sm mt-1">
          Примеры запросов на русском языке — скопируйте или напишите похожий
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {GROUPS.map((group) => {
          const c = COLOR_MAP[group.color];
          return (
            <div key={group.title} className="bg-t-card border border-t-border rounded-lg p-4">
              <div className="flex items-center gap-2 mb-3">
                <span className={`w-2 h-2 rounded-full ${c.dot}`} />
                <span className={`font-mono text-xs px-2 py-0.5 rounded ${c.badge}`}>
                  {group.title}
                </span>
              </div>
              <ul className="space-y-2">
                {group.items.map((item) => (
                  <li key={item} className="flex items-start gap-2 font-mono text-sm text-t-muted">
                    <span className="text-t-accent mt-0.5 shrink-0">›</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          );
        })}
      </div>
    </div>
  );
}
