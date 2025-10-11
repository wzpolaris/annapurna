from __future__ import annotations

import asyncio
import logging
import os
from typing import List

import httpx
from dotenv import load_dotenv
from openai import OpenAI

from .schemas import ChatMessage

load_dotenv()

logger = logging.getLogger('northfield.backend.openai')

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')

_http_client: httpx.Client | None = None
_client: OpenAI | None = None


def _build_client() -> OpenAI | None:
    global _http_client

    if not OPENAI_API_KEY:
        logger.error('OPENAI_API_KEY is not set')
        return None

    if _http_client is None:
        logger.info('Initialising shared HTTP client for OpenAI')
        _http_client = httpx.Client(
            timeout=30,
            follow_redirects=True,
            transport=httpx.HTTPTransport(retries=3)
        )

    return OpenAI(api_key=OPENAI_API_KEY, http_client=_http_client)


class OpenAIConfigurationError(RuntimeError):
    """Raised when OpenAI credentials are missing."""


async def generate_chat_response(
    prompt: str,
    space_title: str,
    history: List[ChatMessage] | None = None
) -> str:
    global _client

    if _client is None:
        logger.info('Creating OpenAI client for the first time')
        _client = _build_client()

    if _client is None:
        raise OpenAIConfigurationError(
            'OPENAI_API_KEY is not configured; unable to request completions.'
        )

    messages = [
        {
            'role': 'system',
            'content': (
                'You are Atlas, an analytical assistant for investment research. '
                f'The current workspace is "{space_title}". Keep answers concise, '
                'actionable, and professional.'
            )
        }
    ]

    if history:
        logger.info('Including %d history messages for context', len(history))
        messages.extend(message.model_dump() for message in history)

    messages.append({'role': 'user', 'content': prompt})

    logger.info('Requesting completion from OpenAI model %s', OPENAI_MODEL)
    response = await asyncio.to_thread(
        _client.chat.completions.create,
        model=OPENAI_MODEL,
        messages=messages,
        temperature=0.4,
    )

    choice = response.choices[0]
    content = choice.message.content or ''
    logger.info('OpenAI response received (%d characters)', len(content))
    return content.strip()
