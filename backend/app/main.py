from __future__ import annotations

from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .openai_client import OpenAIConfigurationError, generate_chat_response
from .mock_response import generate_mock_blocks, generate_upload_block
from .schemas import ChatRequest, ChatResponse, HealthResponse, ResponseBlock, ResponseCard
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


@app.get('/drawers/{filename}')
async def get_drawer(filename: str):
    """Serve drawer files from video_script/drawers/ directory.
    Supports .html files directly and .md files (converted to HTML on-the-fly)."""
    from fastapi.responses import HTMLResponse
    import markdown
    
    # Get the project root (backend/app/main.py -> backend -> project root)
    project_root = Path(__file__).resolve().parent.parent.parent
    drawer_path = project_root / 'video_script' / 'drawers' / filename

    if not drawer_path.exists():
        raise HTTPException(status_code=404, detail=f'Drawer {filename} not found')
    
    # If it's a .html file, serve it directly
    if filename.endswith('.html'):
        return FileResponse(drawer_path, media_type='text/html')
    
    # If it's a .md file, convert to HTML
    if filename.endswith('.md'):
        md_content = drawer_path.read_text(encoding='utf-8')
        
        # Convert markdown to HTML with extensions
        html_content = markdown.markdown(
            md_content,
            extensions=['extra', 'codehilite', 'tables', 'fenced_code']
        )
        
        # Wrap in HTML template with KaTeX support
        full_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{filename}</title>
  
  <!-- KaTeX CSS -->
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css"
        integrity="sha384-n8MVd4RsNIU0tAv4ct0nTaAbDJwPJzDEaqSD1odI+WdtXRGWt2kTvGFasHpSy3SV"
        crossorigin="anonymous">
  
  <!-- KaTeX JS -->
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"
          integrity="sha384-XjKyOOlGwcjNTAIQHIpgOno0Hl1YQqzUOEleOLALmuqehneUG+vnGctmUb0ZY0l8"
          crossorigin="anonymous"></script>
  
  <!-- KaTeX auto-render extension -->
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"
          integrity="sha384-+VBxd3r6XgURycqtZ117nYw44OOcIax56Z4dCRWbxyPt0Koah1uHoK0o4+/RRE05"
          crossorigin="anonymous"
          onload="renderMathInElement(document.body, {{
            delimiters: [
              {{left: '$$', right: '$$', display: true}},
              {{left: '$', right: '$', display: false}},
              {{left: '\\\\[', right: '\\\\]', display: true}},
              {{left: '\\\\(', right: '\\\\)', display: false}}
            ]
          }});"></script>
  
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 14px; line-height: 1.6; color: #212529; padding: 1.5rem; }}
    h1 {{ font-size: 1.5rem; font-weight: 600; color: #228be6; margin: 0 0 1rem 0; }}
    h2 {{ font-size: 1.25rem; font-weight: 600; color: #495057; margin: 1.5rem 0 0.75rem 0; }}
    h3 {{ font-size: 1.1rem; font-weight: 600; color: #495057; margin: 1.25rem 0 0.5rem 0; }}
    p {{ margin: 0 0 1rem 0; }}
    ul, ol {{ margin: 0 0 1rem 1.5rem; padding: 0; }}
    li {{ margin-bottom: 0.5rem; }}
    strong {{ font-weight: 600; }}
    code {{ background: #f1f3f5; padding: 0.125rem 0.375rem; border-radius: 3px; font-family: 'Monaco', monospace; font-size: 0.9em; }}
    pre {{ background: #f8f9fa; padding: 1rem; border-radius: 4px; overflow-x: auto; margin-bottom: 1rem; border: 1px solid #e9ecef; }}
    pre code {{ background: none; padding: 0; }}
    a {{ color: #228be6; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    hr {{ border: none; border-top: 1px solid #dee2e6; margin: 1.5rem 0; }}
    blockquote {{ border-left: 3px solid #228be6; padding-left: 1rem; margin: 1rem 0; color: #495057; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
    th, td {{ border: 1px solid #dee2e6; padding: 0.5rem; text-align: left; }}
    th {{ background: #f8f9fa; font-weight: 600; }}
  </style>
</head>
<body>
{html_content}
</body>
</html>'''
        
        return HTMLResponse(content=full_html)
    
    # Unsupported file type
    raise HTTPException(status_code=400, detail=f'Unsupported file type for {filename}')


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

        normalized_message = request.message.strip().lower()

        # ################################################################
        # Mock and LLM bypass check
        # ################################################################
        # -- Mock bypass
        if normalized_message.startswith('upload'):
            logger.info('Generating upload preview card')
            blocks = generate_upload_block()
            cards = [_build_user_assistant_card(request.message, blocks)]
        elif normalized_message.startswith('mock'):
            logger.info('Generating mock response card')
            blocks = generate_mock_blocks(request.space_key)
            cards = [_build_user_assistant_card(request.message, blocks)]
        # -- LLM bypass
        elif normalized_message.startswith('llm'):
            assistant_message = await generate_chat_response(
                request.message,
                request.space_title,
                history=request.history
            )
            blocks = [ResponseBlock(type='markdown', content=assistant_message)]
            cards = [_build_user_assistant_card(request.message, blocks)]
        # -- RBSA / Analytics
        else:
            from analytics.chat_router_rbsa import process_message
            cards = process_message(request.message)
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
            'message_blocks': sum(len(card.assistant_blocks) for card in cards)
        }
    )

    return ChatResponse(
        conversation_id=request.conversation_id,
        cards=cards,
        timestamp=timestamp
    )


def _build_user_assistant_card(user_text: str, blocks: List[ResponseBlock]) -> ResponseCard:
    return ResponseCard(card_type='user-assistant', user_text=user_text, assistant_blocks=blocks)
