import os
import json
import subprocess
import sys
import platform
import threading
import tkinter as tk
from tkinter import scrolledtext, ttk, filedialog, messagebox
import google.generativeai as genai
from typing import List, Dict, Any, Optional, Union

# Configuration
GEMINI_API_KEY = "AIzaSyA2AHWSsfs1VgFfDggYzzJ6bpZITkVD67c"

class LocalAIAgentGUI:
    def __init__(self, root):
        """Initialize the GUI application."""
        self.root = root
        self.root.title("Local AI Agent")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # Set theme and style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Colors
        self.bg_color = "#f0f0f0"
        self.accent_color = "#4a86e8"
        self.text_color = "#333333"
        self.success_color = "#4caf50"
        self.error_color = "#f44336"
        
        # Setup styles
        self.style.configure("TFrame", background=self.bg_color)
        self.style.configure("TLabel", background=self.bg_color, foreground=self.text_color)
        self.style.configure("TButton", background=self.accent_color, foreground="white", padding=5)
        self.style.configure("Success.TButton", background=self.success_color, foreground="white", padding=5)
        self.style.configure("Error.TButton", background=self.error_color, foreground="white", padding=5)
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Setup API key section
        self.setup_api_section()
        
        # Task input section
        self.setup_task_section()
        
        # Output section
        self.setup_output_section()
        
        # Action buttons
        self.setup_action_buttons()
        
        # Status bar
        self.setup_status_bar()
        
        # Initialize agent
        self.agent = None
        self.current_plan = None
        self.platform = platform.system()
        
        # Show status
        self.set_status(f"Ready - Detected {self.platform} platform")

    def setup_api_section(self):
        """Setup the API key input section."""
        api_frame = ttk.LabelFrame(self.main_frame, text="API Configuration", padding="5")
        api_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(api_frame, text="Gemini API Key:").pack(side=tk.LEFT, padx=5)
        
        self.api_key_var = tk.StringVar(value=os.environ.get("GEMINI_API_KEY", GEMINI_API_KEY))
        self.api_key_entry = ttk.Entry(api_frame, textvariable=self.api_key_var, width=50)
        self.api_key_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.init_button = ttk.Button(api_frame, text="Initialize Agent", command=self.initialize_agent)
        self.init_button.pack(side=tk.RIGHT, padx=5)

    def setup_task_section(self):
        """Setup the task input section."""
        task_frame = ttk.LabelFrame(self.main_frame, text="Task", padding="5")
        task_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(task_frame, text="What task would you like me to perform?").pack(anchor=tk.W, padx=5, pady=2)
        
        self.task_input = scrolledtext.ScrolledText(task_frame, height=4, wrap=tk.WORD)
        self.task_input.pack(fill=tk.X, padx=5, pady=5)
        
        button_frame = ttk.Frame(task_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.generate_button = ttk.Button(button_frame, text="Generate Plan", command=self.generate_plan)
        self.generate_button.pack(side=tk.LEFT, padx=5)
        self.generate_button["state"] = "disabled"

    def setup_output_section(self):
        """Setup the output display section."""
        # Notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Plan tab
        self.plan_frame = ttk.Frame(self.notebook, padding="5")
        self.notebook.add(self.plan_frame, text="Plan")
        
        # Plan output
        ttk.Label(self.plan_frame, text="Generated Plan:").pack(anchor=tk.W, padx=5, pady=2)
        self.plan_output = scrolledtext.ScrolledText(self.plan_frame, height=10, wrap=tk.WORD)
        self.plan_output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Commands tab
        self.commands_frame = ttk.Frame(self.notebook, padding="5")
        self.notebook.add(self.commands_frame, text="Commands")
        
        # Commands output
        ttk.Label(self.commands_frame, text="Commands to Execute:").pack(anchor=tk.W, padx=5, pady=2)
        self.commands_output = scrolledtext.ScrolledText(self.commands_frame, height=10, wrap=tk.WORD)
        self.commands_output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Files tab
        self.files_frame = ttk.Frame(self.notebook, padding="5")
        self.notebook.add(self.files_frame, text="Files")
        
        # Files output
        ttk.Label(self.files_frame, text="Files to Create:").pack(anchor=tk.W, padx=5, pady=2)
        self.files_output = scrolledtext.ScrolledText(self.files_frame, height=10, wrap=tk.WORD)
        self.files_output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Execution log tab
        self.log_frame = ttk.Frame(self.notebook, padding="5")
        self.notebook.add(self.log_frame, text="Execution Log")
        
        # Log output
        self.log_output = scrolledtext.ScrolledText(self.log_frame, height=10, wrap=tk.WORD)
        self.log_output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def setup_action_buttons(self):
        """Setup action buttons."""
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        self.execute_button = ttk.Button(button_frame, text="Execute Plan", command=self.execute_plan)
        self.execute_button.pack(side=tk.LEFT, padx=5)
        self.execute_button["state"] = "disabled"
        
        self.abort_button = ttk.Button(button_frame, text="Abort", command=self.abort_execution)
        self.abort_button.pack(side=tk.LEFT, padx=5)
        self.abort_button["state"] = "disabled"
        
        self.feedback_button = ttk.Button(button_frame, text="Provide Feedback", command=self.open_feedback_dialog)
        self.feedback_button.pack(side=tk.LEFT, padx=5)
        self.feedback_button["state"] = "disabled"
        
        self.clear_button = ttk.Button(button_frame, text="Clear All", command=self.clear_all)
        self.clear_button.pack(side=tk.RIGHT, padx=5)

    def setup_status_bar(self):
        """Setup status bar."""
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def set_status(self, message, error=False):
        """Set status bar message."""
        self.status_var.set(message)
        if error:
            self.status_bar.config(foreground=self.error_color)
        else:
            self.status_bar.config(foreground=self.text_color)

    def log(self, message, tag=None):
        """Add message to log."""
        self.log_output.config(state=tk.NORMAL)
        if tag == "success":
            self.log_output.insert(tk.END, f"✅ {message}\n", "success")
            self.log_output.tag_config("success", foreground=self.success_color)
        elif tag == "error":
            self.log_output.insert(tk.END, f"❌ {message}\n", "error")
            self.log_output.tag_config("error", foreground=self.error_color)
        elif tag == "command":
            self.log_output.insert(tk.END, f"⚙️ {message}\n", "command")
            self.log_output.tag_config("command", foreground=self.accent_color)
        else:
            self.log_output.insert(tk.END, f"{message}\n")
        
        self.log_output.config(state=tk.DISABLED)
        self.log_output.see(tk.END)

    def initialize_agent(self):
        """Initialize the AI agent."""
        api_key = self.api_key_var.get().strip()
        
        if not api_key:
            messagebox.showerror("Error", "API Key cannot be empty")
            return
        
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            self.generate_button["state"] = "normal"
            self.set_status("✅ AI model initialized successfully")
            self.log("AI model initialized successfully", "success")
        except Exception as e:
            error_msg = f"Failed to initialize AI model: {e}"
            self.set_status(error_msg, error=True)
            self.log(error_msg, "error")
            messagebox.showerror("Initialization Error", error_msg)

    def generate_plan(self, feedback=None):
        """Generate a plan using the AI model."""
        task = self.task_input.get("1.0", tk.END).strip()
        
        if not task:
            messagebox.showerror("Error", "Task description cannot be empty")
            return
        
        # Disable buttons during generation
        self.generate_button["state"] = "disabled"
        self.set_status("🔄 Generating plan...")
        
        # Clear previous outputs
        self.plan_output.delete("1.0", tk.END)
        self.commands_output.delete("1.0", tk.END)
        self.files_output.delete("1.0", tk.END)
        
        # Run in a separate thread to prevent UI freeze
        threading.Thread(target=self._generate_plan_thread, args=(task, feedback), daemon=True).start()

    def _generate_plan_thread(self, task, feedback):
        """Thread function for plan generation."""
        context = f"Previous feedback: {feedback}\n" if feedback else ""
        
        # Platform-specific guidance
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
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Handle potential markdown code blocks in the response
            if "```json" in response_text:
                json_content = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_content = response_text.split("```")[1].strip()
            else:
                json_content = response_text
            
            plan = json.loads(json_content)
            self.current_plan = plan
            
            # Update UI in main thread
            self.root.after(0, self._update_plan_ui, plan)
            
        except Exception as e:
            error_msg = f"Error generating plan: {e}"
            self.root.after(0, lambda: self.set_status(error_msg, error=True))
            self.root.after(0, lambda: self.log(error_msg, "error"))
            self.root.after(0, lambda: messagebox.showerror("Generation Error", error_msg))
            self.root.after(0, lambda: self.generate_button.config(state="normal"))

    def _update_plan_ui(self, plan):
        """Update UI with generated plan."""
        # Update plan tab
        for i, step in enumerate(plan.get("plan", []), 1):
            self.plan_output.insert(tk.END, f"{i}. {step}\n\n")
        
        # Update commands tab
        for i, cmd in enumerate(plan.get("commands", []), 1):
            self.commands_output.insert(tk.END, f"{i}. {cmd}\n\n")
        
        # Update files tab
        for i, file_info in enumerate(plan.get("files", []), 1):
            path = file_info.get("path", "Unnamed file")
            content = file_info.get("content", "")
            
            self.files_output.insert(tk.END, f"File {i}: {path}\n")
            self.files_output.insert(tk.END, "-" * 50 + "\n")
            self.files_output.insert(tk.END, f"{content}\n\n")
            self.files_output.insert(tk.END, "=" * 50 + "\n\n")
        
        # Enable execution button
        self.execute_button["state"] = "normal"
        self.generate_button["state"] = "normal"
        
        # Switch to plan tab
        self.notebook.select(0)
        
        # Update status
        self.set_status("✅ Plan generated successfully")
        self.log("Plan generated successfully", "success")

    def execute_plan(self):
        """Execute the current plan."""
        if not self.current_plan:
            messagebox.showerror("Error", "No plan available to execute")
            return
        
        # Ask for confirmation
        if not messagebox.askyesno("Confirm Execution", 
                                  "Are you sure you want to execute this plan? "
                                  "This will create files and run commands on your system."):
            return
        
        # Disable buttons during execution
        self.execute_button["state"] = "disabled"
        self.generate_button["state"] = "disabled"
        self.abort_button["state"] = "normal"
        
        # Switch to log tab
        self.notebook.select(3)
        
        # Clear previous log
        self.log_output.config(state=tk.NORMAL)
        self.log_output.delete("1.0", tk.END)
        self.log_output.config(state=tk.DISABLED)
        
        # Start execution in a separate thread
        threading.Thread(target=self._execute_plan_thread, daemon=True).start()

    def _execute_plan_thread(self):
        """Thread function for plan execution."""
        try:
            # Create files first
            if self.current_plan.get("files"):
                self.root.after(0, lambda: self.set_status("🔄 Creating files..."))
                self.root.after(0, lambda: self.log("Creating files..."))
                
                for file_info in self.current_plan.get("files", []):
                    path = file_info.get("path", "")
                    content = file_info.get("content", "")
                    
                    try:
                        # Create directory if it doesn't exist
                        directory = os.path.dirname(path)
                        if directory and not os.path.exists(directory):
                            os.makedirs(directory)
                        
                        # Write file (with encoding for Windows)
                        with open(path, "w", encoding="utf-8") as f:
                            f.write(content)
                            
                        self.root.after(0, lambda p=path: self.log(f"Created file: {p}", "success"))
                    except Exception as e:
                        error_msg = f"Error creating file {path}: {e}"
                        self.root.after(0, lambda msg=error_msg: self.log(msg, "error"))
                        self.root.after(0, lambda msg=error_msg: self.set_status(msg, error=True))
                        self.root.after(0, self._finish_execution_with_error)
                        return
            
            # Execute commands
            if self.current_plan.get("commands"):
                self.root.after(0, lambda: self.set_status("🔄 Executing commands..."))
                
                for cmd in self.current_plan.get("commands", []):
                    self.root.after(0, lambda c=cmd: self.log(f"Executing: {c}", "command"))
                    
                    try:
                        # Execute the command with proper shell for the platform
                        if self.platform == "Windows":
                            # On Windows, ensure we use cmd.exe
                            process = subprocess.run(
                                cmd, 
                                shell=True, 
                                text=True, 
                                capture_output=True,
                                executable=None if 'powershell' in cmd.lower() else 'cmd.exe'
                            )
                        else:
                            # On Unix-like systems
                            process = subprocess.run(
                                cmd, 
                                shell=True, 
                                text=True, 
                                capture_output=True
                            )
                        
                        # Check if successful
                        if process.returncode == 0:
                            self.root.after(0, lambda: self.log("Command executed successfully", "success"))
                            if process.stdout:
                                self.root.after(0, lambda out=process.stdout: self.log(f"Output:\n{out}"))
                        else:
                            error_msg = f"Command failed with error code: {process.returncode}"
                            self.root.after(0, lambda msg=error_msg: self.log(msg, "error"))
                            if process.stderr:
                                self.root.after(0, lambda err=process.stderr: self.log(f"Error output:\n{err}", "error"))
                            self.root.after(0, self._finish_execution_with_error)
                            return
                    except Exception as e:
                        error_msg = f"Error executing command: {e}"
                        self.root.after(0, lambda msg=error_msg: self.log(msg, "error"))
                        self.root.after(0, lambda msg=error_msg: self.set_status(msg, error=True))
                        self.root.after(0, self._finish_execution_with_error)
                        return
            
            # Execution completed successfully
            self.root.after(0, lambda: self.set_status("✅ Plan executed successfully"))
            self.root.after(0, lambda: self.log("Plan executed successfully", "success"))
            self.root.after(0, self._finish_execution_success)
            
        except Exception as e:
            error_msg = f"Error during execution: {e}"
            self.root.after(0, lambda msg=error_msg: self.set_status(msg, error=True))
            self.root.after(0, lambda msg=error_msg: self.log(msg, "error"))
            self.root.after(0, self._finish_execution_with_error)

    def _finish_execution_success(self):
        """Handle successful execution completion."""
        self.execute_button["state"] = "disabled"
        self.generate_button["state"] = "normal"
        self.abort_button["state"] = "disabled"
        
        # Ask user if task was completed successfully
        if messagebox.askyesno("Task Completed", 
                              "Was the task completed successfully?"):
            messagebox.showinfo("Success", "Task completed successfully!")
        else:
            self.feedback_button["state"] = "normal"
            messagebox.showinfo("Feedback Needed", 
                              "Please provide feedback to refine the task.")

    def _finish_execution_with_error(self):
        """Handle execution failure."""
        self.execute_button["state"] = "disabled"
        self.generate_button["state"] = "normal"
        self.abort_button["state"] = "disabled"
        self.feedback_button["state"] = "normal"
        
        messagebox.showinfo("Execution Failed", 
                          "Execution failed. Please provide feedback to refine the task.")

    def abort_execution(self):
        """Abort the current execution."""
        # This is a simple implementation - in a real-world application,
        # you would need to properly terminate the subprocess
        messagebox.showinfo("Abort", "Aborting execution is not fully implemented in this version.")
        self.set_status("⚠️ Execution aborted by user")
        self.log("Execution aborted by user", "error")
        
        self.execute_button["state"] = "disabled"
        self.generate_button["state"] = "normal"
        self.abort_button["state"] = "disabled"

    def open_feedback_dialog(self):
        """Open dialog for user feedback."""
        feedback_dialog = tk.Toplevel(self.root)
        feedback_dialog.title("Provide Feedback")
        feedback_dialog.geometry("500x300")
        feedback_dialog.transient(self.root)
        feedback_dialog.grab_set()
        
        ttk.Label(feedback_dialog, text="What went wrong? Please provide details:").pack(anchor=tk.W, padx=10, pady=5)
        
        feedback_text = scrolledtext.ScrolledText(feedback_dialog, height=10, wrap=tk.WORD)
        feedback_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        button_frame = ttk.Frame(feedback_dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def submit_feedback():
            feedback = feedback_text.get("1.0", tk.END).strip()
            if feedback:
                feedback_dialog.destroy()
                self.generate_plan(feedback)
                self.feedback_button["state"] = "disabled"
        
        submit_button = ttk.Button(button_frame, text="Submit Feedback", command=submit_feedback)
        submit_button.pack(side=tk.RIGHT, padx=5)
        
        cancel_button = ttk.Button(button_frame, text="Cancel", command=feedback_dialog.destroy)
        cancel_button.pack(side=tk.RIGHT, padx=5)

    def clear_all(self):
        """Clear all inputs and outputs."""
        self.task_input.delete("1.0", tk.END)
        self.plan_output.delete("1.0", tk.END)
        self.commands_output.delete("1.0", tk.END)
        self.files_output.delete("1.0", tk.END)
        
        self.log_output.config(state=tk.NORMAL)
        self.log_output.delete("1.0", tk.END)
        self.log_output.config(state=tk.DISABLED)
        
        self.current_plan = None
        self.execute_button["state"] = "disabled"
        self.abort_button["state"] = "disabled"
        self.feedback_button["state"] = "disabled"
        
        self.set_status(f"Ready - Detected {self.platform} platform")

def main():
    """Main function to run the GUI."""
    root = tk.Tk()
    app = LocalAIAgentGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()