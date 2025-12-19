import os
import sys
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown

from agent import ClinicalAgent

# Default key provided by user (in a real app, use env vars!)
DEFAULT_API_KEY = "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"

console = Console()

def main():
    parser = argparse.ArgumentParser(description="Clinical Workflow Agent")
    parser.add_argument("--dry-run", action="store_true", help="Run in dry-run mode (no actual booking)")
    parser.add_argument("--model", type=str, default="Qwen/Qwen2.5-72B-Instruct", help="Hugging Face model ID")
    args = parser.parse_args()

    # Get API Key
    api_key = os.environ.get("HF_API_KEY", DEFAULT_API_KEY)
    if not api_key:
        console.print("[bold red]Error:[/bold red] No Hugging Face API Key found. Please set HF_API_KEY environment variable.")
        sys.exit(1)

    console.print(Panel.fit("🏥 Clinical Workflow Agent POC", style="bold blue"))
    console.print(f"[dim]Model: {args.model}[/dim]")
    if args.dry_run:
        console.print("[bold yellow]⚠ DRY RUN MODE ENABLED[/bold yellow]")

    agent = ClinicalAgent(api_key=api_key, model=args.model, dry_run=args.dry_run)

    console.print("\n[bold green]Available Test Scenarios:[/bold green]")
    console.print("1. \"Schedule a cardiology follow-up for patient Ravi Kumar next week and check insurance eligibility\"")
    console.print("2. \"Check insurance for Linda Chen\"")
    console.print("3. \"Find available dermatology slots\"")
    
    console.print("\n[bold]Type 'exit' or 'quit' to stop.[/bold]\n")

    while True:
        user_input = Prompt.ask("[bold blue]User[/bold blue]")
        
        if user_input.lower() in ["exit", "quit"]:
            break
            
        if not user_input.strip():
            continue
            
        with console.status("[bold green]Agent is thinking...[/bold green]", spinner="dots"):
            response_data = agent.run(user_input)
            response = response_data["final_answer"]
            
        console.print(Panel(Markdown(response), title="Agent Response", style="bold white"))

if __name__ == "__main__":
    main()
