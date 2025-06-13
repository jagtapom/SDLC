from nicegui import ui, app
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from autogen import GroupChat
from src.orchestrator import start_agent_workflow, custom_speaker_selection
from src.agents.user_agent import user_agent

# Global state (simulate session state)
state = {
    "workflow_status": "initial",
    "chat_manager": None,
    "uploaded_file_path": None,
    "stories_approved": False,
    "stories_file": None,
    "code_approved": False,
    "code_file": None
}

logger = logging.getLogger(__name__)

steps = [
    "1. Upload Requirement",
    "2. Generate User Stories",
    "3. HITL: Approve Stories",
    "4. Create JIRA Ticket",
    "5. Generate Code",
    "6. HITL: Approve Code",
    "7. Review Outputs"
]

completed_steps = set()

# Layout
with ui.row().classes("w-full"):
    with ui.column().classes("w-1/4 bg-blue-900 text-white p-4 min-h-screen"):
        ui.image("https://upload.wikimedia.org/wikipedia/en/3/30/Barclays_logo.svg").classes("mb-4").style("width: 120px")
        ui.label("SDLC Wizard Steps").classes("text-xl mb-4 text-blue-300")
        for i, step in enumerate(steps, 1):
            status_icon = "✅" if step in completed_steps else "🔄"
            ui.label(f"{status_icon} {step}").classes("text-white mb-1")

    with ui.column().classes("w-3/4 p-6 bg-white min-h-screen shadow-md"):
        ui.label("SDLC Automation Dashboard").classes("text-3xl text-primary mb-6 text-center")

        def handle_upload(e):
            file = e.name
            input_dir = os.path.join(project_root, "input")
            os.makedirs(input_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_filename = f"upload_{timestamp}.txt"
            file_path = os.path.join(input_dir, new_filename)
            with open(file_path, "wb") as f:
                f.write(e.content.read())
            state["uploaded_file_path"] = file_path
            ui.notify(f"File uploaded and saved as: {new_filename}")
            logger.info(f"Saved uploaded file to: {file_path}")

        ui.upload(on_upload=handle_upload, label="Upload Requirements File", auto_upload=True)

        def process_requirements():
            if state["workflow_status"] == "initial" and state["uploaded_file_path"]:
                try:
                    ui.notify("Processing requirements...")
                    logger.info(f"Processing file: {state['uploaded_file_path']}")
                    start_agent_workflow(state["uploaded_file_path"])
                    app.reload()  # force refresh
                except Exception as e:
                    ui.notify(f"Error: {str(e)}", type="negative")

        ui.button("Process Requirements", on_click=process_requirements)

        if state["workflow_status"] == "stories_generated" and state["stories_file"]:
            stories_path = os.path.join(project_root, "stories", state["stories_file"])
            if os.path.exists(stories_path):
                ui.label("Generated Stories").classes("text-xl font-semibold mt-4")
                with open(stories_path, 'r') as f:
                    stories = json.load(f)
                    ui.json(stories)

                if not state["stories_approved"]:
                    def approve_stories():
                        state["stories_approved"] = True
                        state["workflow_status"] = "stories_approved"
                        ui.notify("Stories approved! Creating Jira tickets...")

                        if state["chat_manager"]:
                            try:
                                user_agent.initiate_chat(
                                    state["chat_manager"],
                                    message="Stories approved. Please proceed with creating Jira tickets."
                                )
                                app.reload()
                            except Exception as e:
                                ui.notify(f"Error updating chat: {str(e)}", type="negative")

                    ui.button("Approve Stories", on_click=approve_stories)

        if state["workflow_status"] == "code_generated" and state["code_file"]:
            if os.path.exists(state["code_file"]):
                ui.label("Generated Program").classes("text-xl font-semibold mt-4")
                with open(state["code_file"], 'r') as f:
                    code = f.read()
                    ui.code(code, language="python")

                if not state["code_approved"]:
                    def approve_code():
                        state["code_approved"] = True
                        state["workflow_status"] = "code_approved"
                        ui.notify("Code approved! Workflow completed.")

                        if state["chat_manager"]:
                            try:
                                user_agent.initiate_chat(
                                    state["chat_manager"],
                                    message="Code approved. Workflow completed."
                                )
                                app.reload()
                            except Exception as e:
                                ui.notify(f"Error updating chat: {str(e)}", type="negative")

                    ui.button("Approve Code", on_click=approve_code)

ui.run(title="SDLC Automation Dashboard", reload=True)
