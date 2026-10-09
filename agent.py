import os
import json
import time
import google.generativeai as genai
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from tools import (
    get_active_alerts, get_service_logs, 
    restart_service, get_service_status, create_incident_ticket,
    search_company_runbooks, request_human_approval
)

console = Console()

def build_agent():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        console.print("[bold red]❌ Error: GEMINI_API_KEY environment variable is not set![/bold red]")
        exit(1)
    
    genai.configure(api_key=api_key)

    tools_dict = {
        "get_active_alerts": get_active_alerts,
        "get_service_logs": get_service_logs,
        "restart_service": restart_service,
        "get_service_status": get_service_status,
        "create_incident_ticket": create_incident_ticket,
        "search_company_runbooks": search_company_runbooks,
        "request_human_approval": request_human_approval
    }

    system_instruction = """
    You are an autonomous L1 DevOps Remediator agent.
    Your goal is to investigate system alerts, diagnose issues by reading logs, 
    remediate problems (e.g., by restarting services), verify the fix worked, 
    and log an incident ticket.
    
    CRITICAL INSTRUCTIONS:
    1. UNDERSTAND: Start by checking for active alerts.
    2. CONTEXT: If a service is degraded, you MUST call 'search_company_runbooks' to learn the policy for that specific service BEFORE taking any action.
    3. PLAN & EXECUTE: Read the service logs to diagnose the issue. 
    4. APPROVAL: If the company runbook states that human approval is required, you MUST call 'request_human_approval' before performing a restart or any remediation. If denied, halt remediation.
    5. ADAPT: If you see memory leak logs or hanging processes (and have approval if required), a restart is the appropriate remediation.
    6. VERIFY: ALWAYS verify your actions. If you restart a service, you MUST check its status afterwards to ensure it is 'healthy' before concluding.
    7. COMPLETE: Once verified, ALWAYS create a ticket summarizing the root cause and the fix applied.
    8. EFFICIENCY: To prevent API rate limits, you MUST call multiple tools concurrently in a single turn whenever possible (e.g., if you know you need to check logs and check the runbook, do both in the same turn).
    9. Once the ticket is created, output a final summary for the user.
    """

    model = genai.GenerativeModel(
        model_name="gemini-flash-lite-latest",
        tools=list(tools_dict.values()),
        system_instruction=system_instruction
    )
    
    return model, tools_dict

def run_agentic_loop(user_prompt: str):
    console.print(Panel(f"[bold white]{user_prompt}[/bold white]", title="🚀 [bold green]User Request[/bold green]", border_style="green"))
    
    model, tools_dict = build_agent()
    chat = model.start_chat()
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with console.status("[bold cyan]🤖 Agent is reading request...[/bold cyan]", spinner="dots"):
                response = chat.send_message(user_prompt)
            break
        except Exception as e:
            if "429" in str(e) or "Quota exceeded" in str(e):
                console.print(f"[bold red]⏳ RATE LIMIT:[/bold red] [yellow]Free tier limit hit on initial request. Pausing for 60 seconds... (Attempt {attempt+1}/{max_retries})[/yellow]")
                with console.status("[bold yellow]Sleeping to reset quota...[/bold yellow]", spinner="clock"):
                    time.sleep(60)
            else:
                raise e
    
    while True:
        if not response.parts or not hasattr(response.parts[0], 'function_call') or not response.parts[0].function_call:
            console.print(Panel(f"[white]{response.text}[/white]", title="✅ [bold green]Agent Final Summary[/bold green]", border_style="green"))
            break
        
        tool_responses = []
        
        for part in response.parts:
            if part.function_call:
                func_name = part.function_call.name
                args = {k: v for k, v in part.function_call.args.items()}
                
                # Format arguments nicely
                formatted_args = json.dumps(args, indent=2) if args else "{}"
                thought_text = f"[bold cyan]Tool:[/bold cyan] {func_name}\n[bold cyan]Args:[/bold cyan]\n{formatted_args}"
                console.print(Panel(thought_text, title="🧠 [bold blue]Agent Thought & Plan[/bold blue]", border_style="blue"))
                time.sleep(1.75) # Added artificial delay to improve UI readability for human operators monitoring the terminal
                
                func = tools_dict.get(func_name)
                if func:
                    try:
                        # Actually run the function
                        result = func(**args)
                        
                        # Try to format observation as pretty JSON if possible
                        try:
                            parsed_json = json.loads(result)
                            pretty_json = json.dumps(parsed_json, indent=2)
                            syntax = Syntax(pretty_json, "json", theme="monokai", word_wrap=True)
                            console.print(Panel(syntax, title="👁️ [bold magenta]System Observation[/bold magenta]", border_style="magenta"))
                        except:
                            console.print(Panel(str(result), title="👁️ [bold magenta]System Observation[/bold magenta]", border_style="magenta"))
                        
                        time.sleep(1.75) # Added artificial delay to improve UI readability for human operators monitoring the terminal
                        
                        tool_responses.append(
                            {
                                "function_response": {
                                    "name": func_name,
                                    "response": {"result": result}
                                }
                            }
                        )
                    except Exception as e:
                        error_msg = str(e)
                        console.print(Panel(f"[bold red]{error_msg}[/bold red]", title="⚠️ [bold red]Execution Error[/bold red]", border_style="red"))
                        tool_responses.append(
                            {
                                "function_response": {
                                    "name": func_name,
                                    "response": {"error": error_msg}
                                }
                            }
                        )
                else:
                    console.print(f"[bold red]⚠️ SYSTEM ERROR: Tool '{func_name}' not found.[/bold red]\n")
        
        if tool_responses:
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    with console.status("[bold cyan]🔄 Agent is analyzing observation and planning next move...[/bold cyan]", spinner="bouncingBar"):
                        response = chat.send_message(tool_responses)
                    break 
                except Exception as e:
                    if "429" in str(e) or "Quota exceeded" in str(e):
                        console.print(f"[bold red]⏳ RATE LIMIT:[/bold red] [yellow]Free tier limit hit. Pausing for 60 seconds... (Attempt {attempt+1}/{max_retries})[/yellow]")
                        with console.status("[bold yellow]Sleeping to reset quota...[/bold yellow]", spinner="clock"):
                            time.sleep(60)
                    else:
                        raise e 
        else:
            break

if __name__ == "__main__":
    try:
        run_agentic_loop("Please check the system for any active alerts and resolve them. Make sure to log a ticket when done.")
    except KeyboardInterrupt:
        console.print("\n[bold red]Agent stopped by user.[/bold red]")
