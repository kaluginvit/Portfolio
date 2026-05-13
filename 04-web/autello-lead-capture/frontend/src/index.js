import './styles.css';

// ── Анимация золотых кружков ──────────────────────────────────────────────
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const circles = [];

function resize() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
}

function randomCircle() {
  return {
    x: Math.random() * canvas.width,
    y: Math.random() * canvas.height,
    r: 20 + Math.random() * 60,
    dx: (Math.random() - 0.5) * 0.5,
    dy: (Math.random() - 0.5) * 0.5,
    alpha: 0.04 + Math.random() * 0.08,
  };
}

resize();
window.addEventListener('resize', resize);
for (let i = 0; i < 18; i++) circles.push(randomCircle());

function animateCircles() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  circles.forEach(c => {
    ctx.beginPath();
    ctx.arc(c.x, c.y, c.r, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(180, 150, 80, ${c.alpha})`;
    ctx.fill();
    c.x += c.dx;
    c.y += c.dy;
    if (c.x < -c.r || c.x > canvas.width + c.r) c.dx *= -1;
    if (c.y < -c.r || c.y > canvas.height + c.r) c.dy *= -1;
  });
  requestAnimationFrame(animateCircles);
}
animateCircles();

// ── Поведенческие метрики ────────────────────────────────────────────────
const metrics = {
  startTime: Date.now(),
  buttonsClicked: [],
  hoverAreas: {},
  returnCount: parseInt(sessionStorage.getItem('returnCount') || '0'),
};

sessionStorage.setItem('returnCount', metrics.returnCount + 1);

document.addEventListener('click', e => {
  const tag = e.target.tagName + (e.target.name ? `[${e.target.name}]` : '');
  metrics.buttonsClicked.push(tag);
});

document.addEventListener('mouseover', e => {
  const name = e.target.name || e.target.id;
  if (name) metrics.hoverAreas[name] = (metrics.hoverAreas[name] || 0) + 1;
});

// ── Загрузка услуг ───────────────────────────────────────────────────────
const serviceSelect = document.getElementById('serviceSelect');

async function loadServices() {
  try {
    const res = await fetch('/api/admin-settings/');
    if (!res.ok) throw new Error('Ошибка загрузки');
    const data = await res.json();
    serviceSelect.innerHTML = '<option value="">Выберите услугу</option>';
    data.forEach(item => {
      const opt = document.createElement('option');
      opt.value = item.services;
      opt.textContent = `${item.services} (${item.budget_range})`;
      serviceSelect.appendChild(opt);
    });
  } catch {
    serviceSelect.innerHTML = '<option value="">Не удалось загрузить услуги</option>';
  }
}

loadServices();

// ── Слайдер бюджета ──────────────────────────────────────────────────────
const budgetSlider = document.getElementById('budgetSlider');
const budgetValue = document.getElementById('budgetValue');

function formatBudget(val) {
  return parseInt(val).toLocaleString('ru-RU') + ' ₽';
}

budgetSlider.addEventListener('input', () => {
  budgetValue.textContent = formatBudget(budgetSlider.value);
  const pct = ((budgetSlider.value - budgetSlider.min) / (budgetSlider.max - budgetSlider.min)) * 100;
  budgetSlider.style.background =
    `linear-gradient(to right, #6366f1 0%, #6366f1 ${pct}%, #e5e7eb ${pct}%)`;
});

// ── Отправка формы ───────────────────────────────────────────────────────
const form = document.getElementById('applicationForm');
const submitBtn = document.getElementById('submitBtn');
const formMessage = document.getElementById('formMessage');

function showMessage(text, type) {
  formMessage.textContent = text;
  formMessage.className = `form-message ${type}`;
}

form.addEventListener('submit', async e => {
  e.preventDefault();

  const fd = new FormData(form);
  const payload = {};
  fd.forEach((val, key) => { if (val) payload[key] = val; });

  if (!payload.first_name || !payload.last_name) {
    showMessage('Пожалуйста, заполните имя и фамилию.', 'error');
    return;
  }
  if (!payload.interested_service) {
    showMessage('Пожалуйста, выберите услугу.', 'error');
    return;
  }

  submitBtn.disabled = true;
  submitBtn.textContent = 'Отправляем...';

  try {
    const res = await fetch('/api/applications/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!res.ok) throw new Error(`Ошибка ${res.status}`);
    const application = await res.json();

    // Отправляем метрики поведения
    await fetch('/api/behavior-metrics/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        id: application.id,
        time_on_page: Math.round((Date.now() - metrics.startTime) / 1000),
        buttons_clicked: JSON.stringify(metrics.buttonsClicked),
        cursor_hover_areas: JSON.stringify(metrics.hoverAreas),
        return_count: metrics.returnCount,
      }),
    });

    showMessage('Заявка отправлена! Мы свяжемся с вами в ближайшее время.', 'success');
    form.reset();
    budgetValue.textContent = formatBudget(500000);
    loadServices();
  } catch (err) {
    showMessage(`Ошибка отправки: ${err.message}`, 'error');
    submitBtn.disabled = false;
    submitBtn.textContent = 'Отправить заявку';
  }
});
