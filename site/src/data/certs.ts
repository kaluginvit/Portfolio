import { RAW_MAIN } from './links';

const p = (name: string) =>
  `${RAW_MAIN}/%D0%A1%D0%B5%D1%80%D1%82%D0%B8%D1%84%D0%B8%D0%BA%D0%B0%D1%82%D1%8B/${encodeURIComponent(name)}`;

/** Certificate thumbnails from raw.githubusercontent.com, lazy-loaded on the page. */
export const certificates: { src: string; label: string }[] = [
  { src: p('AI_в_таблицах_рус.png'), label: 'ИИ в таблицах' },
  { src: p('Аналитик_данных_рус.png'), label: 'Аналитик данных' },
  { src: p('Автоматизатор_бизнес-процессов_рус.png'), label: 'Автоматизация процессов' },
  { src: p('Автоматизация_n8n_рус.png'), label: 'Автоматизация на n8n' },
  { src: p('Vibe-Coding_и_агенты_рус.png'), label: 'Vibe-Coding и агенты' },
  { src: p('Perplexity_рус.png'), label: 'Perplexity' },
  { src: p('ИИ-презентации_рус.png'), label: 'ИИ-презентации' },
  { src: p('Нейросети_для_финансистов_рус.png'), label: 'Нейросети для финансистов' },
  { src: p('Профессия_Вайбкодер_рус.png'), label: 'Профессия Вайбкодер' },
  { src: p('Лендинг.png'), label: 'Лендинг' },
];
