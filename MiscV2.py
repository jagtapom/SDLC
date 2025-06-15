from nicegui import ui, app
import os, sys, json, logging, io
from pathlib import Path
from datetime import datetime
import docx, PyPDF2

# Add backend project root to path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from src.orchestrator import start_agent_workflow
from src.agents.user_agent import user_agent

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
        reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        return "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
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
    # Sidebar
    with ui.column().classes("w-1/4 bg-blue-900 text-white p-4 min-h-screen"):
        ui.image("https://upload.wikimedia.org/wikipedia/en/3/30/Barclays_logo.svg").style("width: 140px").classes("mb-6")
        ui.label("SDLC Wizard Steps").classes("text-lg font-bold mb-4 text-white")
        for step in steps:
            ui.label(step).classes("mb-2")

    # Main Content
    with ui.column().classes("w-3/4 p-8 bg-gray-50 min-h-screen"):
        ui.label("SDLC Automation Dashboard").classes("text-3xl text-blue-800 font-bold mb-6")

        # Upload Section
        with ui.card().classes("bg-white shadow-md p-6 mb-6"):
            ui.label("Upload Requirements File").classes("text-lg text-blue-600 mb-2")

            def handle_upload(e):
                file = e.name
                content = e.content.read()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"upload_{timestamp}.{file.split('.')[-1]}"
                input_dir = os.path.join(project_root, "input")
                os.makedirs(input_dir, exist_ok=True)
                file_path = os.path.join(input_dir, filename)

                try:
                    parsed_text = extract_text_from_file(content, file)
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(parsed_text)

                    state["uploaded_file_path"] = file_path
                    state["workflow_status"] = "uploaded"
                    ui.notify(f"✅ File uploaded and saved as: {filename}")
                    logger.info(f"Uploaded to: {file_path}")
                except Exception as ex:
                    ui.notify(f"❌ Failed to parse: {str(ex)}", type="negative")

            ui.upload(on_upload=handle_upload, label="Upload File", auto_upload=True).props('accept=".txt,.pdf,.docx"')
            ui.button("PROCESS REQUIREMENTS", on_click=lambda: process_requirements()).props('color="primary"').classes("mt-4")

        # Display JSON stories if generated
        if state["workflow_status"] == "stories_generated" and state["stories_file"]:
            stories_path = os.path.join(project_root, "stories", state["stories_file"])
            if os.path.exists(stories_path):
                with open(stories_path, 'r') as f:
                    stories = json.load(f)
                ui.label("Generated Stories").classes("text-xl font-semibold mt-4")
                ui.json(stories)

                if not state["stories_approved"]:
                    def approve_stories():
                        state["stories_approved"] = True
                        state["workflow_status"] = "stories_approved"
                        ui.notify("✅ Stories approved. Proceeding to JIRA creation...")
                        if state["chat_manager"]:
                            try:
                                user_agent.initiate_chat(
                                    state["chat_manager"],
                                    message="Stories approved. Please proceed with creating Jira tickets."
                                )
                                app.reload()
                            except Exception as e:
                                ui.notify(f"Error updating chat: {str(e)}", type="negative")
                    ui.button("Approve Stories", on_click=approve_stories).classes("mt-2")

        if state["workflow_status"] == "code_generated" and state["code_file"]:
            if os.path.exists(state["code_file"]):
                with open(state["code_file"], 'r') as f:
                    code = f.read()
                ui.label("Generated Program").classes("text-xl font-semibold mt-4")
                ui.code(code, language="python")

                if not state["code_approved"]:
                    def approve_code():
                        state["code_approved"] = True
                        state["workflow_status"] = "code_approved"
                        ui.notify("✅ Code approved. Workflow complete!")
                        if state["chat_manager"]:
                            try:
                                user_agent.initiate_chat(
                                    state["chat_manager"],
                                    message="Code approved. Workflow completed."
                                )
                                app.reload()
                            except Exception as e:
                                ui.notify(f"Error updating chat: {str(e)}", type="negative")
                    ui.button("Approve Code", on_click=approve_code).classes("mt-2")

        # Agent Output Debug Info
        with ui.card().classes("bg-white shadow-md p-6 mt-4"):
            ui.label("Agent Execution Log").classes("text-lg text-blue-600 mb-2")
            ui.label().bind_text_from(state, 'workflow_status', lambda v: f"Workflow Status: {v}")
            ui.label().bind_text_from(state, 'stories_file', lambda v: f"Stories File: {v or 'None'}")
            ui.label().bind_text_from(state, 'stories_approved', lambda v: f"Stories Approved: {v}")
            ui.label().bind_text_from(state, 'code_file', lambda v: f"Program File: {v or 'None'}")
            ui.label().bind_text_from(state, 'code_approved', lambda v: f"Code Approved: {v}")
            ui.label(f"Chat Manager: {'Active' if state['chat_manager'] else 'None'}")

def process_requirements():
    if state["workflow_status"] == "uploaded" and state["uploaded_file_path"]:
        try:
            ui.notify("🚀 Running Autogen Agent Pipeline...")
            logger.info(f"Starting pipeline with file: {state['uploaded_file_path']}")
            start_agent_workflow(state["uploaded_file_path"])
            app.reload()
        except Exception as e:
            ui.notify(f"❌ Error: {str(e)}", type="negative")

ui.run(title="SDLC Automation Dashboard", reload=True)
