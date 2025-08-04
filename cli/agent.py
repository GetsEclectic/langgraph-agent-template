#!/usr/bin/env python3
"""
CLI interface for the LangGraph agent template.
Provides chat and server functionality for agent interaction.
"""

import asyncio
import os
import subprocess
import sys

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from agent.graph import AgentConfig, create_agent

app = typer.Typer(help="LangGraph AI Agent - Extensible agent with MCP integration")
console = Console()


@app.command()
def chat(
    goal: str | None = typer.Argument(None, help="Initial goal or task for the agent"),
    model: str = typer.Option("claude-3-5-sonnet-20241022", help="Model to use"),
    temperature: float = typer.Option(0.1, help="Model temperature"),
) -> None:
    """
    Start an interactive chat session with the agent.
    """
    asyncio.run(_chat_session(goal, model, temperature))


async def _chat_session(
    initial_goal: str | None, model: str, temperature: float
) -> None:
    """Run an interactive chat session with the agent."""
    load_dotenv()

    console.print(
        Panel.fit(
            "[bold blue]🤖 LangGraph Agent[/bold blue]\n"
            "AI assistant with MCP integration\n\n"
            "[dim]Type 'quit' to exit[/dim]",
            title="Welcome",
        )
    )

    # Initialize agent
    try:
        config = AgentConfig(model_name=model, temperature=temperature)
        console.print("🔧 Initializing agent...")
        agent = await create_agent(config)
        console.print("✅ Agent ready!")
    except Exception as e:
        console.print(f"❌ Failed to initialize agent: {e}")
        return

    # Get initial goal if not provided
    if not initial_goal:
        initial_goal = Prompt.ask(
            "\n[bold]What would you like me to help you with?[/bold]",
            default="Help me understand what you can do",
        )

    try:
        while True:
            console.print(f"\n[bold blue]Goal:[/bold blue] {initial_goal}")
            console.print("🤔 Thinking...")

            try:
                result = await agent.run(initial_goal)

                # Display the agent's response
                if "messages" in result and result["messages"]:
                    last_message = result["messages"][-1]
                    if hasattr(last_message, "content"):
                        content = last_message.content
                    else:
                        content = str(last_message)

                    console.print(
                        Panel(content, title="🤖 Agent Response", border_style="blue")
                    )

            except Exception as e:
                console.print(f"❌ Agent error: {e}")

            # Get next goal
            console.print("\n" + "=" * 50)
            next_goal = Prompt.ask(
                "[bold]What's next?[/bold] (or 'quit' to exit)", default="quit"
            )

            if next_goal.lower() in ["quit", "exit", "q"]:
                break

            initial_goal = next_goal

    finally:
        await agent.cleanup()
        console.print("👋 Goodbye!")


@app.command()
def serve(
    port: int = typer.Option(8000, help="Port to bind the LangGraph server to"),
    allow_blocking: bool = typer.Option(False, help="Allow blocking operations (needed for LangSmith Hub)"),
) -> bool:
    """
    Start the LangGraph server for chat UI integration.
    """
    console.print(
        Panel.fit(
            "[bold blue]🚀 Starting LangGraph Server[/bold blue]\n\n"
            f"[bold]Port:[/bold] {port}\n\n"
            "[bold yellow]Next Steps:[/bold yellow]\n"
            "1. Server will start on the specified port\n"
            "2. In another terminal: cd chat-ui && npm run dev\n"
            "3. Open: http://localhost:3000",
            title="LangGraph Server",
        )
    )

    try:
        cmd = ["langgraph", "dev", "--port", str(port)]
        if allow_blocking:
            cmd.append("--allow-blocking")
        result = subprocess.run(cmd, check=False)
        return result.returncode == 0

    except FileNotFoundError:
        console.print(
            "❌ langgraph CLI not found. Install with: pip install 'langgraph-cli[inmem]'"
        )
        return False
    except KeyboardInterrupt:
        console.print("\n👋 Server stopped")
        return True
    except Exception as e:
        console.print(f"❌ Failed to start LangGraph server: {e}")
        return False


@app.command(name="chat-ui")
def start_chat_ui(port: int = typer.Option(3000, help="Port for the chat UI")) -> bool:
    """
    Start the chat UI for interacting with the agent.
    Requires the LangGraph server to be running first.
    """
    chat_ui_path = os.path.join(os.getcwd(), "chat-ui")

    if not os.path.exists(chat_ui_path):
        console.print("❌ Chat UI not found at ./chat-ui/")
        return False

    console.print(
        Panel.fit(
            "[bold green]🎨 Starting Chat UI[/bold green]\n\n"
            f"[bold]Port:[/bold] {port}\n"
            f"[bold]Path:[/bold] {chat_ui_path}\n\n"
            "[bold yellow]Prerequisites:[/bold yellow]\n"
            "1. LangGraph server must be running on port 8000\n"
            "2. Run 'python -m cli.agent serve' in another terminal\n\n"
            f"[bold cyan]Access:[/bold cyan] http://localhost:{port}",
            title="Chat UI",
        )
    )

    try:
        result = subprocess.run(
            ["npm", "run", "dev", "--", "--port", str(port)],
            cwd=chat_ui_path,
            check=False,
        )
        return result.returncode == 0

    except FileNotFoundError:
        console.print("❌ npm not found. Please install Node.js and npm.")
        return False
    except KeyboardInterrupt:
        console.print("\n👋 Chat UI stopped")
        return True
    except Exception as e:
        console.print(f"❌ Failed to start chat UI: {e}")
        return False


@app.command()
def test() -> bool:
    """
    Run the test suite to verify the agent is working.
    """
    console.print("🧪 Running agent tests...")

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-v"],
            capture_output=True,
            text=True,
        )

        console.print(result.stdout)
        if result.stderr:
            console.print(f"[red]Errors:[/red]\n{result.stderr}")

        if result.returncode == 0:
            console.print("✅ All tests passed!")
        else:
            console.print("❌ Some tests failed.")

        return result.returncode == 0

    except Exception as e:
        console.print(f"❌ Failed to run tests: {e}")
        return False


if __name__ == "__main__":
    app()
