# services/llm_service.py
import os
import sys
import json
import anthropic
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'mcp'))
from mcp_client import get_tools_for_anthropic, call_tool

load_dotenv()

SYSTEM_PROMPT = """
You are a factory assistant for Pristini.
Help users analyze employee performance, machine efficiency,
atelier productivity, dispatching, and global factory rendement.
Use your available tools to fetch real data when needed.
Respond clearly and professionally.
"""

async def generate(messages: list) -> str:
    """
    Generate a response using Claude with MCP tool support.
    
    Args:
        messages: List of message dicts with 'role' and 'content' keys
        
    Returns:
        str: Claude's response text
    """
    # Validate API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY is not configured in environment")
    
    # Initialize client
    client = anthropic.Anthropic(api_key=api_key)
    model = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
    
    # Fetch available MCP tools
    tools = await get_tools_for_anthropic()
    
    # Format messages for Anthropic API
    formatted = [
        {
            "role": "assistant" if m.get("role") in ("assistant", "model") else "user",
            "content": m["content"]
        }
        for m in messages if m.get("content", "").strip()
    ]
    
    # Tool use loop
    while True:
        response = client.messages.create(
            model=model,
            system=SYSTEM_PROMPT,
            max_tokens=4096,  # Increased for more comprehensive responses
            tools=tools,
            messages=formatted
        )
        
        # Check if Claude wants to use a tool
        if response.stop_reason == "tool_use":
            # Find the tool use block
            tool_block = next(b for b in response.content if b.type == "tool_use")
            
            # Execute the tool via MCP
            tool_result = await call_tool(tool_block.name, tool_block.input)
            
            # Add assistant's tool use to conversation
            formatted.append({"role": "assistant", "content": response.content})
            
            # Add tool result back to conversation
            formatted.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": tool_block.id,
                    "content": tool_result if isinstance(tool_result, str) else json.dumps(tool_result)
                }]
            })
            
            # Continue loop to let Claude process the tool result
        else:
            # No more tools needed, return final response
            return next((b.text for b in response.content if b.type == "text"), "")