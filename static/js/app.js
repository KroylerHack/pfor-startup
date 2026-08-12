/**
 * PFOR Platform — Main Application Module
 * Handles strategy generation form, agent progress animation,
 * report rendering, and copy/print actions.
 */

const API_BASE = window.location.origin || 'http://localhost:8000';

function getCurrentLanguage() {
  return document.body.dataset.lang || localStorage.getItem('pfor-language') || 'ru';
}

const AGENTS = [
  { id: 'agent-director', name: 'Director', icon: '🎯', label: 'Strategic Analysis' },
  { id: 'agent-marketer', name: 'Marketer', icon: '📈', label: 'Market Planning' },
  { id: 'agent-financier', name: 'Financier', icon: '💰', label: 'Financial Modeling' },
  { id: 'agent-editor', name: 'Editor', icon: '✍️', label: 'Report Synthesis' },
];

const AGENT_DURATIONS = [8000, 8000, 8000, 6000];

const TRANSLATIONS = {
  ru: {
    'nav.login': 'Войти',
    'nav.register': 'Регистрация',
    'nav.logout': 'Выйти',
    'hero.badge': 'Мультиагентный ИИ · Gemini API',
    'hero.title': 'Автоматизированная генерация бизнес-стратегий',
    'hero.subtitle': 'Введите вашу проблему простым языком — мультиагентная система сформирует детальный план за 5 минут.',
    'input.label': 'Ваша бизнес-задача',
    'input.placeholder': 'Например: Наш стартап делает B2B SaaS для автоматизации бухгалтерии малого бизнеса. Мы не можем масштабировать продажи — CAC слишком высок, конверсия из лида в клиента менее 5%. Как нам это исправить?',
    'button.generate': 'Сформировать стратегию',
    'report.heading': 'Стратегический отчёт',
    'report.ready': 'Готово',
    'report.copy': '📋 Копировать',
    'report.print': '🖨️ Печать',
    'report.new': '+ Новый отчёт',
    'feature.one.title': 'Стратегический анализ',
    'feature.one.desc': 'Agent Director формулирует цели и концепцию решения на основе вашей задачи.',
    'feature.two.title': 'GTM и маркетинг',
    'feature.two.desc': 'Agent Marketer строит воронки, определяет каналы и позиционирование.',
    'feature.three.title': 'Финансовое моделирование',
    'feature.three.desc': 'Agent Financier считает юнит-экономику, бюджет и сценарии роста.',
    'char.count': '{count} characters',
  },
  en: {
    'nav.login': 'Log in',
    'nav.register': 'Register',
    'nav.logout': 'Log out',
    'hero.badge': 'Multi-agent AI · Gemini API',
    'hero.title': 'Automated business strategy generation',
    'hero.subtitle': 'Describe your challenge in plain language — the multi-agent system will build a detailed plan in minutes.',
    'input.label': 'Your business challenge',
    'input.placeholder': 'For example: Our startup builds B2B SaaS for automating accounting for small businesses. We cannot scale sales because CAC is too high and conversion from lead to client is below 5%. How can we fix this?',
    'button.generate': 'Generate strategy',
    'report.heading': 'Strategic report',
    'report.ready': 'Ready',
    'report.copy': '📋 Copy',
    'report.print': '🖨️ Print',
    'report.new': '+ New report',
    'feature.one.title': 'Strategic analysis',
    'feature.one.desc': 'The Director agent defines goals and solution direction based on your challenge.',
    'feature.two.title': 'GTM & marketing',
    'feature.two.desc': 'The Marketer agent maps funnels, channels, and positioning.',
    'feature.three.title': 'Financial modeling',
    'feature.three.desc': 'The Financier agent calculates unit economics, budget, and growth scenarios.',
    'char.count': '{count} characters',
  }
};

function applyLanguage(lang = 'ru') {
  const safeLang = TRANSLATIONS[lang] ? lang : 'ru';
  const dict = TRANSLATIONS[safeLang] || TRANSLATIONS.ru;
  localStorage.setItem('pfor-language', safeLang);
  document.documentElement.lang = safeLang;
  document.body.dataset.lang = safeLang;

  document.querySelectorAll('[data-i18n]').forEach((node) => {
    const key = node.dataset.i18n;
    if (dict[key]) node.textContent = dict[key];
  });

  document.querySelectorAll('[data-i18n-placeholder]').forEach((node) => {
    const key = node.dataset.i18nPlaceholder;
    if (dict[key]) node.placeholder = dict[key];
  });

  const langButtons = document.querySelectorAll('.lang-btn');
  langButtons.forEach((btn) => {
    btn.classList.toggle('active', btn.dataset.lang === safeLang);
  });

  if (problemTextarea && charCounter) {
    const len = problemTextarea.value.length;
    charCounter.textContent = dict['char.count'].replace('{count}', len);
  }
}

function initTheme() {
  const savedTheme = localStorage.getItem('pfor-theme') || 'light';
  document.body.dataset.theme = savedTheme;
  const button = document.getElementById('theme-toggle-btn');
  if (button) {
    button.textContent = savedTheme === 'dark' ? '☀️' : '🌙';
  }
}

function toggleTheme() {
  const current = document.body.dataset.theme === 'dark' ? 'dark' : 'light';
  const next = current === 'dark' ? 'light' : 'dark';
  document.body.dataset.theme = next;
  localStorage.setItem('pfor-theme', next);
  const button = document.getElementById('theme-toggle-btn');
  if (button) button.textContent = next === 'dark' ? '☀️' : '🌙';
}

let problemTextarea, charCounter, generateBtn;
let agentsProgress, progressBarFill;
let reportSection, reportContent;

function updateCharCounter() {
  if (!problemTextarea || !charCounter) return;
  const len = problemTextarea.value.length;
  charCounter.textContent = `${len} characters`;
}

function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  container.appendChild(toast);

  setTimeout(() => toast.remove(), 3200);
}

window.showToast = showToast;

let agentTimers = [];

function resetAgentChips() {
  AGENTS.forEach(agent => {
    const chip = document.getElementById(agent.id);
    if (!chip) return;
    chip.classList.remove('active', 'done');
    chip.querySelector('.agent-status').textContent = 'Waiting...';
  });

  if (progressBarFill) progressBarFill.style.width = '0%';
}

function animateAgents() {
  return new Promise((resolve) => {
    agentTimers.forEach(clearTimeout);
    agentTimers = [];
    resetAgentChips();

    let elapsed = 0;
    const totalDuration = AGENT_DURATIONS.reduce((a, b) => a + b, 0);

    AGENTS.forEach((agent, index) => {
      const duration = AGENT_DURATIONS[index];

      const startTimer = setTimeout(() => {
        const chip = document.getElementById(agent.id);
        if (!chip) return;
        chip.classList.add('active');
        chip.querySelector('.agent-status').textContent = 'Analyzing...';

        const progress = ((elapsed + duration * 0.5) / totalDuration) * 100;
        if (progressBarFill) progressBarFill.style.width = `${progress}%`;
      }, elapsed);

      agentTimers.push(startTimer);

      const endTimer = setTimeout(() => {
        const chip = document.getElementById(agent.id);
        if (!chip) return;
        chip.classList.remove('active');
        chip.classList.add('done');
        chip.querySelector('.agent-status').textContent = 'Complete ✓';

        if (index === AGENTS.length - 1) {
          if (progressBarFill) progressBarFill.style.width = '100%';
          setTimeout(resolve, 400);
        }
      }, elapsed + duration - 400);

      agentTimers.push(endTimer);
      elapsed += duration;
    });
  });
}

function stopAgentAnimation() {
  agentTimers.forEach(clearTimeout);
  agentTimers = [];
}

function renderMarkdown(md) {
  let html = md
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  html = html
    .replace(/^### (.*)$/gm, '<h3>$1</h3>')
    .replace(/^## (.*)$/gm, '<h2>$1</h2>')
    .replace(/^# (.*)$/gm, '<h1>$1</h1>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>');

  return `<div class="markdown-body"><p>${html}</p></div>`;
}

function copyReport() {
  if (!reportContent) return;
  const text = reportContent.innerText || reportContent.textContent || '';
  if (!navigator.clipboard) {
    alert('Clipboard is not available.');
    return;
  }
  navigator.clipboard.writeText(text).then(() => {
    showToast('Отчёт скопирован в буфер обмена.', 'success');
  }, () => {
    showToast('Не удалось скопировать отчёт.', 'error');
  });
}

function resetReportView() {
  if (!reportSection || !reportContent) return;
  reportSection.classList.remove('visible');
  reportContent.innerHTML = '';
  if (problemTextarea) problemTextarea.focus();
}

async function generateStrategy() {
  const prompt = problemTextarea.value.trim();
  if (!prompt || prompt.length < 20) {
    showToast('Введите более развернутую задачу для генерации стратегии.', 'error');
    return;
  }

  const token = localStorage.getItem('pfor_access_token');
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers.Authorization = `Bearer ${token}`;

  await animateAgents();

  try {
    const response = await fetch(`${API_BASE}/api/v1/generate-strategy`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ prompt_text: prompt, language: getCurrentLanguage() }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Strategy generation failed.');
    }

    if (reportContent) {
      const markdown = data.result_markdown || '## Отчёт\n\nСодержимое недоступно.';
      reportContent.innerHTML = renderMarkdown(markdown);
      reportSection.classList.add('visible');
      showToast('Отчёт успешно сформирован.', 'success');
    }
  } catch (error) {
    showToast(error.message || 'Не удалось сформировать отчёт.', 'error');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  problemTextarea = document.getElementById('problem-textarea');
  charCounter = document.getElementById('char-counter');
  generateBtn = document.getElementById('generate-btn');
  agentsProgress = document.getElementById('agents-progress');
  progressBarFill = document.getElementById('progress-bar-fill');
  reportSection = document.getElementById('report-section');
  reportContent = document.getElementById('report-content');

  if (problemTextarea) {
    problemTextarea.addEventListener('input', updateCharCounter);
    updateCharCounter();
  }

  if (generateBtn) {
    generateBtn.addEventListener('click', generateStrategy);
  }

  document.querySelectorAll('.lang-btn').forEach((button) => {
    button.addEventListener('click', () => {
      applyLanguage(button.dataset.lang || 'ru');
    });
  });

  document.getElementById('theme-toggle-btn')?.addEventListener('click', toggleTheme);
  document.getElementById('copy-report-btn')?.addEventListener('click', copyReport);
  document.getElementById('print-report-btn')?.addEventListener('click', () => window.print());
  document.getElementById('new-report-btn')?.addEventListener('click', resetReportView);

  initTheme();
  applyLanguage(getCurrentLanguage());
});
