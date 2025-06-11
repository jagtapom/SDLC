import dash
from dash import dcc, html, Input, Output, State, ctx
import os
from datetime import datetime
from pathlib import Path

from src.orchestrator import start_agent_workflow, update_group_chat

app = dash.Dash(__name__)
server = app.server

def debug_info_layout():
    return html.Div([
        html.H4("Debug Info:"),
        html.Div(id="workflow-status"),
        html.Div(id="stories-file"),
        html.Div(id="stories-approved"),
        html.Div(id="code-file"),
        html.Div(id="code-approved"),
        html.Div(id="chat-manager")
    ], style={"padding": "10px", "backgroundColor": "#222", "color": "white", "width": "25%", "float": "left"})

app.layout = html.Div([
    dcc.Store(id='workflow-status-store', data="initial"),
    dcc.Store(id='uploaded-file-path'),
    dcc.Store(id='stories-approved', data=False),
    dcc.Store(id='code-approved', data=False),
    dcc.Store(id='stories-file'),
    dcc.Store(id='code-file'),
    dcc.Store(id='chat-manager', data=False),
    dcc.Store(id='step', data=0),

    html.Div(debug_info_layout()),

    html.Div([
        html.H1("SDLC Automation Workflow", style={"textAlign": "center"}),
        html.Div(id='step-content'),
        html.Div([
            html.Button("Previous", id='prev-btn', n_clicks=0),
            html.Button("Next", id='next-btn', n_clicks=0),
        ], style={"marginTop": "20px", "textAlign": "center"})
    ], style={"marginLeft": "27%"})
])

# ----------- Step Wizard ------------
@app.callback(
    Output("step", "data"),
    Input("prev-btn", "n_clicks"),
    Input("next-btn", "n_clicks"),
    State("step", "data")
)
def update_step(prev, next_, current):
    if ctx.triggered_id == "prev-btn":
        return max(0, current - 1)
    elif ctx.triggered_id == "next-btn":
        return min(2, current + 1)
    return current

@app.callback(
    Output("step-content", "children"),
    Input("step", "data")
)
def display_step(step):
    if step == 0:
        return html.Div([
            html.H3("Step 1: Upload Requirements File"),
            dcc.Upload(id='file-upload', children=html.Div([
                'Drag and drop file here or click to upload'
            ]), style={'border': '2px dashed #ccc', 'padding': '20px'}),
            html.Button("Process Requirements", id="process-btn")
        ])
    elif step == 1:
        return html.Div([
            html.H3("Step 2: Generated Stories"),
            html.Div(id="show-stories"),
            html.Button("Approve Stories", id="approve-stories-btn")
        ])
    elif step == 2:
        return html.Div([
            html.H3("Step 3: Generated Code"),
            html.Div(id="show-code"),
            html.Button("Approve Code", id="approve-code-btn")
        ])

# ----------- File Upload Handler ------------
@app.callback(
    Output("uploaded-file-path", "data"),
    Input("file-upload", "contents"),
    State("file-upload", "filename")
)
def save_file(contents, filename):
    if contents is not None:
        input_dir = Path(__file__).resolve().parent.parent / "input"
        os.makedirs(input_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = input_dir / f"upload_{timestamp}.txt"
        with open(path, "w") as f:
            f.write(contents.split(",")[1])
        return str(path)
    return None

# ----------- Start Workflow ------------
@app.callback(
    Output("workflow-status-store", "data"),
    Input("process-btn", "n_clicks"),
    State("uploaded-file-path", "data"),
    prevent_initial_call=True
)
def run_workflow(n, file_path):
    if file_path:
        try:
            start_agent_workflow(file_path)
            return "stories_generated"
        except Exception as e:
            return f"error: {str(e)}"
    return "initial"

# ----------- Approve Stories ------------
@app.callback(
    Output("stories-approved", "data"),
    Output("workflow-status-store", "data"),
    Input("approve-stories-btn", "n_clicks"),
    prevent_initial_call=True
)
def approve_stories(n):
    try:
        update_group_chat("Stories approved. Please proceed with creating Jira tickets.")
        return True, "stories_approved"
    except Exception as e:
        return False, f"error: {str(e)}"

# ----------- Approve Code ------------
@app.callback(
    Output("code-approved", "data"),
    Output("workflow-status-store", "data"),
    Input("approve-code-btn", "n_clicks"),
    prevent_initial_call=True
)
def approve_code(n):
    try:
        update_group_chat("Code approved. Workflow completed.")
        return True, "code_approved"
    except Exception as e:
        return False, f"error: {str(e)}"

# ----------- Show Generated Stories ------------
@app.callback(
    Output("show-stories", "children"),
    Input("workflow-status-store", "data"),
    State("stories-file", "data")
)
def display_stories(status, stories_file):
    if status == "stories_generated" and stories_file:
        path = Path(__file__).resolve().parent.parent / "stories" / stories_file
        if path.exists():
            import json
            with open(path) as f:
                data = json.load(f)
            return html.Pre(json.dumps(data, indent=2))
    return "No stories available yet."

# ----------- Show Generated Code ------------
@app.callback(
    Output("show-code", "children"),
    Input("workflow-status-store", "data"),
    State("code-file", "data")
)
def display_code(status, code_file):
    if status == "code_generated" and code_file and os.path.exists(code_file):
        with open(code_file, 'r') as f:
            return html.Pre(f.read())
    return "No code generated yet."

# ----------- Debug Info Panel Updates ------------
@app.callback(Output("workflow-status", "children"), Input("workflow-status-store", "data"))
def update_status(status): return f"Workflow Status: {status}"

@app.callback(Output("stories-file", "children"), Input("stories-file", "data"))
def update_stories_file(val): return f"Stories File: {val or 'None'}"

@app.callback(Output("code-file", "children"), Input("code-file", "data"))
def update_code_file(val): return f"Program File: {val or 'None'}"

@app.callback(Output("stories-approved", "children"), Input("stories-approved", "data"))
def update_stories_flag(val): return f"Stories Approved: {val}"

@app.callback(Output("code-approved", "children"), Input("code-approved", "data"))
def update_code_flag(val): return f"Code Approved: {val}"

@app.callback(Output("chat-manager", "children"), Input("chat-manager", "data"))
def update_chat_flag(val): return f"Chat Manager: {'Active' if val else 'None'}"

# Run app
if __name__ == "__main__":
    app.run_server(debug=True, port=8051)
