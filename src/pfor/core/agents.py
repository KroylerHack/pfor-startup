"""
PFOR Ollama-powered strategy generator.
Generates a deep Markdown report via local Ollama API and role-based strategy prompts.
"""
import logging

import httpx

from pfor.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

OLLAMA_SYSTEM_PROMPT = """Ты — мультиагентная платформа PFOR.
Твоя задача — выступить как консилиум четырех ролей и создать глубокую, структурированную стратегию.

Роли:
- Director: исследует проблему и формулирует стратегические цели.
- Marketer: анализирует рынок, позиционирование и каналы продаж.
- Financier: рассчитывает бюджет, KPI, ROI и финансовые риски.
- Editor: сводит результат в единый понятный отчёт.

Отвечай только на русском, узбекском или английском языке, в зависимости от языка запроса.

Выдавай ответ в формате Markdown, минимум 5 разделов:
1. Анализ проблемы
2. Цели и приоритеты
3. Пошаговый план действий
4. Роли, ресурсы и распределение ответственности
5. Риски, KPI и критерии успеха
6. Рекомендации и следующий этап

Каждая роль должна быть отражена в отчёте и понятно обозначена.
"""


class MultiAgentPipeline:
    """Compatibility wrapper for the old naming used by the project."""

    def __init__(self, base_url: str | None = None, model: str | None = None) -> None:
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL

    async def run(self, prompt_text: str, language: str = "ru") -> str:
        """Generate the final Markdown strategy report via Ollama Chat API."""
        prompt_message = (
            "Язык ответа: {}\n\n".format(language)
            + "Пожалуйста, отвечай в формате Markdown и разбей отчёт на роли Director, Marketer, Financier и Editor.\n\n"
            + "Бизнес-проблема:\n"
            + prompt_text
        )

        payload = {
            "model": self.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": OLLAMA_SYSTEM_PROMPT},
                {"role": "user", "content": prompt_message},
            ],
            "options": {"temperature": 0.25, "num_predict": 3000},
        }

        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(f"{self.base_url}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            content = data.get("message", {}).get("content")
            if not content:
                raise ValueError("Ollama response did not contain message content.")
            return content.strip()
