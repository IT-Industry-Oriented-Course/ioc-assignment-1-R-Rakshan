import json
import os
import sys
from typing import List, Dict, Any, Optional
from huggingface_hub import InferenceClient
from rich.console import Console
from rich.panel import Panel

import tools
import utils

console = Console()

class ClinicalAgent:
    def __init__(self, api_key: str, model: str = "Qwen/Qwen2.5-72B-Instruct", dry_run: bool = False):
        self.client = InferenceClient(api_key=api_key)
        self.model = model
        self.dry_run = dry_run
        self.tools_map = {
            "search_patient": tools.search_patient,
            "check_insurance_eligibility": tools.check_insurance_eligibility,
            "find_available_slots": tools.find_available_slots,
            "book_appointment": tools.book_appointment
        }
        self.tool_schemas = tools.get_all_tool_schemas()
        self.messages = []
        self.system_prompt = self._build_system_prompt()
        
    def _build_system_prompt(self) -> str:
        schemas_str = json.dumps(self.tool_schemas, indent=2)
        return f"""
You are a Clinical Workflow Orchestrator. Your goal is to help clinicians and admins with appointment scheduling and care coordination.
You have access to the following tools:

{schemas_str}

**Instructions:**
1. Analyze the user's request.
2. Determine if you need to use a tool.
3. If you need to use a tool, output a JSON object with the following format:
   {{
     "tool_name": "<name_of_tool>",
     "arguments": {{ <args_object> }}
   }}
4. If you have the result from a tool, use it to answer the user's request or call the next tool.
5. If you have completed the task or cannot perform it, respond with a final answer in natural language.
6. **CRITICAL:** Do NOT provide medical advice or diagnoses. If asked, refuse politely.
7. **CRITICAL:** Do NOT hallucinate data. Only use data returned by tools.
8. **CRITICAL:** When booking, ensure you have a valid patient_id and slot_id.

**Response Format:**
- If calling a tool: Output ONLY the JSON object. Do not add conversational text.
- If providing a final answer: Just write the text.
"""

    def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        if tool_name not in self.tools_map:
            return f"Error: Tool '{tool_name}' not found."
        
        # Dry Run Logic for Side-Effecting Tools
        if self.dry_run and tool_name == "book_appointment":
            return json.dumps({
                "status": "success", 
                "appointment": {
                    "id": "mock_appt_001", 
                    "patient_id": arguments.get("patient_id"), 
                    "slot_id": arguments.get("slot_id"), 
                    "status": "Confirmed (Dry Run)"
                },
                "note": "This was a dry run. No booking was made."
            })

        try:
            func = self.tools_map[tool_name]
            result = func(**arguments)
            return json.dumps(result)
        except Exception as e:
            return f"Error executing tool '{tool_name}': {str(e)}"

    def run(self, user_input: str) -> Dict[str, Any]:
        """
        Runs the agent loop and returns a dictionary containing the final response
        and a trace of steps (thoughts/tool calls).
        """
        # Reset messages for a new turn if desired, or keep history. 
        if not self.messages:
            self.messages.append({"role": "system", "content": self.system_prompt})
        
        self.messages.append({"role": "user", "content": user_input})
        
        max_turns = 5
        turn = 0
        steps = []
        
        while turn < max_turns:
            turn += 1
            
            try:
                # Call LLM
                response = self.client.chat_completion(
                    model=self.model,
                    messages=self.messages,
                    max_tokens=500,
                    temperature=0.1
                )
                
                content = response.choices[0].message.content
                self.messages.append({"role": "assistant", "content": content})
                
                # Check for tool call
                tool_call = self._parse_tool_call(content)
                
                if tool_call:
                    console.print(Panel(f"Tool Call: {tool_call['tool_name']}\nArgs: {tool_call['arguments']}", title="Agent Action", style="bold cyan"))
                    
                    # Audit Log Decision
                    utils.log_audit("AGENT_DECISION", {"tool": tool_call['tool_name'], "args": tool_call['arguments']})
                    
                    # Execute tool
                    result_str = self._execute_tool(tool_call['tool_name'], tool_call['arguments'])
                    
                    console.print(Panel(f"Result: {result_str}", title="Tool Output", style="bold green"))
                    
                    # Log step
                    steps.append({
                        "type": "tool_call",
                        "tool": tool_call['tool_name'],
                        "args": tool_call['arguments'],
                        "result": result_str
                    })
                    
                    # Feed back to LLM
                    self.messages.append({"role": "user", "content": f"Tool Output: {result_str}"})
                else:
                    # Final answer
                    return {
                        "final_answer": content,
                        "steps": steps
                    }
                    
            except Exception as e:
                console.print(f"[bold red]Error in agent loop:[/bold red] {e}")
                return {
                    "final_answer": "I encountered an error while processing your request.",
                    "steps": steps,
                    "error": str(e)
                }
                
        return {
            "final_answer": "I reached the maximum number of steps without finishing the task.",
            "steps": steps
        }

    def _parse_tool_call(self, content: str) -> Optional[Dict]:
        """
        Attempts to parse a JSON tool call from the LLM output.
        Returns dict if successful, None otherwise.
        """
        content = content.strip()
        # Simple heuristic: starts with { and contains tool_name
        if "{" in content and "tool_name" in content:
            try:
                # Extract JSON substring if there's extra text (though we asked for ONLY JSON)
                start = content.find("{")
                end = content.rfind("}") + 1
                json_str = content[start:end]
                data = json.loads(json_str)
                if "tool_name" in data and "arguments" in data:
                    return data
            except json.JSONDecodeError:
                pass
        return None
