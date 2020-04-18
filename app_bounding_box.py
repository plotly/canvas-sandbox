import dash
from dash.dependencies import Input, Output, State
import dash_html_components as html
import dash_core_components as dcc
from glob import glob
import numpy as np
from utils import make_figure, path_to_indices
import plotly.graph_objects as go
import os

print("we are in", os.getcwd())
print(os.listdir())

color_dict = {'car':'blue', 'truck':'red', 'building':'yellow', 'tree':'green'}
options = ['car', 'truck', 'building', 'tree']

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

filelist = [app.get_asset_url('driving.jpg'),
            app.get_asset_url('professional-transport-autos-bridge-traffic-road-rush-hour.jpg'),
            app.get_asset_url('rocket.jpg')]

server = app.server

fig = make_figure(filelist[0], mode='layout')
fig['layout']['newshape']['line']['color'] = color_dict['car']

app.layout=html.Div(
        [
        html.H4("Draw bounding boxes around objects"),
        dcc.Graph(id='graph', figure=fig),
        dcc.Store(id='graph-copy', data=fig),
        dcc.Store(id='annotations-store', 
            data={filename:{'shapes':[]} for filename in filelist}),
        dcc.Store(id='image_files', data={'files':filelist, 'current':0}),
        html.H6("Type of annotation"),
        dcc.RadioItems(id='radio',
            options=[{'label':opt, 'value':opt} for opt in color_dict.keys()],
            value=options[0],
            labelStyle={'display': 'inline-block'}
        ),
        html.Button('Previous', id='previous'),
        html.Button('Next', id='next'),
        html.H6("How to display images"),
        dcc.RadioItems(id='mode',
            options=[{'label':'trace', 'value':'trace'},
                     {'label':'layout', 'value':'layout'}],
            value='layout',
            labelStyle={'display': 'inline-block'}
        ),

        ],
        style={'width':'50%'})


@app.callback(
    dash.dependencies.Output('annotations-store', 'data'),
    [dash.dependencies.Input('graph', 'relayoutData')],
    [dash.dependencies.State('annotations-store', 'data'),
     dash.dependencies.State('image_files', 'data')
     ]
    )
def shape_added(fig_data, store_data, image_files):
    if fig_data and image_files and 'shapes' in fig_data:
        filename = image_files['files'][image_files['current']]
        store_data[filename]['shapes'] = fig_data['shapes']
        return store_data
    else:
        return dash.no_update


@app.callback(
    dash.dependencies.Output('graph', 'figure'),
    [dash.dependencies.Input('radio', 'value'),
     dash.dependencies.Input('image_files', 'data'),
     dash.dependencies.Input('mode', 'value')],
    [dash.dependencies.State('annotations-store', 'data')]
    )
def radio_pressed(val, image_files, mode, store_data):
    """
    When radio button changed OR current file changed, update figure.
    """
    if val is None:
        return dash.no_update

    if image_files:
        filename = image_files['files'][image_files['current']]
    else:
        filename = filelist[0]
    fig = make_figure(filename, mode=mode)
    fig['layout']['shapes'] = store_data[image_files['files'][image_files['current']]]['shapes']
    fig['layout']['newshape']['line']['color'] = color_dict[val]
    return fig


@app.callback(
    dash.dependencies.Output('image_files', 'data'),
    [dash.dependencies.Input('previous', 'n_clicks'),
     dash.dependencies.Input('next', 'n_clicks')],
    [dash.dependencies.State('image_files', 'data')]
    )
def previousnext_pressed(n_clicks_back, n_clicks_fwd, image_files):
    """
    Update current file when next or previous button is pressed. 
    """
    if (n_clicks_back is None and n_clicks_fwd is None) or image_files is None:
        return dash.no_update
    ctx = dash.callback_context
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    current = image_files['current']
    l = len(image_files['files'])
    image_files['current'] = ((current + 1) % l if button_id == 'next'
                                else (current - 1) % l)
    return image_files


if __name__ == '__main__':
    app.run_server(debug=True)

