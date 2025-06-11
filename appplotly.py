import dash
from dash import html, dcc, Input, Output, State, ctx
import os
import json
from datetime import datetime
from pathlib import Path
import logging

# External functions and modules
from autogen import GroupChat
from src.orchestrator import start_agent_workflow
from src.agents.user_agent import user_agent

# Logging setup
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# App and session state setup
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server

# Global path setup
project_root = str(Path(__file__).parent)
input_dir = os.path.join(project_root, "input")
stories_dir = os.path.join(project_root, "stories")
os.makedirs(input_dir, exist_ok=True)

# Wizard steps
wizard_steps = [
    "Upload Requirements",
    "Generated Stories",
    "Generated Code"
]

# Layout definition
app.layout = html.Div([
    dcc.Store(id='step'),
    dcc.Store(id='uploaded-file-path'),
    dcc.Store(id='stories-approved', data=False),
    dcc.Store(id='code-approved', data=False),
    dcc.Store(id='stories-file'),
    dcc.Store(id='code-file'),

    html.H1("SDLC Automation Workflow", style={"textAlign": "center"}),

    html.Div(id='breadcrumb'),

    html.Div(id='step-content'),

    html.Div([
        html.Button("Previous", id='prev-btn', n_clicks=0),
        html.Button("Next", id='next-btn', n_clicks=0),
    ], style={"marginTop": "20px", "textAlign": "center"})
])

# Breadcrumb component
@app.callback(
    Output('breadcrumb', 'children'),
    Input('step', 'data')
)
def update_breadcrumb(current_step):
    if current_step is None:
        current_step = 0
    return html.Div([
        html.Span(f"{i+1}. {step}" if i != current_step else html.B(f"{i+1}. {step}"),
                  style={"padding": "10px"})
        for i, step in enumerate(wizard_steps)
    ])

# Step content
@app.callback(
    Output('step-content', 'children'),
    Input('step', 'data'),
    State('uploaded-file-path', 'data'),
    State('stories-file', 'data'),
    State('stories-approved', 'data'),
    State('code-file', 'data'),
    State('code-approved', 'data')
)
def render_step_content(step, file_path, stories_file, stories_approved, code_file, code_approved):
    if step is None:
        step = 0

    if step == 0:
        return html.Div([
            dcc.Upload(
                id='upload-data',
                children=html.Div(['Drag and Drop or ', html.A('Select a .txt File')]),
                style={
                    'width': '100%', 'height': '60px', 'lineHeight': '60px',
                    'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px',
                    'textAlign': 'center', 'margin': '10px'
                },
                multiple=False
            ),
            html.Div(id='upload-status')
        ])

    elif step == 1 and stories_file:
        path = os.path.join(stories_dir, stories_file)
        if os.path.exists(path):
            with open(path, 'r') as f:
                stories = json.load(f)
            return html.Div([
                html.H3("Generated Stories"),
                html.Pre(json.dumps(stories, indent=2)),
                html.Button("Approve Stories", id='approve-stories-btn') if not stories_approved else html.Div("✅ Stories Approved")
            ])
    elif step == 2 and code_file:
        if os.path.exists(code_file):
            with open(code_file, 'r') as f:
                code = f.read()
            return html.Div([
                html.H3("Generated Code"),
                html.Pre(code),
                html.Button("Approve Code", id='approve-code-btn') if not code_approved else html.Div("✅ Code Approved")
            ])
    return html.Div("No content available.")

# Handle file upload
@app.callback(
    Output('uploaded-file-path', 'data'),
    Output('upload-status', 'children'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def handle_upload(contents, filename):
    if contents:
        content_type, content_string = contents.split(',')
        import base64
        decoded = base64.b64decode(content_string)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_name = f"upload_{timestamp}.txt"
        file_path = os.path.join(input_dir, saved_name)
        with open(file_path, "wb") as f:
            f.write(decoded)
        logger.info(f"File saved at: {file_path}")

        start_agent_workflow(file_path)
        return file_path, f"File '{filename}' uploaded and processed."
    return dash.no_update, ""

# Handle next and prev navigation
@app.callback(
    Output('step', 'data'),
    Input('next-btn', 'n_clicks'),
    Input('prev-btn', 'n_clicks'),
    State('step', 'data')
)
def navigate_steps(next_clicks, prev_clicks, current_step):
    if current_step is None:
        current_step = 0
    triggered = ctx.triggered_id
    if triggered == 'next-btn' and current_step < len(wizard_steps) - 1:
        current_step += 1
    elif triggered == 'prev-btn' and current_step > 0:
        current_step -= 1
    return current_step

# Approve story
@app.callback(
    Output('stories-approved', 'data'),
    Input('approve-stories-btn', 'n_clicks'),
    prevent_initial_call=True
)
def approve_stories(n):
    user_agent.initiate_chat(
        None,  # replace with actual chat manager
        message="Stories approved. Proceeding to Jira ticket creation."
    )
    return True

# Approve code
@app.callback(
    Output('code-approved', 'data'),
    Input('approve-code-btn', 'n_clicks'),
    prevent_initial_call=True
)
def approve_code(n):
    user_agent.initiate_chat(
        None,  # replace with actual chat manager
        message="Code approved. Workflow completed."
    )
    return True

if __name__ == '__main__':
    app.run_server(debug=True)
