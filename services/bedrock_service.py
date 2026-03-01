import os
import sys
import json
import asyncio
import boto3
from typing import AsyncGenerator
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'mcp'))

load_dotenv()

SYSTEM_PROMPT = """You are a factory assistant for Pristini.
Help users analyze employee performance, machine efficiency,
atelier productivity, dispatching, and global factory rendement.
Use your available tools to fetch real data when needed.
Do NOT narrate your actions. Never say "Let me look that up" or "I'll fetch the data".
Just fetch the data and present the results directly.

FORMATTING RULES (always follow):
- Use ## for section headings and ### for subsection headings.
- Use **bold** for labels, metrics names, and emphasis.
- Use markdown bullet lists (- item) for listing attributes. Indent sub-items with two spaces.
- Use numbered lists (1. 2. 3.) for ranked items.
- Use markdown tables (| col | col |) for tabular data -- always include a header row and separator row.
- Separate sections with blank lines for readability.
- Keep responses structured: heading, content, next heading.
- Never use plain text walls. Always structure the output.

CHART VISUALIZATION:
When the data lends itself to visualization (comparisons, distributions, trends), include a chart block.
Do NOT add charts for simple answers. Only use them when they add value (1-2 per response max).

```chart
{"type": "bar", "title": "Title", "labels": ["A", "B"], "values": [10, 20], "ylabel": "Unit"}
```

Supported types: bar, horizontal_bar, pie, line.
Place the chart right after the relevant data section.
"""


def _get_client():
    region = os.getenv("BEDROCK_REGION", "us-east-1")
    return boto3.client("bedrock-runtime", region_name=region)


def _anthropic_tools_to_bedrock(tools: list[dict]) -> list[dict]:
    bedrock_tools = []
    for t in tools:
        schema = t.get("input_schema", {"type": "object", "properties": {}})
        if "properties" not in schema:
            schema["properties"] = {}
        bedrock_tools.append({
            "toolSpec": {
                "name": t["name"],
                "description": t.get("description", ""),
                "inputSchema": {"json": schema},
            }
        })
    return bedrock_tools


def _format_messages(messages: list[dict]) -> list[dict]:
    formatted = []
    for m in messages:
        if not m.get("content", "").strip():
            continue
        role = "assistant" if m.get("role") in ("assistant", "model") else "user"
        formatted.append({
            "role": role,
            "content": [{"text": m["content"]}],
        })
    return formatted


def _stream_converse(client, model_id, conversation, tool_config):
    """Synchronous Bedrock converse_stream call (runs in thread)."""
    kwargs = {
        "modelId": model_id,
        "system": [{"text": SYSTEM_PROMPT}],
        "messages": conversation,
        "inferenceConfig": {"maxTokens": 4096},
    }
    if tool_config:
        kwargs["toolConfig"] = tool_config

    response = client.converse_stream(**kwargs)
    stream = response.get("stream", [])

    text_chunks = []
    assistant_content = []
    current_tool = None
    stop_reason = "end_turn"

    for event in stream:
        if "contentBlockStart" in event:
            start = event["contentBlockStart"].get("start", {})
            if "toolUse" in start:
                current_tool = {
                    "toolUseId": start["toolUse"]["toolUseId"],
                    "name": start["toolUse"]["name"],
                    "input_json": "",
                }
            else:
                current_tool = None

        elif "contentBlockDelta" in event:
            delta = event["contentBlockDelta"]["delta"]
            if "text" in delta:
                text_chunks.append(delta["text"])
                yield ("text", delta["text"])
            elif "toolUse" in delta and current_tool:
                current_tool["input_json"] += delta["toolUse"]["input"]

        elif "contentBlockStop" in event:
            if current_tool:
                try:
                    tool_input = json.loads(current_tool["input_json"]) if current_tool["input_json"] else {}
                except json.JSONDecodeError:
                    tool_input = {}
                assistant_content.append({
                    "toolUse": {
                        "toolUseId": current_tool["toolUseId"],
                        "name": current_tool["name"],
                        "input": tool_input,
                    }
                })
                current_tool = None
            elif text_chunks:
                assistant_content.append({"text": "".join(text_chunks)})
                text_chunks = []

        elif "messageStop" in event:
            stop_reason = event["messageStop"].get("stopReason", "end_turn")
            if text_chunks:
                assistant_content.append({"text": "".join(text_chunks)})
                text_chunks = []

    yield ("done", stop_reason, assistant_content)


async def stream_bedrock(messages: list, tools: list[dict]) -> AsyncGenerator[str, None]:
    from mcp_client import call_tool

    client = _get_client()
    model_id = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0")
    bedrock_tools = _anthropic_tools_to_bedrock(tools)
    conversation = _format_messages(messages)
    tool_config = {"tools": bedrock_tools} if bedrock_tools else None

    while True:
        stop_reason = "end_turn"
        assistant_content = []

        loop = asyncio.get_event_loop()
        queue: asyncio.Queue = asyncio.Queue()

        def _run_stream():
            for item in _stream_converse(client, model_id, conversation, tool_config):
                loop.call_soon_threadsafe(queue.put_nowait, item)

        thread = loop.run_in_executor(None, _run_stream)

        while True:
            item = await queue.get()
            if item[0] == "text":
                yield item[1]
            elif item[0] == "done":
                stop_reason = item[1]
                assistant_content = item[2]
                break

        await thread

        if stop_reason == "tool_use":
            conversation.append({"role": "assistant", "content": assistant_content})

            tool_results = []
            for block in assistant_content:
                if "toolUse" not in block:
                    continue
                tool_use = block["toolUse"]
                result = await call_tool(tool_use["name"], tool_use.get("input", {}))
                result_text = result if isinstance(result, str) else json.dumps(result)
                tool_results.append({
                    "toolResult": {
                        "toolUseId": tool_use["toolUseId"],
                        "content": [{"text": result_text}],
                    }
                })

            conversation.append({"role": "user", "content": tool_results})
        else:
            break


async def generate_bedrock(messages: list, tools: list[dict]) -> str:
    chunks = []
    async for chunk in stream_bedrock(messages, tools):
        chunks.append(chunk)
    return "".join(chunks)


async def generate_bedrock_with_prompt(messages: list, tools: list[dict], system_prompt: str) -> str:
    from mcp_client import call_tool

    client = _get_client()
    model_id = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0")
    bedrock_tools = _anthropic_tools_to_bedrock(tools)
    conversation = _format_messages(messages)
    tool_config = {"tools": bedrock_tools} if bedrock_tools else None

    while True:
        kwargs = {
            "modelId": model_id,
            "system": [{"text": system_prompt}],
            "messages": conversation,
            "inferenceConfig": {"maxTokens": 8192},
        }
        if tool_config:
            kwargs["toolConfig"] = tool_config

        response = client.converse(**kwargs)
        stop_reason = response.get("stopReason", "end_turn")
        output_message = response["output"]["message"]

        if stop_reason == "tool_use":
            conversation.append(output_message)
            tool_results = []
            for block in output_message["content"]:
                if "toolUse" not in block:
                    continue
                tool_use = block["toolUse"]
                result = await call_tool(tool_use["name"], tool_use.get("input", {}))
                result_text = result if isinstance(result, str) else json.dumps(result)
                tool_results.append({
                    "toolResult": {
                        "toolUseId": tool_use["toolUseId"],
                        "content": [{"text": result_text}],
                    }
                })
            conversation.append({"role": "user", "content": tool_results})
        else:
            for block in output_message["content"]:
                if "text" in block:
                    return block["text"]
            return ""
