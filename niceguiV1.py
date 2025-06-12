from nicegui import ui
import os
import base64
from datetime import datetime

UPLOAD_DIR = 'uploads'
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Global state
agent_logs = []
status_flags = {
    'uploaded': False,
    'run_started': False,
    'run_done': False,
    'stories_approved': False,
    'code_approved': False,
    'jira_created': False,
    'jira_ticket': '',
}
result_files = {
    'stories': '',
    'code': ''
}

# Wizard Step Display
steps = [
    "1. Upload Requirement",
    "2. Generate User Stories",
    "3. HITL: Approve Stories",
    "4. Create JIRA Ticket",
    "5. Generate Code",
    "6. HITL: Approve Code",
    "7. Review Outputs",
]

current_step = 0

@ui.page('/')
def main_page():
    global current_step

    with ui.row().classes('w-full'):

        # Left panel
        with ui.column().classes('w-1/4 q-pa-md'):
            ui.label('🧠 SDLC Wizard Steps').classes('text-h6 text-primary')
            wizard_list = ui.element('ul').classes('text-white')
            for i, step in enumerate(steps):
                status_icon = '✅' if i < current_step else ('🔵' if i == current_step else '⬜')
                ui.element('li').classes('q-mb-xs').text(f"{status_icon} {step}").props('style="list-style:none;"').parent = wizard_list
            ui.separator()
            debug_info = ui.label().classes('text-subtitle2 text-grey-4')

        # Right panel
        with ui.column().classes('w-3/4 q-pa-md'):
            ui.label('SDLC Automation').classes('text-h4 text-primary')
            ui.separator()

            file_label = ui.label().classes('text-green')

            file_upload = ui.upload(on_upload=lambda e: handle_upload(e, file_label), label='📂 Upload Requirements File')
            file_upload.props('accept=".txt,.pdf"')

            ui.button('🚀 Process Requirements', on_click=start_pipeline, color='primary')

            log_display = ui.column().classes('q-pa-md bg-dark text-blue-3 rounded-borders')
            for log in agent_logs:
                ui.label(log).classes('text-caption').parent = log_display

            # Debug Section
            def update_debug():
                debug_info.text = f"Stories File: {result_files['stories']} | Code File: {result_files['code']} | JIRA: {status_flags['jira_ticket']}"
            ui.timer(2.0, lambda: refresh_logs(log_display, update_debug))

def handle_upload(e, label):
    content = e.content
    filename = e.name
    filepath = os.path.join(UPLOAD_DIR, f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}")
    with open(filepath, 'wb') as f:
        f.write(content)
    label.text = f"📁 Uploaded: {filename}"
    status_flags['uploaded'] = True


def start_pipeline():
    global current_step
    agent_logs.clear()
    status_flags.update({
        'run_started': True,
        'run_done': False,
        'stories_approved': False,
        'code_approved': False,
        'jira_created': False,
        'jira_ticket': '',
    })

    # Simulate pipeline
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    agent_logs.append("Translator Agent: Processed input and translated.")
    agent_logs.append("BA Agent: Created user stories.")
    result_files['stories'] = f"stories_{now}.txt"
    open(os.path.join(UPLOAD_DIR, result_files['stories']), 'w').write("User Story: Extract data.")
    status_flags['stories_approved'] = True

    current_step = 4

    agent_logs.append("JIRA Agent: Created ticket JIRA-4321.")
    status_flags['jira_ticket'] = 'JIRA-4321'
    status_flags['jira_created'] = True

    agent_logs.append("CodeGen Agent: Generated Python code.")
    result_files['code'] = f"program_{now}.py"
    open(os.path.join(UPLOAD_DIR, result_files['code']), 'w').write("def run(): pass")
    status_flags['code_approved'] = True

    current_step = 7
    status_flags['run_done'] = True


def refresh_logs(display, update_debug):
    display.clear()
    for log in agent_logs:
        ui.label(log).classes('text-caption').parent = display
    update_debug()

ui.run()
