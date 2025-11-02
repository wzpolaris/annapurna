            
import os
import sys
import dotenv
from openai import OpenAI

dotenv.load_dotenv()  # Load environment variables from .env file

_own_dir = os.path.dirname(__file__)
if _own_dir not in sys.path:
    sys.path.insert(0, _own_dir)

_project_root = os.path.abspath(os.path.join(_own_dir, '..', '..'))
print(f"Project root: {_project_root}")

from rbsa_pipeline import rbsa_run_pipeline as rbsa_run_pipeline

OPENAI_CONTEXT_MAX_CHARS = 100_000  # Approximate max chars for LLM context (e.g. gpt-4, gpt-5)


def load_config():
    import os
    import yaml
    # Load config from config.yaml in project root
    _proj_root = os.path.join(os.path.dirname(__file__), '..', '..')
    print(_proj_root)
    config_path = os.path.join(_proj_root, "config.yaml")
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)
    return cfg


def call_llm(text :str) -> str:

    max_chars = OPENAI_CONTEXT_MAX_CHARS
    if len(text) > max_chars:
        raise ValueError(f'LLM input exceeds {max_chars} characters. Received {len(text)}.')

    cfg = load_config()
    model = cfg["summarization"].get("model", "gpt-4")

    system_prompt = cfg["summarization"].get("system_prompt", "You are a helpful assistant.")

    client = OpenAI()  # Automatically reads OPENAI_API_KEY from environment

    # Check if using GPT-5 (new Responses API) or GPT-4 (Chat Completions API)
        # GPT-5 uses the new Responses API
    if model.startswith("gpt-5"):
        prompt = f"{system_prompt}\n\n{text}"
        resp = client.responses.create(
            model=model,
            input=prompt,
            reasoning={"effort": "medium"},
            text={"verbosity": "medium"}
        )
        return resp.output_text.strip()
    else:
        raise Exception("Only gpt-5 models are supported currently.")


def ai_main():
    s  = 'what is the capital of france?'
    response = call_llm(s)
    return response


if __name__ == "__main__":

    resp = ai_main()
    print(resp)
