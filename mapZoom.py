from flask import Flask, request, jsonify
import dash
from dash import html, dcc, Output, Input, State, ClientsideFunction, ALL
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import json
import os

# Initialise the Flask server
server = Flask(__name__)

# Initialise the Dash app with the Flask server
app = dash.Dash(__name__, server=server, external_stylesheets=[dbc.themes.BOOTSTRAP])

button_positions = {}

# Load existing buttons from JSON file
data_file = 'buttons_data.json'
if os.path.exists(data_file):
    with open(data_file, 'r') as f:
        button_data = json.load(f)
        button_positions = button_data

else:
    button_data = {}

# Create a Flask route to handle updates from JavaScript
@server.route('/update_button_positions', methods=['POST'])
def update_button_positions():
    global button_positions
    try:
        data = request.get_json()
        if data is None:
            return jsonify(success=False, error="No JSON data provided"), 400

        for button_id, new_data in data.items():
            # Ensure the new data has 'text' and 'additional_text' keys, even if they are empty
            if 'text' not in new_data:
                new_data['text'] = ""
            if 'additional_text' not in new_data:
                new_data['additional_text'] = ""

            # If the button already exists, update its position and size, but keep the text and additional_text
            if button_id in button_positions:
                # Preserve existing text and additional_text
                existing_data = button_positions[button_id]
                existing_data.update({
                    'x': new_data.get('x', existing_data.get('x')),
                    'y': new_data.get('y', existing_data.get('y')),
                    'width': new_data.get('width', existing_data.get('width')),
                    'height': new_data.get('height', existing_data.get('height')),
                    'text': new_data.get('text', existing_data.get('text')),
                    'additional_text': new_data.get('additional_text', existing_data.get('additional_text'))
                })
            else:
                # If the button does not exist, just add the new data
                button_positions[button_id] = new_data

        print(button_positions)
        return jsonify(success=True)
    except Exception as e:
        print(f"Error handling /update_button_positions: {e}")
        return jsonify(success=False, error=str(e)), 500


fig = go.Figure(go.Scattergeo())
fig.update_geos(
    showcountries=True,  # Show country borders
    showcoastlines=True,
    coastlinecolor="Black",
    projection_type="equirectangular",
    showland=True,
    landcolor="rgb(217, 217, 217)",
    lataxis_showgrid=False,
    lonaxis_showgrid=False,
)
fig.update_layout(
    margin={"r": 0, "t": 0, "l": 0, "b": 0},
    geo=dict(
        lataxis_range=[-60, 90],  # Limit latitude (approximate world bounds)
        lonaxis_range=[-180, 180],  # Limit longitude (approximate world bounds)
    )
)


# App layout
app.layout = html.Div([
    dcc.Tabs(id="view-tabs", value='map', children=[
        dcc.Tab(label='Map View', value='map'),
        dcc.Tab(label='List View', value='list'),
    ]),
    html.Div([
        dbc.Switch(
            id="edit-mode-toggle",
            label="Edit Mode",
            value=False,  # Start with Edit Mode off
            className="mb-3"
        ),
    ], style={"display": "flex", "align-items": "center", "margin-bottom": "20px"}),

    html.Div(id='map-view', children=[
        html.Button("Create Button", id="create-button", n_clicks=0, className="ml-3 btn btn-primary"),
        html.Button("Save Positions", id="print-positions-btn", n_clicks=0, className="ml-3 btn btn-primary"),

        dcc.Graph(
            id="world-map",
            figure=fig,
            style={"width": "100%", "height": "80vh"},
            config={"scrollZoom": True}
        ),

        html.Div(
            id="button-container",
            style={
                "position": "relative",
                "width": "100%",
                "height": "80vh",
                "top": "-80vh",
                "z-index": 10
            },
            children=[
                html.Button(
                    f"{button_data[btn_id]['text']}",
                    id={'type': 'dynamic-button', 'index': btn_id},
                    className="draggable-button btn btn-primary",
                    **{
                        'data-id': btn_id
                    },
                    style={
                        "position": "absolute",
                        "top": f"{button_data[btn_id]['y']}px",
                        "left": f"{button_data[btn_id]['x']}px",
                        "width": f"{button_data[btn_id]['width']}px",
                        "height": f"{button_data[btn_id]['height']}px",
                        "background-color": "lightblue"
                    }
                ) for btn_id in button_data
            ]
        ),
    ]),
    html.Div(id='list-view', style={'display': 'none'}, children=[
        html.H2("List of Buttons"),
        html.Ul(id="button-list")
    ]),
    dcc.Input(id='update-store-trigger', type='hidden', value="5"),

    dcc.Store(id='button-positions-store', data={}),
    dcc.Store(id='temp-store', data={}),

    html.Div(id="dummy", style={"display": "none"}),

    dcc.Store(id="current-button-id", data=None),

    # Store to hold the text of each button
    dcc.Store(id="button-text-store", data={btn_id: button_data[btn_id]['text'] for btn_id in button_data}),

    dcc.Store(id="additional-text-store",
              data={btn_id: button_data[btn_id]['additional_text'] for btn_id in button_data}),

    html.Div(id='output-container', style={'display': 'none'}),

    dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Edit Button Text")),
            dbc.ModalBody([
                dcc.Textarea(id="textarea", style={"width": "100%", "height": "50px"}, placeholder="Button Label"),
                dcc.Textarea(id="additional-textarea", style={"width": "100%", "height": "100px"},
                             placeholder="Additional Information")
            ]),
            dbc.ModalFooter([
                dbc.Button("Save", id="save-button", className="ms-auto"),
                dbc.Button("Delete", id="delete-button", className="ms-auto", color="danger")  # Add Delete button
            ])
        ],
        id="modal",
        is_open=False,
    )
])


def save_buttons_to_json(buttons_data):
    with open(data_file, 'w') as f:
        json.dump(buttons_data, f)


# Combined callback for handling everything
@app.callback(
    [Output("modal", "is_open"), Output("textarea", "value"), Output("additional-textarea", "value"),
     Output("current-button-id", "data"), Output("button-container", "children"), Output("button-text-store", "data"),
     Output("additional-text-store", "data")],
    [Input({'type': 'dynamic-button', 'index': ALL}, 'n_clicks'), Input("save-button", "n_clicks"),
     Input("delete-button", "n_clicks"), Input("create-button", "n_clicks")],
    [State("edit-mode-toggle", "value"), State("modal", "is_open"), State("textarea", "value"),
     State("additional-textarea", "value"), State("current-button-id", "data"), State("button-container", "children"),
     State("button-text-store", "data"), State("additional-text-store", "data")]
)
def manage_modal_and_buttons(n_clicks, save_n_clicks, delete_n_clicks, create_n_clicks, edit_mode, is_open, new_text,
                             additional_text, button_id, children, text_store, additional_store):
    ctx = dash.callback_context

    # For button creation
    if ctx.triggered and "create-button.n_clicks" in ctx.triggered[0]['prop_id']:
        if children is None:
            children = []
        button_counter = len(button_positions)

        # Increment counter
        button_counter += 1

        new_button_id = button_counter
        # Create a unique data-id for each new button
        new_button = html.Button(
            f"Drag/Resize {new_button_id}",
            id={'type': 'dynamic-button', 'index': new_button_id},
            className="draggable-button",
            **{
                'data-id': f"dynamic-button-{new_button_id}"
            },
            style={
                "position": "absolute",
                "top": f"{new_button_id * 50}px",
                "left": "50px",
                "width": "100px",
                "height": "50px",
                "background-color": "lightblue"
            }
        )
        children.append(new_button)
        return is_open, "", "", None, children, text_store, additional_store

    # For opening the button for editing
    if ctx.triggered and any("dynamic-button" in trigger['prop_id'] for trigger in ctx.triggered):
        if edit_mode:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            index = eval(button_id)['index']  # Directly use the index without converting to int
            saved_text = text_store.get(str(index), f"Drag/Resize {index}")
            saved_additional_text = additional_store.get(str(index), "")
            return True, saved_text, saved_additional_text, index, children, text_store, additional_store

    # For saving text to the correct button and closing the modal
    if ctx.triggered and "save-button.n_clicks" in ctx.triggered[0]['prop_id']:
        if button_id is not None:
            # Ensure the key is in the correct format
            temp = str(button_id)
            if not temp.startswith("dynamic-button-"):
                position_key = f"dynamic-button-{temp}"
            else:
                position_key = temp
            for i, child in enumerate(children):
                if child['props']['id']['index'] == button_id:
                    children[i]['props']['children'] = new_text
                    # Save the text and additional info in the stores
                    text_store[str(button_id)] = new_text
                    additional_store[str(button_id)] = additional_text
                    # Retrieve position and size from the positions store
                    # position_key = f"dynamic-button-{button_id}"
                    button_positions[position_key]["text"] = new_text
                    button_positions[position_key]["additional_text"] = additional_text
            print(button_positions)

            return False, "", "", None, children, text_store, additional_store

    # for deleting the button
    if ctx.triggered and "delete-button.n_clicks" in ctx.triggered[0]['prop_id']:
        if button_id is not None:
            # Remove the button from the children
            children = [child for child in children if child['props']['id']['index'] != button_id]
            # Remove the button's data from the stores and JSON
            text_store.pop(str(button_id), None)
            additional_store.pop(str(button_id), None)
            position_key = f"dynamic-button-{button_id}"
            button_positions.pop(position_key, None)

            button_data.pop(str(button_id), None)
            print(button_positions)
            return False, "", "", None, children, text_store, additional_store

    return is_open, "", "", None, children, text_store, additional_store




@app.callback(
    Output('output-container', 'children'),
)
def print_positions(n_clicks):
    if n_clicks > 0:  # Ensure the button has been clicked at least once
        print("Updated Button Positions:")
        print(button_positions)
        save_buttons_to_json(button_positions)
    return ""  # No visible output necessary


@app.callback(
    [Output('map-view', 'style'), Output('list-view', 'style')],
    [Input('view-tabs', 'value')]
)
def toggle_view(selected_view):
    if selected_view == 'map':
        return {'display': 'block'}, {'display': 'none'}
    else:
        return {'display': 'none'}, {'display': 'block'}

@app.callback(
    Output('button-list', 'children'),
    Input('view-tabs', 'value')
)
def update_list_view(selected_view):
    if selected_view == 'list':
        items = [
            html.Li(f"{button_data['text']} - {button_data['additional_text']}")
            for btn_id, button_data in button_positions.items()
        ]
        return items
    return []


#  JavaScript to make the buttons draggable and resizable
app.clientside_callback(
    ClientsideFunction(namespace="clientside", function_name="make_draggable"),
    Output('dummy', 'children'),
    Input('button-container', 'children')
)

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
