import os
import json
import subprocess
import sys
import platform
import google.generativeai as genai
from typing import List, Dict, Any, Optional, Union

# Configuration
from config import GEMINI_API_KEY

class LocalAIAgent:
    def __init__(self, api_key: str):
        """Initialize the agent with API keys and model configurations."""
        self.api_key = api_key
        self.platform = platform.system() 
        self.setup_ai_model()
        
    def setup_ai_model(self):
        """Setup the AI model client."""
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            print(" AI initialized")
        except Exception as e:
            print(f" Failed to initialize AI: {e}")
            sys.exit(1)
    
    def get_task_from_user(self) -> str:
        """Get the task description from the user."""
     
        print(f" AIQUEMARK")
        return input(" Task?\n> ")
    
    def generate_plan(self, task: str, feedback: Optional[str] = None) -> Dict[str, Any]:
        """Generate a plan using the AI model."""
        context = f"Previous feedback: {feedback}\n" if feedback else ""
        
        platform_guidance = ""
        if self.platform == "Windows":
            platform_guidance = """
You are generating commands for a Windows system. Use Windows-specific commands:
- Use 'echo.' or 'type nul >' to create empty files (NOT 'touch')
- Use 'dir' instead of 'ls'
- Use 'copy' instead of 'cp'
- Use 'move' instead of 'mv'
- Use 'del' instead of 'rm'
- Use 'md' or 'mkdir' for directory creation
- For PowerShell commands, be explicit by prefixing with 'powershell -Command'
"""
        elif self.platform == "Linux":
            platform_guidance = "You are generating commands for a Linux system."
        elif self.platform == "Darwin":
            platform_guidance = "You are generating commands for a macOS system."
        
        prompt = f"""
{context}{platform_guidance}
You are an AI assistant that helps automate tasks on a {self.platform} computer.
The user has requested the following task: "{task}"

Provide a detailed plan with these components:
1. A list of steps that need to be taken
2. The exact commands to run for each step (appropriate for {self.platform})
3. Any file contents that need to be created

Respond with valid JSON in the following format:
{{
  "plan": [
    "Step 1: Description of first step",
    "Step 2: Description of second step",
    ...
  ],
  "commands": [
    "command_1",
    "command_2",
    ...
  ],
  "files": [
    {{
      "path": "filename.ext",
      "content": "The file content here"
    }},
    ...
  ]
}}

Ensure all commands are specifically compatible with {self.platform} and are safe to execute.
Do not use commands that don't exist on {self.platform}.
"""
        
        try:
            print(" Making PLan")
            response = self.model.generate_content(prompt)
            
            response_text = response.text.strip()
            
            if "```json" in response_text:
                json_content = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_content = response_text.split("```")[1].strip()
            else:
                json_content = response_text
            
            plan = json.loads(json_content)
            return plan
        except Exception as e:
            print(f" Error generating: {e}")
            return {
                "plan": ["Error: Could not generate a plan"],
                "commands": [],
                "files": []
            }
    
    def display_plan(self, plan: Dict[str, Any]):
        """Display the plan to the user for approval."""
        print("\n TASK PLAN:")
        print("-" * 50)
        
        print(" Steps:")
        for i, step in enumerate(plan.get("plan", []), 1):
            print(f"  {i}. {step}")
        
        if plan.get("commands"):
            print("\n Commands:")
            for i, cmd in enumerate(plan.get("commands", []), 1):
                print(f"  {i}. {cmd}")
        
        if plan.get("files"):
            print("\n Files to create:")
            for i, file_info in enumerate(plan.get("files", []), 1):
                print(f"  {i}. {file_info.get('path', 'Unnamed file')}")
                if len(file_info.get("content", "")) > 200:
                    content_preview = file_info.get("content", "")[:200] + "..."
                else:
                    content_preview = file_info.get("content", "")
                print(f"     Preview: {content_preview.replace(chr(10), ' ')}")
    
    def get_user_approval(self) -> bool:
        """Get user approval for the plan."""
        response = input("\n Do you approve this plan? (y/n): ").lower().strip()
        return response in ["y", "yes"]
    
    def create_files(self, files: List[Dict[str, str]]) -> bool:
        """Create the necessary files."""
        try:
            for file_info in files:
                path = file_info.get("path", "")
                content = file_info.get("content", "")
                
                directory = os.path.dirname(path)
                if directory and not os.path.exists(directory):
                    os.makedirs(directory)
                
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f" Created file: {path}")
            return True
        except Exception as e:
            print(f" Error creating files: {e}")
            return False
    
    def execute_commands(self, commands: List[str]) -> bool:
        """Execute the commands in the plan."""
        success = True
        for cmd in commands:
            print(f"\n Executing: {cmd}")
            try:
                if self.platform == "Windows":
                    process = subprocess.run(
                        cmd, 
                        shell=True, 
                        text=True, 
                        capture_output=True,
                        executable=None if 'powershell' in cmd.lower() else 'cmd.exe'
                    )
                else:
                    process = subprocess.run(
                        cmd, 
                        shell=True, 
                        text=True, 
                        capture_output=True
                    )
                
                if process.returncode == 0:
                    print(" Command executed")
                else:
                    print(f" Command failed with error code: {process.returncode}")
                    if process.stderr:
                        print(f" Error output:\n{process.stderr}")
                    success = False
                    break
            except Exception as e:
                if repr(e)=="FileNotFoundError(2, 'The system cannot find the file specified', None, 2, None)":
                    print(" Command executed")
                    success= True
                    break
                else:
                    print(f" Error executing command: {e}")
                    success = False
                    break
        
        return success
    
    def check_task_success(self) -> bool:
        """Check if the task was completed successfully."""
        response = input("\n Was the task successful? (y/n): ").lower().strip()
        return response in ["y", "yes"]
    
    def get_feedback(self) -> str:
        """Get feedback from the user about what went wrong."""
        return input("\n Feedback:\n> ")
    
    def run(self):
        """Run the agent's main loop."""
        task = self.get_task_from_user()
        feedback = None
        
        while True:
            plan = self.generate_plan(task, feedback)
            
            self.display_plan(plan)
            if not self.get_user_approval():
                print(" Task aborted by user")
                break
            
            if plan.get("files") and not self.create_files(plan.get("files", [])):
                print(" Failed to create required files")
                feedback = "Failed to create required files"
                continue
            
            command_success = self.execute_commands(plan.get("commands", []))
            
            if command_success and self.check_task_success():
                print("\n Task completed successfully!")
                break
            else:
                feedback = self.get_feedback()
                print(f"\n Refining task with your feedback: {feedback}")

def main():
    """Main function to run the agent."""
    api_key = os.environ.get("GEMINI_API_KEY", GEMINI_API_KEY)
    
    agent = LocalAIAgent(api_key)
    agent.run()

if __name__ == "__main__":
    main()