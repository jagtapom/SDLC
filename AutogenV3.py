from dash import Dash, html, dcc, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import base64
import io
import time
from concurrent.futures import ThreadPoolExecutor
import PyPDF2
import pandas as pd
from datetime import datetime
import os
from main import run_sdlc_pipeline  # Use actual Autogen logic from main.py

app = Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])
app.title = "SDLC Automation Dashboard"
executor = ThreadPoolExecutor(max_workers=2)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

status_flags = {
    "uploaded": None,
    "run_started": None,
    "run_done": None,
    "stories_approved": False,
    "code_approved": False,
    "jira_created": False,
    "jira_ticket": ""
}

result_files = {
    "stories": None,
    "code": None
}

agent_logs = []
result_store = {}

def extract_text_from_pdf(content):
    reader = PyPDF2.PdfReader(io.BytesIO(content))
    return "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])

def save_file(content, filename):
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, 'wb') as f:
        f.write(content)
    return filepath

def run_pipeline_async(task_id, text):
    try:
        result_store[task_id] = {"status": "running", "messages": []}
        result = run_sdlc_pipeline(text)  # Calls actual Autogen pipeline

        agent_logs.clear()
        now = datetime.now().strftime("%Y%m%d_%H%M%S")

        for step in result:
            name, content = step.get("name"), step.get("content")
            agent_logs.append(f"{name} Agent: {content[:60]}...")
            if "story" in name.lower():
                result_files["stories"] = f"stories_{now}.txt"
                with open(os.path.join(UPLOAD_DIR, result_files["stories"]), 'w') as f:
                    f.write(content)
                status_flags["stories_approved"] = True
            elif "code" in name.lower():
                result_files["code"] = f"code_{now}.py"
                with open(os.path.join(UPLOAD_DIR, result_files["code"]), 'w') as f:
                    f.write(content)
                status_flags["code_approved"] = True
            elif "jira" in name.lower():
                status_flags["jira_created"] = True
                status_flags["jira_ticket"] = content.strip()

        status_flags["run_done"] = True
        result_store[task_id]["status"] = "done"
    except Exception as e:
        result_store[task_id] = {"status": "error", "messages": str(e)}

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.Img(src="/assets/barclays_logo.png", style={"width": "80%", "marginBottom": "20px"}),
            html.H4("🧠 SDLC Wizard Steps", className="text-primary mb-3"),
            html.Ul([
                html.Li("1. Upload Requirement", className="text-light"),
                html.Li("2. Generate User Stories", className="text-light"),
                html.Li("3. HITL: Approve Stories", className="text-light"),
                html.Li("4. Create JIRA Ticket", className="text-light"),
                html.Li("5. Generate Code", className="text-light"),
                html.Li("6. HITL: Approve Code", className="text-light"),
                html.Li("7. Review Outputs", className="text-light")
            ]),
            html.Hr(),
            html.Div(id='debug-info', className="text-light small")
        ], width=3),
        dbc.Col([
            html.H2("SDLC Automation", className="text-center text-primary mb-4"),
            dbc.Breadcrumb(items=[
                {"label": "Home", "href": "#"},
                {"label": "Upload Requirement", "active": True}
            ], className="mb-4"),
            dbc.Card([
                dbc.CardHeader("Upload Requirements File"),
                dbc.CardBody([
                    dcc.Upload(
                        id='upload-data',
                        children=html.Div(['📂 Drag and drop file here or ', html.A('Browse files')]),
                        multiple=False,
                        style={
                            'border': '2px dashed #aaa',
                            'padding': '40px',
                            'textAlign': 'center',
                            'backgroundColor': '#222',
                            'color': '#ccc'
                        }
                    ),
                    html.Div(id='file-upload-status', className="mt-3 text-success"),
                    dbc.Button("Process Requirements", id='run-button', color='primary', className='mt-3')
                ])
            ]),
            html.Br(),
            dbc.Card([
                dbc.CardHeader("Agent Execution Log"),
                dbc.CardBody(html.Ul(id='agent-log', className="text-info small"))
            ])
        ], width=9)
    ]),
    dcc.Interval(id='poll-interval', interval=2000, n_intervals=0, disabled=True)
], fluid=True)

@app.callback(
    Output('file-upload-status', 'children'),
    Output('upload-data', 'filename'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    prevent_initial_call=True
)
def handle_upload(contents, filename):
    if contents and filename:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        filepath = save_file(decoded, f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        status_flags["uploaded"] = datetime.now()
        return f"File uploaded and saved as: {os.path.basename(filepath)}", filename
    return dash.no_update, dash.no_update

@app.callback(
    Output('poll-interval', 'disabled'),
    Output('debug-info', 'children'),
    Output('agent-log', 'children'),
    Input('run-button', 'n_clicks'),
    Input('poll-interval', 'n_intervals'),
    prevent_initial_call=True
)
def run_pipeline_or_poll(n_clicks, poll):
    trigger = ctx.triggered_id
    task_id = "task"
    if trigger == 'run-button':
        status_flags['run_started'] = datetime.now()
        status_flags['run_done'] = False
        executor.submit(run_pipeline_async, task_id, "sample input")
        return False, "Pipeline execution started...", []
    elif trigger == 'poll-interval':
        result = result_store.get(task_id)
        if not result:
            return False, "Waiting for task to start...", []
        if result['status'] == 'done':
            logs = [html.Li(log) for log in agent_logs]
            debug_lines = [
                f"Workflow Status: ✅ Completed",
                f"Stories File: {result_files['stories']}",
                f"Stories Approved: {status_flags['stories_approved']}",
                f"Program File: {os.path.join(UPLOAD_DIR, result_files['code'])}",
                f"Code Approved: {status_flags['code_approved']}",
                f"JIRA Ticket: {status_flags['jira_ticket']}"
            ]
            return True, html.Ul([html.Li(l) for l in debug_lines]), logs
        elif result['status'] == 'error':
            return True, f"❌ Error: {result['messages']}", [html.Li("Failure during processing")] 
        return False, "⏳ Still processing...", [html.Li("Running...")]
    return dash.no_update, dash.no_update, dash.no_update

if __name__ == '__main__':
    app.run_server(debug=True)
