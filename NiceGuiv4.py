from nicegui import ui, app
import os
import sys
import json
import logging
import io
from pathlib import Path
from datetime import datetime
import docx  # for .docx support
import PyPDF2  # for .pdf support

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

def extract_text_from_file(file_content: bytes, filename: str) -> str:
    ext = filename.split('.')[-1].lower()

    if ext == "txt":
        return file_content.decode('utf-8', errors='ignore')

    elif ext == "pdf":
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        return "\n".join([p.extract_text() for p in pdf_reader.pages if p.extract_text()])

    elif ext == "docx":
        doc = docx.Document(io.BytesIO(file_content))
        return "\n".join([para.text for para in doc.paragraphs])

    else:
        raise ValueError(f"Unsupported file type: {ext}")

# Debug Sidebar
with ui.column().classes('fixed right-0 top-0 m-4 bg-white shadow-lg p-4 rounded max-w-xs'):
    ui.label("Debug Info")
    ui.label().bind_text_from(state, 'workflow_status', lambda v: f"Workflow Status: {v}")
    ui.label().bind_text_from(state, 'stories_file', lambda v: f"Stories File: {v or 'None'}")
    ui.label().bind_text_from(state, 'stories_approved', lambda v: f"Stories Approved: {v}")
    ui.label().bind_text_from(state, 'code_file', lambda v: f"Program File: {v or 'None'}")
    ui.label().bind_text_from(state, 'code_approved', lambda v: f"Code Approved: {v}")
    ui.label(f"Chat Manager: {'Active' if state['chat_manager'] else 'None'}")

with ui.row().classes('m-4'):
    with ui.column().classes('w-2/3'):
        ui.label("SDLC Automation").classes("text-2xl font-bold mb-4")

        def handle_upload(e):
            file = e.name
            file_content = e.content.read()
            input_dir = os.path.join(project_root, "input")
            os.makedirs(input_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_filename = f"upload_{timestamp}.{file.split('.')[-1]}"
            file_path = os.path.join(input_dir, new_filename)

            try:
                extracted_text = extract_text_from_file(file_content, file)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(extracted_text)

                state["uploaded_file_path"] = file_path
                ui.notify(f"✅ File uploaded and saved as: {new_filename}")
                logger.info(f"Saved and parsed file to: {file_path}")
            except Exception as ex:
                ui.notify(f"❌ Failed to parse file: {str(ex)}", color="negative")

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
