import dash
from dash.dependencies import Input, Output, State
import dash_html_components as html
import dash_core_components as dcc
import dash_table
from glob import glob
import numpy as np
from utils import make_figure, path_to_indices
import plotly.graph_objects as go
import os
import re

# prepare bijective type<->color mapping
typ_col_pairs=[('car','blue'), ('truck','red'), ('building','yellow'), ('tree','green')]
# types to colors
color_dict = {}
# colors to types
type_dict = {}
for typ,col in typ_col_pairs: 
    color_dict[typ]=col
    type_dict[col]=typ

options = list(color_dict.keys())
columns = [
"Timestamp",
"Type",
"Top Left x",
"Top Left y",
"Bottom Right x",
"Bottom Right y"
]

def column_name_to_id(n):
    n=n.translate({ord(" "):ord("-")})
    return 'annotations-table-column-%s'%(n,)

def shape_to_table_row(sh):
    k=column_name_to_id
    return {
        k("Timestamp"):0,
        k("Type"):type_dict[sh['line']['color']],
        k("Top Left x"):sh['x1'],
        k("Top Left y"):sh['y1'],
        k("Bottom Right x"):sh['x0'],
        k("Bottom Right y"):sh['y0']
    }
    
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
        dcc.Graph(id='graph',
                  figure=fig,
                  config={'modeBarButtonsToAdd':['drawrect', 'eraseshape']}),
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
        html.H6("Annotations"),
        dash_table.DataTable(
            id='annotations-table',
            columns=[
                dict(
                    name=n,
                    id=column_name_to_id(n)
                ) for n in columns
            ]

        ),

        ],
        style={'width':'50%'})


@app.callback(
    [dash.dependencies.Output('annotations-store', 'data'),
     dash.dependencies.Output('annotations-table', 'data'),
     dash.dependencies.Output('graph', 'figure')],
    [dash.dependencies.Input('graph', 'relayoutData'),
     dash.dependencies.Input('radio', 'value'),
     dash.dependencies.Input('image_files', 'data'),
     dash.dependencies.Input('mode', 'value')],
    [dash.dependencies.State('annotations-store', 'data')])
def shape_added(fig_data, radio_val, image_files, mode_val, store_data):
    ret=None
    filename = image_files['files'][image_files['current']]
    cbcontext=[p['prop_id'] for p in dash.callback_context.triggered][0]
    if cbcontext == 'graph.relayoutData':
        try:
            store_data[filename]['shapes'] = fig_data['shapes']
        except KeyError:
            store_data[filename]['shapes'] = ''
    if cbcontext == 'image_files.data':
        print("landed here")
        for key, val in fig_data.items():
            try:
                shape_nb, coord = key.split('.')
                # shape_nb is for example 'shapes[2].x0' we want the number
                shape_nb = shape_nb.split('.')[0].split('[')[-1].split(']')[0]
                print(key, val, store_data[filename]['shapes'][int(shape_nb)][coord],
                    fig_data[key])
                store_data[filename]['shapes'][int(shape_nb)][coord] = fig_data[key]
                print(store_data[filename]['shapes'][int(shape_nb)][coord])
            except ValueError:
                pass
    ret = (
        store_data,
        [shape_to_table_row(sh) for sh in store_data[filename]['shapes']]
    )
    fig = make_figure(filename, mode=mode_val)
    fig['layout']['shapes'] = store_data[image_files['files'][image_files['current']]]['shapes']
    fig['layout']['newshape']['line']['color'] = color_dict[radio_val]
    sd,td=ret
    ret=(sd,td,fig)
    return ret

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

