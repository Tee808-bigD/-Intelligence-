"""personal_assistant.py
--------
A standalone Super-Agent with full local system access,
internet connectivity, and Odysseus mesh integration.
Runs as a pure Python script without requiring ADK CLI.
"""

import asyncio
import os
import subprocess
import shutil
import json
from pathlib import Path
import httpx
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

# =============================================================================
# LOCAL SYSTEM TOOLS (The "PC Access" Suite)
# =============================================================================

async def list_directory(path: str = ".") -> str:
    """List the files and folders in the specified directory."""
    try:
        p = Path(path).expanduser().resolve()
        if not p.is_dir():
            return f"Error: {path} is not a directory."
        items = list(p.iterdir())
        result = [f"[{'DIR' if i.is_dir() else 'FILE'}] {i.name}" for i in items]
        return "\n".join(result) if result else "Directory is empty."
    except Exception as e:
        return f"Error listing directory: {str(e)}"

async def read_local_file(path: str) -> str:
    """Read the contents of a local file."""
    try:
        p = Path(path).expanduser().resolve()
        if not p.is_file():
            return f"Error: {path} is not a file."
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"Error reading file: {str(e)}"

async def write_local_file(path: str, content: str) -> str:
    """Write or overwrite a local file. REQUIRES PERMISSION."""
    try:
        p = Path(path).expanduser().resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

async def execute_shell_command(command: str) -> str:
    """Execute a shell command. REQUIRES PERMISSION."""
    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        output = stdout.decode().strip()
        error = stderr.decode().strip()
        if output and error:
            return f"STDOUT:\n{output}\n\nSTDERR:\n{error}"
        return output if output else error if error else "Command executed successfully."
    except Exception as e:
        return f"Error executing command: {str(e)}"

# =============================================================================
# WORLD & CONNECTIVITY TOOLS
# =============================================================================

async def web_search_and_fetch(query: str) -> str:
    """Search the internet and fetch the most relevant content."""
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
            response = await client.get(f"https://www.google.com/search?q={query}")
            return f"Search results for {query}:\n{response.text[:2000]}"
    except Exception as e:
        return f"Error during web search: {str(e)}"

async def nats_publish(subject: str, message: str) -> str:
    """Publish a message to the Odysseus NATS mesh."""
    try:
        import nats
        nc = await nats.connect(os.environ.get("NATS_URL", "nats://localhost:4222"))
        await nc.publish(subject.encode(), message.encode())
        await nc.close()
        return f"Published message to {subject}"
    except Exception as e:
        return f"Error publishing to NATS: {str(e)}"

# =============================================================================
# AGENT LOGIC & TOOL HANDLER
# =============================================================================

# Define the tool mapping
TOOLS = {
    "list_directory": list_directory,
    "read_local_file": read_local_file,
    "write_local_file": write_local_file,
    "execute_shell_command": execute_shell_command,
    "web_search_and_fetch": web_search_and_fetch,
    "nats_publish": nats_publish,
}

# Map tools to GenAI function declarations
FUNCTION_DECLS = [
    types.FunctionDeclaration(name="list_directory", description="List files in a directory", parameters={"type": "OBJECT", "properties": {"path": {"type": "STRING", "description": "Path to list"}}}),
    types.FunctionDeclaration(name="read_local_file", description="Read a local file", parameters={"type": "OBJECT", "properties": {"path": {"type": "STRING", "description": "Path to read"}}}),
    types.FunctionDeclaration(name="write_local_file", description="Write a local file. REQUIRES PERMISSION.", parameters={"type": "OBJECT", "properties": {"path": {"type": "STRING"}, "content": {"type": "STRING"}}}),
    types.FunctionDeclaration(name="execute_shell_command", description="Run shell command. REQUIRES PERMISSION.", parameters={"type": "OBJECT", "properties": {"command": {"type": "STRING"}}}),
    types.FunctionDeclaration(name="web_search_and_fetch", description="Search the internet", parameters={"type": "OBJECT", "properties": {"query": {"type": "STRING"}}}),
    types.FunctionDeclaration(name="nats_publish", description="Publish to Odysseus mesh", parameters={"type": "OBJECT", "properties": {"subject": {"type": "STRING"}, "message": {"type": "STRING"}}}),
]

async def main():
    # Initialize Gemini Client
    client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
    model_id = "gemini-1.5-flash-latest"

    chat = client.chats.create(
        model=model_id,
        config=types.GenerateContentConfig(
            tools=[types.Tool(function_declarations=FUNCTION_DECLS)],
            system_instruction=(
                "You are the Odysseus Super-Assistant. You have full access to the local PC and the internet.\n\n"
                "🛡️ PERMISSION RULE:\n"
                "You MUST ask for explicit permission before calling 'write_local_file', 'execute_shell_command', or 'nats_publish'.\n"
                "Describe the action and ask 'May I proceed?'. Only call the tool after the user says 'YES'.\n\n"
                "Be proactive, precise, and transparent."
            )
        )
    )

    print("\n🚀 Odysseus Super-Assistant is ONLINE (Local Mode)")
    print("Type 'exit' or 'quit' to stop.\n")

    while True:
        user_input = input("User: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        response = chat.send_message(user_input)

        # Handle Tool Calls
        while response.candidates[0].content.parts[0].function_call:
            part = response.candidates[0].content.parts[0]
            fn_call = part.function_call
            fn_name = fn_call.name
            fn_args = fn_call.args

            print(f"\n[Agent wants to use tool: {fn_name}]")
            print(f"Args: {fn_args}")

            # Permission Check for risky tools
            if fn_name in ["write_local_file", "execute_shell_command", "nats_publish"]:
                confirm = input(f"⚠️  The agent wants to execute {fn_name}. May I proceed? (yes/no): ")
                if confirm.lower() != "yes":
                    print("Permission denied. Telling agent to abort.")
                    response = chat.send_message(f"User denied permission to use {fn_name}. Please find another way or ask again.")
                    continue

            # Execute the tool
            tool_fn = TOOLS.get(fn_name)
            if tool_fn:
                result = await tool_fn(**fn_args)
                print(f"Tool Result: {result}")

                # Send result back to AI
                response = chat.send_message(
                    types.Part.from_function_response(
                        name=fn_name,
                        response={"result": result}
                    )
                )
            else:
                response = chat.send_message(f"Error: Tool {fn_name} not found.")

        print(f"\nAssistant: {response.text}\n")

if __name__ == "__main__":
    asyncio.run(main())
