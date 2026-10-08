import os
import json
import google.generativeai as genai
from tools import (
    get_active_alerts, get_service_logs, 
    restart_service, get_service_status, create_incident_ticket
)

def build_agent():
    # 1. Ensure API key is present
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set!")
    
    genai.configure(api_key=api_key)

    # 2. Map tools for manual execution
    tools_dict = {
        "get_active_alerts": get_active_alerts,
        "get_service_logs": get_service_logs,
        "restart_service": restart_service,
        "get_service_status": get_service_status,
        "create_incident_ticket": create_incident_ticket
    }

    # 3. System Prompt - Defines the agent's behavior, autonomy, and verification constraints
    system_instruction = """
    You are an autonomous L1 DevOps Remediator agent.
    Your goal is to investigate system alerts, diagnose issues by reading logs, 
    remediate problems (e.g., by restarting services), verify the fix worked, 
    and log an incident ticket.
    
    CRITICAL INSTRUCTIONS:
    1. UNDERSTAND: Start by checking for active alerts.
    2. PLAN & EXECUTE: If a service is degraded, read its logs to diagnose the issue. 
    3. ADAPT: If you see memory leak logs or hanging processes, a restart is the appropriate remediation.
    4. VERIFY: ALWAYS verify your actions. If you restart a service, you MUST check its status afterwards to ensure it is 'healthy' before concluding.
    5. COMPLETE: Once verified, ALWAYS create a ticket summarizing the root cause and the fix applied.
    6. Once the ticket is created, output a final summary for the user.
    """

    # We use gemini-3.5-flash as it is exceptionally fast at tool calling
    model = genai.GenerativeModel(
        model_name="gemini-3.5-flash",
        tools=list(tools_dict.values()),
        system_instruction=system_instruction
    )
    
    return model, tools_dict

def run_agentic_loop(user_prompt: str):
    """
    This is the core ReAct (Reason + Act) loop. 
    It fulfills the Intern Assignment's requirement for:
    Understand -> Plan -> Execute -> Observe -> Adapt -> Verify -> Complete
    """
    print(f"\n🚀 [USER REQUEST]: {user_prompt}\n")
    print("-" * 60)
    
    model, tools_dict = build_agent()
    chat = model.start_chat()
    
    # 1. Send initial goal
    response = chat.send_message(user_prompt)
    
    # 2. The loop
    while True:
        # If the LLM didn't request a tool call, it's done processing and is just talking.
        if not response.parts or not hasattr(response.parts[0], 'function_call') or not response.parts[0].function_call:
            print("\n✅ [AGENT FINAL SUMMARY]:")
            print(response.text)
            break
        
        tool_responses = []
        
        # Iterate over all tool calls the LLM wants to make concurrently
        for part in response.parts:
            if part.function_call:
                func_name = part.function_call.name
                args = {k: v for k, v in part.function_call.args.items()}
                
                print(f"🧠 [AGENT THOUGHT/PLAN]: Decided to use tool '{func_name}'")
                print(f"🔧 [AGENT EXECUTE]: Calling {func_name}({args})")
                
                # Actually run the local Python function
                func = tools_dict.get(func_name)
                if func:
                    try:
                        result = func(**args)
                        print(f"👁️  [OBSERVATION]: {result}\n")
                        
                        # Pack the result back into a format the LLM understands
                        tool_responses.append(
                            {
                                "function_response": {
                                    "name": func_name,
                                    "response": {"result": result}
                                }
                            }
                        )
                    except Exception as e:
                        # Error handling (Reliability criteria)
                        error_msg = str(e)
                        print(f"⚠️  [EXECUTION ERROR]: {error_msg}\n")
                        tool_responses.append(
                            {
                                "function_response": {
                                    "name": func_name,
                                    "response": {"error": error_msg}
                                }
                            }
                        )
                else:
                    print(f"⚠️ [SYSTEM ERROR]: Tool '{func_name}' not found.\n")
        
        # 3. Adapt/Verify: Send the observations back to the LLM so it can decide the next step
        if tool_responses:
            print("🔄 [AGENT]: Analyzing observation and deciding next action...")
            import time
            
            # Retry loop for rate limits
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = chat.send_message(tool_responses)
                    break # Success, break out of retry loop
                except Exception as e:
                    if "429" in str(e) or "Quota exceeded" in str(e):
                        print(f"⏳ [RATE LIMIT]: Free tier limit hit. Pausing for 60 seconds before resuming... (Attempt {attempt+1}/{max_retries})")
                        time.sleep(60)
                    else:
                        raise e # If it's not a rate limit, crash normally
        else:
            break

if __name__ == "__main__":
    # Example execution
    try:
        run_agentic_loop("Please check the system for any active alerts and resolve them. Make sure to log a ticket when done.")
    except Exception as e:
        print(f"\n❌ Failed to run agent: {e}")
        print("Did you forget to export GEMINI_API_KEY?")
