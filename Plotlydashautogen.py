from dash import Dash, html, dcc, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import base64
import io
import time
from concurrent.futures import ThreadPoolExecutor
import PyPDF2
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

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

def extract_text_from_pdf(content):
    reader = PyPDF2.PdfReader(io.BytesIO(content))
    return "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])

def save_file(content, filename):
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, 'wb') as f:
        f.write(content)
    return filepath

def run_sdlc_pipeline(text):
    agent_logs.clear()
    time.sleep(1)
    agent_logs.append("Translator Agent: Processed input and converted to English.")
    time.sleep(1)
    agent_logs.append("BA Agent: Created user stories from input.")
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_files["stories"] = f"stories_upload_{now}.txt"
    with open(os.path.join(UPLOAD_DIR, result_files["stories"]), 'w') as f:
        f.write("User Story: As a user, I want to extract data.")
    status_flags["stories_approved"] = True
    time.sleep(1)
    agent_logs.append("CodeGen Agent: Generated Python code for requirement.")
    result_files["code"] = f"program_{now}.py"
    with open(os.path.join(UPLOAD_DIR, result_files["code"]), 'w') as f:
        f.write("def factorial(n): return 1 if n==0 else n*factorial(n-1)")
    status_flags["code_approved"] = True
    time.sleep(1)
    status_flags["jira_created"] = True
    status_flags["jira_ticket"] = "JIRA-12345"
    agent_logs.append("JIRA Agent: Created ticket JIRA-12345 in backlog.")
    status_flags["run_done"] = True

app.layout = dbc.Container([
    dbc.Row([
        # Left Sidebar
        dbc.Col([
            html.H4("🧠 SDLC Wizard Steps", className="text-info mb-3"),
            html.Ul([
                html.Li("1. Upload Requirement", className="text-light"),
                html.Li("2. Generate User Stories", className="text-light"),
                html.Li("3. HITL: Approve Stories", className="text-light"),
                html.Li("4. Generate Code", className="text-light"),
                html.Li("5. HITL: Approve Code", className="text-light"),
                html.Li("6. Create JIRA Ticket", className="text-light"),
                html.Li("7. Review Outputs", className="text-light")
            ]),
            html.Hr(),
            html.Div(id='debug-info', className="text-light small")
        ], width=3),

        # Right Main Area
        dbc.Col([
            html.H2("SDLC Automation", className="text-center text-light mb-4"),

            dbc.Breadcrumb(items=[
                {"label": "Home", "href": "#"},
                {"label": "Upload Requirement", "active": True}
            ], className="mb-4"),

            dbc.Card([
                dbc.CardHeader("Upload Requirements File"),
                dbc.CardBody([
                    dcc.Upload(
                        id='upload-data',
                        children=html.Div([
                            '📂 Drag and drop file here or ',
                            html.A('Browse files')
                        ]),
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

    # Polling for agent status updates
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
    if trigger == 'run-button':
        status_flags['run_started'] = datetime.now()
        status_flags['run_done'] = False
        executor.submit(run_sdlc_pipeline, "sample input")
        return False, "Pipeline execution started...", []
    elif trigger == 'poll-interval':
        if status_flags['run_done']:
            logs = [html.Li(log) for log in agent_logs]
            debug_lines = [
                f"Workflow Status: code1_approved",
                f"Stories File: {result_files['stories']}",
                f"Stories Approved: {status_flags['stories_approved']}",
                f"Program File: {os.path.join(UPLOAD_DIR, result_files['code'])}",
                f"Code Approved: {status_flags['code_approved']}",
                f"JIRA Ticket: {status_flags['jira_ticket']}",
                f"Chat Manager: Active"
            ]
            return True, html.Ul([html.Li(l) for l in debug_lines]), logs
        return False, "⏳ Processing...", [html.Li("Waiting for results...")]
    return dash.no_update, dash.no_update, dash.no_update

if __name__ == '__main__':
    app.run_server(debug=True)
