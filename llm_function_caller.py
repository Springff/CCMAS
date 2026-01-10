"""
Lightweight helper to use model function-calling (OpenAI-compatible).

This module provides:
- `convert_tools_to_openai_functions(tools_definitions)` : convert tool JSON-schema defs to OpenAI `functions` format
- `call_model_with_functions(messages, functions, llm_config)` : call the LLM using the `functions` parameter and return the assistant response

Notes:
- This is intentionally small and targets OpenAI-compatible APIs. If you use another provider,
  adapt the call implementation accordingly.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

try:
    import openai
    _HAVE_OPENAI = True
except Exception:
    _HAVE_OPENAI = False


def convert_tools_to_openai_functions(tools_definitions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert a list of tool definitions (as returned by `get_tools_for_autogen()`)
    to an OpenAI-compatible `functions` list.

    Each input tool is expected to be a dict with at least `name` and `description`.
    If a tool contains a `parameters` JSON Schema, it will be reused for `parameters`.
    """
    functions = []

    for t in tools_definitions:
        func = {
            "name": t.get("name") or t.get("tool_name") or "unnamed_tool",
            "description": t.get("description", ""),
        }

        # Use existing JSON Schema if provided
        parameters = t.get("parameters") or t.get("json_schema") or None
        if parameters and isinstance(parameters, dict):
            func["parameters"] = parameters
        else:
            # fallback: accept any object
            func["parameters"] = {"type": "object", "properties": {}}

        functions.append(func)

    return functions


def _get_api_key_from_config(llm_config: Optional[Dict[str, Any]]) -> Optional[str]:
    if not llm_config:
        return os.getenv("LLM_API_KEY")
    # attempt to extract
    try:
        return llm_config.get("config_list", [])[0].get("api_key")
    except Exception:
        return os.getenv("LLM_API_KEY")


def call_model_with_functions(
    messages: List[Dict[str, str]],
    functions: List[Dict[str, Any]],
    llm_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Call the LLM with the `functions` parameter (OpenAI-style). Returns a dict with keys:
    - `role`: e.g. 'assistant' or 'function'
    - `content`: assistant textual content (may be empty if function_call produced)
    - `function_call`: when model requests a function call, this field is present and contains {name, arguments}
    - `raw`: raw API response object

    Raises RuntimeError if no OpenAI client is available.
    """
    if not _HAVE_OPENAI:
        raise RuntimeError("openai package not available. Install 'openai' to use function-calling helper.")

    api_key = _get_api_key_from_config(llm_config)
    if api_key:
        openai.api_key = api_key

    model = None
    temperature = 0.7
    try:
        if llm_config:
            model = llm_config.get("config_list", [])[0].get("model")
            temperature = llm_config.get("temperature", temperature)
    except Exception:
        pass

    model = model or os.getenv("LLM_MODEL_ID") or "gpt-4-0613"

    try:
        logger.info(f"Calling model {model} with {len(functions)} functions")
        resp = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            functions=functions,
            function_call="auto",
            temperature=temperature,
        )

        # navigate response
        choice = resp.get("choices", [])[0]
        message = choice.get("message", {})

        out = {
            "role": message.get("role"),
            "content": message.get("content"),
            "function_call": message.get("function_call"),
            "raw": resp,
        }

        return out

    except Exception as e:
        logger.exception("Error calling OpenAI ChatCompletion.create")
        raise
