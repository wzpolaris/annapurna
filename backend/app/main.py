from __future__ import annotations

from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .openai_client import OpenAIConfigurationError, generate_chat_response
from .mock_response import generate_mock_blocks
from .schemas import ChatRequest, ChatResponse, HealthResponse, ResponseBlock
from .tables import build_space_table


#################################################################
# Hack to include analytics module
#################################################################
# import sys
# from pathlib import Path
# DEFAULT_PROJECT_ROOT = Path(__file__).resolve().parent.parent
# if str(DEFAULT_PROJECT_ROOT) not in sys.path:
#     sys.path.insert(1,str(DEFAULT_PROJECT_ROOT))
#     try:
#         from analytics.chat_router_rbsa import process_message
#         print('Imported analytics module.')
#     except ImportError:
#         raise Exception('Cannot import analytics module')


# Configure concurrent logging for multi-worker safety
try:
    from concurrent_log_handler import ConcurrentRotatingFileHandler
    CONCURRENT_LOGGING = True
except ImportError:
    CONCURRENT_LOGGING = False
    print("Warning: concurrent-log-handler not installed. Using standard FileHandler.")

log_dir = Path(__file__).resolve().parent.parent.parent / 'logs'
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / 'fastapi.log'

# Set up concurrent logging
if CONCURRENT_LOGGING:
    handler = ConcurrentRotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
else:
    handler = logging.FileHandler(log_file, encoding='utf-8')



logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s [%(module)s.%(funcName)s:%(lineno)d]: %(message)s',
    handlers=[handler]
)
logger = logging.getLogger('main.fastapi')


app = FastAPI(
    title='Northfield Backend',
    version='0.1.0',
    docs_url='/docs',
    redoc_url='/redoc'
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get('/health', response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse()


@app.post('/chat', response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    try:

        logger.info(
            'Chat request received',
            extra={
                'conversation_id': request.conversation_id,
                'space_key': request.space_key,
                'space_title': request.space_title,
                'history_length': len(request.history or [])
            }
        )

        # ################################################################
        # Mock and LLM bypass check
        # ################################################################
        # -- Mock bypass
        if request.message.strip().lower().startswith('mock'):
            logger.info('Generating mock response blocks')
            outputs = generate_mock_blocks(request.space_key)
        # -- LLM bypass
        elif request.message.strip().lower().startswith('llm'):
            assistant_message = await generate_chat_response(
                request.message,
                request.space_title,
                history=request.history
            )
            outputs = [ResponseBlock(type='markdown', content=assistant_message)]
        # -- RBSA
        else:
            from analytics.chat_router_rbsa import process_message
            summary_text: str = process_message(request.message)
            outputs = [
                ResponseBlock(type='markdown', content=summary_text, altText=None)
            ]
    except OpenAIConfigurationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - surface unexpected errors
        logger.exception('OpenAI call failed')
        raise HTTPException(status_code=502, detail='OpenAI request failed') from exc

    # table_md: Optional[str] = None
    # if request.space_key and request.space_key != 'home' and not request.message.strip().lower().startswith('mock'):
    #     table_md = build_space_table(request.space_key)

    # if table_md:
    #     outputs.append(ResponseBlock(type='markdown', content=f"### Data snapshot\n{table_md}"))

    timestamp = datetime.now(tz=timezone.utc).isoformat()

    logger.info(
        'Chat response ready',
        extra={
            'conversation_id': request.conversation_id,
            'timestamp': timestamp,
            'message_blocks': len(outputs)
        }
    )

    return ChatResponse(
        conversation_id=request.conversation_id,
        outputs=outputs,
        timestamp=timestamp
    )
