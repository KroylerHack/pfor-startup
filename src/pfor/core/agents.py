"""
PFOR Ollama-powered strategy generator.
Generates a single deep Markdown report via the local Ollama API.
"""
import logging
from datetime import datetime

import httpx

from pfor.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

OLLAMA_SYSTEM_PROMPT = """Ты — Главный бизнес-стратег и аналитик PFOR.
Твоя задача — помогать клиентам превращать бизнес-проблему в глубокую, структурированную стратегию и план действий.

Отвечай только на русском, узбекском или английском языке в зависимости от запроса пользователя.

Формат ответа — Markdown, 4–5 страниц / разделов. Используй ясный бизнес-словарь, практические рекомендации и таблицы там, где это уместно.

Структура ответа:
# PFOR Strategic Report
**Дата:** ...
**Проблема:** ...

## 1. Анализ проблемы
## 2. Цели и приоритеты
## 3. Пошаговый план действий
## 4. Роли, ресурсы и распределение ответственности
## 5. Риски, KPI и критерии успеха
## 6. Рекомендации и следующий этап

Учитывай: бизнес-процессы, роли, сроки, риски, KPI, зависимости, приоритеты, эксплуатационные риски, ROI и минимальный viable plan.
"""


class MultiAgentPipeline:
    """Compatibility wrapper for the old naming used by the project."""

    def __init__(self, base_url: str | None = None, model: str | None = None) -> None:
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self._client = httpx.AsyncClient(timeout=180.0)

    async def run(self, prompt_text: str, language: str = "ru") -> str:
        """Generate the final Markdown strategy report via Ollama Chat API."""
        payload = {
            "model": self.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": OLLAMA_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Язык ответа: {language}\n\n"
                        f"Бизнес-проблема:\n{prompt_text}"
                    ),
                },
            ],
            "options": {"temperature": 0.3, "num_predict": 3000},
        }

        try:
            response = await self._client.post(f"{self.base_url}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            content = data.get("message", {}).get("content")
            if not content:
                raise ValueError("Ollama response did not contain message content.")
            return content.strip()
        except Exception as exc:
            logger.exception("Ollama generation failed")
            return self._fallback_report(prompt_text, language, exc)

    def _fallback_report(self, prompt_text: str, language: str, exc: Exception) -> str:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        return f"""# PFOR Strategic Report
**Дата:** {today}
**Проблема:** {prompt_text[:200]}{'...' if len(prompt_text) > 200 else ''}

## 1. Анализ проблемы
Входная задача требует системного подхода и структурирования усилий по ролям, приоритетам и KPI.

## 2. Цели и приоритеты
- Определить корневую причину проблемы.
- Выделить 2–3 ключевых приоритета на ближайший квартал.
- Согласовать роли, владельцев и ресурсное обеспечение.

## 3. Пошаговый план действий
1. Сформировать рабочую группу и владельца инициативы.
2. Провести диагностику текущей ситуации и точек потерь.
3. Определить минимальный набор изменений и приоритеты.
4. Провести пилот и измерять KPI.
5. Масштабировать успешный результат.

## 4. Роли, ресурсы и распределение ответственности
| Роль | Ответственность | Объём участия |
|------|-----------------|---------------|
| Руководитель | Оценка приоритетов | Высокий |
| Бизнес-аналитик | Диагностика и карта процессов | Высокий |
| Менеджер проекта | План-график и трекинг | Средний |
| Финансист | Бюджет и контроль ROI | Средний |

## 5. Риски, KPI и критерии успеха
- Риск: отсутствие единого владельца.
- Риск: перегрузка команды изменениями.
- KPI: снижение операционных потерь, рост конверсии, улучшение сроков.

## 6. Рекомендации и следующий этап
Дальше важно зафиксировать 1–2 успешных пилота, измерить эффект и затем масштабировать результат в единый бизнес-процесс.

> Временный fallback-отчёт создан, потому что локальный Ollama был недоступен. Подключите сервис и повторите генерацию.

Ошибка: {exc}
"""
