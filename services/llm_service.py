import os
import sys
import json
import anthropic
from typing import AsyncGenerator
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'mcp'))
from mcp_client import get_tools_for_anthropic, call_tool

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


def _format_messages(messages: list) -> list[dict]:
    return [
        {
            "role": "assistant" if m.get("role") in ("assistant", "model") else "user",
            "content": m["content"]
        }
        for m in messages if m.get("content", "").strip()
    ]


async def _stream_anthropic(messages: list, tools: list[dict]) -> AsyncGenerator[str, None]:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY is not configured in environment")

    client = anthropic.AsyncAnthropic(api_key=api_key)
    model = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
    formatted = _format_messages(messages)

    while True:
        async with client.messages.stream(
            model=model,
            system=SYSTEM_PROMPT,
            max_tokens=4096,
            tools=tools,
            messages=formatted,
        ) as stream:
            async for text in stream.text_stream:
                yield text

            final = await stream.get_final_message()

        if final.stop_reason == "tool_use":
            formatted.append({"role": "assistant", "content": final.content})

            for block in final.content:
                if block.type != "tool_use":
                    continue
                tool_result = await call_tool(block.name, block.input)
                formatted.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": tool_result if isinstance(tool_result, str) else json.dumps(tool_result),
                    }]
                })
        else:
            break


async def _generate_anthropic(messages: list, tools: list[dict]) -> str:
    chunks = []
    async for chunk in _stream_anthropic(messages, tools):
        chunks.append(chunk)
    return "".join(chunks)


async def generate(messages: list) -> str:
    tools = await get_tools_for_anthropic()
    provider = os.getenv("LLM_PROVIDER", "anthropic").lower().strip()

    if provider == "bedrock":
        from services.bedrock_service import generate_bedrock
        return await generate_bedrock(messages, tools)

    return await _generate_anthropic(messages, tools)


async def generate_stream(messages: list) -> AsyncGenerator[str, None]:
    tools = await get_tools_for_anthropic()
    provider = os.getenv("LLM_PROVIDER", "anthropic").lower().strip()

    if provider == "bedrock":
        from services.bedrock_service import stream_bedrock
        async for chunk in stream_bedrock(messages, tools):
            yield chunk
    else:
        async for chunk in _stream_anthropic(messages, tools):
            yield chunk


async def generate_report(messages: list) -> str:
    """Generate a report-formatted response using the report system prompt."""
    from services.report_service import REPORT_SYSTEM_PROMPT
    tools = await get_tools_for_anthropic()
    provider = os.getenv("LLM_PROVIDER", "anthropic").lower().strip()

    if provider == "bedrock":
        from services.bedrock_service import generate_bedrock_with_prompt
        return await generate_bedrock_with_prompt(messages, tools, REPORT_SYSTEM_PROMPT)

    return await _generate_with_prompt(messages, tools, REPORT_SYSTEM_PROMPT)


async def _generate_with_prompt(messages: list, tools: list[dict], system_prompt: str) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY is not configured in environment")

    client = anthropic.AsyncAnthropic(api_key=api_key)
    model = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
    formatted = _format_messages(messages)

    while True:
        response = await client.messages.create(
            model=model,
            system=system_prompt,
            max_tokens=8192,
            tools=tools,
            messages=formatted,
        )

        if response.stop_reason == "tool_use":
            formatted.append({"role": "assistant", "content": response.content})
            for block in response.content:
                if block.type != "tool_use":
                    continue
                tool_result = await call_tool(block.name, block.input)
                formatted.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": tool_result if isinstance(tool_result, str) else json.dumps(tool_result),
                    }]
                })
        else:
            return next((b.text for b in response.content if b.type == "text"), "")
