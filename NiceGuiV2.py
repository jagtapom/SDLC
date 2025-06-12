from nicegui import ui
import asyncio
from datetime import datetime

status_flags = {
    "uploaded": False,
    "stories_generated": False,
    "stories_approved": False,
    "jira_created": False,
    "code_generated": False,
    "code_approved": False,
    "outputs_reviewed": False
}

agent_logs = []
current_step = 1

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

# Wizard Side Panel
with ui.row():
    with ui.column().classes("w-1/4 bg-blue-900 text-white p-4") as sidebar:
        ui.image("https://upload.wikimedia.org/wikipedia/en/3/30/Barclays_logo.svg").classes("mb-4").style("width: 120px")
        ui.label("SDLC Wizard Steps").classes("text-xl mb-4 text-blue-300")
        wizard_list = ui.element('ul').classes('q-pl-none')
        for i, step in enumerate(steps, 1):
            status_icon = "✅" if i in completed_steps else "🔄" if i == current_step else "🔲"
            with wizard_list:
                with ui.element('li').classes('q-mb-xs').props('style="list-style:none;"'):
                    ui.label(f"{status_icon} {step}")
                ui.separator()

    # Main Panel
    with ui.column().classes("w-3/4 p-4") as main_panel:
        ui.label("SDLC Automation").classes("text-2xl text-blue-300 text-center mb-6")

        upload = ui.upload(on_upload=lambda e: handle_upload(e), auto_upload=True).props('accept=".pdf,.txt,.docx"')
        file_status = ui.label().classes("text-green-400 mt-2")
        run_button = ui.button("Process Requirements", on_click=lambda: trigger_pipeline()).classes("mt-4")

        ui.label("Agent Execution Log").classes("text-xl mt-6 text-blue-200")
        log_area = ui.column().classes("bg-gray-900 text-white p-3 rounded-lg text-sm")


async def trigger_pipeline():
    global current_step
    run_button.disable()
    agent_logs.clear()
    log_area.clear()

    current_step = 2
    await simulate_agent("Translator Agent", "Processed input and converted to English")
    status_flags["uploaded"] = True
    completed_steps.add(1)

    current_step = 3
    await simulate_agent("BA Agent", "Generated user stories")
    status_flags["stories_generated"] = True
    completed_steps.add(2)

    current_step = 4
    await simulate_hitl("Do you approve the user stories?")
    status_flags["stories_approved"] = True
    completed_steps.add(3)

    current_step = 5
    await simulate_agent("JIRA Agent", "Created ticket JIRA-12345")
    status_flags["jira_created"] = True
    completed_steps.add(4)

    current_step = 6
    await simulate_agent("CodeGen Agent", "Generated Python code for requirement")
    status_flags["code_generated"] = True
    completed_steps.add(5)

    current_step = 7
    await simulate_hitl("Do you approve the generated code?")
    status_flags["code_approved"] = True
    completed_steps.add(6)

    current_step = 8
    status_flags["outputs_reviewed"] = True
    completed_steps.add(7)

    log_area.clear()
    for msg in agent_logs:
        ui.label(msg).classes("text-white text-sm")

    ui.notify("✅ Pipeline completed successfully")


def handle_upload(e):
    file_status.set_text(f"Uploaded: {e.name}")
    status_flags["uploaded"] = True
    completed_steps.add(1)


async def simulate_agent(name, message):
    agent_logs.append(f"{name}: {message}")
    ui.label(f"{name}: {message}").classes("text-green-300")
    await asyncio.sleep(1.5)


async def simulate_hitl(prompt):
    result = None
    dialog = ui.dialog()
    with dialog:
        with ui.card():
            ui.label(prompt)
            with ui.row():
                ui.button("Yes", on_click=lambda: dialog.submit("Yes"))
                ui.button("No", on_click=lambda: dialog.submit("No"))
    result = await dialog
    if result == "No":
        ui.notify("Please revise before proceeding", color="negative")
        await simulate_hitl(prompt)


ui.run()
