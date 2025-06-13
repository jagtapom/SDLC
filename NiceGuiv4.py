from nicegui import ui, app
import os
import sys
import json
import logging
import io
from pathlib import Path
from datetime import datetime
import docx
import PyPDF2

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

steps = [
    "1. Upload Requirement",
    "2. Generate User Stories",
    "3. HITL: Approve Stories",
    "4. Create JIRA Ticket",
    "5. Generate Code",
    "6. HITL: Approve Code",
    "7. Review Outputs"
]

with ui.row().classes("w-full"):
    # Sidebar with steps and logo
    with ui.column().classes("w-1/4 bg-blue-900 text-white p-4 min-h-screen"):
        ui.image("https://upload.wikimedia.org/wikipedia/en/3/30/Barclays_logo.svg").classes("mb-4").style("width: 140px")
        ui.label("SDLC Wizard Steps").classes("text-xl mb-4 text-white")
        for step in steps:
            ui.label(step).classes("text-white mb-2")

    # Main content area
    with ui.column().classes("w-3/4 p-8 bg-gray-50 min-h-screen"):
        ui.label("SDLC Automation Dashboard").classes("text-3xl text-blue-800 font-bold mb-6")

        with ui.card().classes("bg-white shadow-md p-6 mb-6"):
            ui.label("Upload Requirements File").classes("text-lg text-blue-600 mb-2")
            upload = ui.upload(on_upload=lambda e: handle_upload(e), auto_upload=True).props('accept=".pdf,.txt,.docx"')
            ui.button("PROCESS REQUIREMENTS", on_click=lambda: process_requirements()).props('color="primary"').classes("mt-4")

        with ui.card().classes("bg-white shadow-md p-6"):
            ui.label("Agent Execution Log").classes("text-lg text-blue-600 mb-2")
            ui.label().bind_text_from(state, 'workflow_status', lambda v: f"Workflow Status: {v}")
            ui.label().bind_text_from(state, 'stories_file', lambda v: f"Stories File: {v or 'None'}")
            ui.label().bind_text_from(state, 'stories_approved', lambda v: f"Stories Approved: {v}")
            ui.label().bind_text_from(state, 'code_file', lambda v: f"Program File: {v or 'None'}")
            ui.label().bind_text_from(state, 'code_approved', lambda v: f"Code Approved: {v}")
            ui.label(f"Chat Manager: {'Active' if state['chat_manager'] else 'None'}")

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

def process_requirements():
    if state["workflow_status"] == "initial" and state["uploaded_file_path"]:
        try:
            ui.notify("Processing requirements...")
            logger.info(f"Processing file: {state['uploaded_file_path']}")
            start_agent_workflow(state["uploaded_file_path"])
            app.reload()  # force refresh
        except Exception as e:
            ui.notify(f"Error: {str(e)}", type="negative")

ui.run(title="SDLC Automation Dashboard", reload=True)
