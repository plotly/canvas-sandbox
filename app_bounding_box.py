import dash
from dash.dependencies import Input, Output, State, ClientsideFunction
import dash_html_components as html
import dash_core_components as dcc
import dash_table
from glob import glob
import numpy as np
from utils import make_figure, path_to_indices
import plotly.graph_objects as go
import os
import re
import uuid
import time

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
"X0",
"Y0",
"X1",
"Y1"
]

def column_name_to_id(n):
    n=n.translate({ord(" "):ord("-")})
    return 'annotations-table-column-%s'%(n,)

def format_float(f):
    return '%.2f' % (f,)

def shape_to_table_row(sh):
    k=column_name_to_id
    return {
        k("Timestamp"):sh['timestamp'],
        k("Type"):type_dict[sh['line']['color']],
        k("X0"):format_float(sh['x1']),
        k("Y0"):format_float(sh['y1']),
        k("X1"):format_float(sh['x0']),
        k("Y1"):format_float(sh['y0'])
    }

def shape_cmp(s0,s1):
    """ Compare two shapes """
    return (
        (s0['x0'] == s1['x0']) and
        (s0['x1'] == s1['x1']) and
        (s0['y0'] == s1['y0']) and
        (s0['y1'] == s1['y1']) and
        (s0['line']['color'] == s1['line']['color']))

class shape_in:
    def __init__(self,se):
        self.se = se
    def __call__(self,s):
        """ check if a shape is in list (done this way to use custom compare) """
        return any(shape_cmp(s,s_) for s_ in self.se)

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
        html.A(id='download',download='annotations.json',
        children='Download annotations'),
        html.Div(id='debug-div')
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
        if 'shapes' in fig_data.keys():
            # this means all the shapes have been passed to this function via
            # fig_data, so we store them

            # find the shapes that are new
            new_shapes=list(filter(
                lambda s: not shape_in(store_data[filename]['shapes'])(s),
                fig_data['shapes']))
            # add timestamps to the new shapes
            for s in new_shapes:
                s['timestamp']=time.ctime()
            # find the shapes that already exist in store data
            old_shapes=list(filter(
                shape_in(store_data[filename]['shapes']),
                fig_data['shapes']))
            store_data[filename]['shapes'] = old_shapes + new_shapes

        elif re.match('shapes\[[0-9]+\].x0', list(fig_data.keys())[0]):
            # this means a shape was updated (e.g., by clicking and dragging its
            # vertices), so we just update the specific shape
            for key, val in fig_data.items():
                shape_nb, coord = key.split('.')
                # shape_nb is for example 'shapes[2].x0': this extracts the number
                shape_nb = shape_nb.split('.')[0].split('[')[-1].split(']')[0]
                store_data[filename]['shapes'][int(shape_nb)][coord] = fig_data[key]
                # update timestamp
                store_data[filename]['shapes'][int(shape_nb)]['timestamp']=time.ctime()
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

app.clientside_callback(
"""
function(the_store_data) {
    var s = JSON.stringify(the_store_data);
    var b = new Blob([s],{type: 'text/plain'});
    var url = URL.createObjectURL(b);
    return url;
}
""",
    Output('download', 'href'),
    [Input('annotations-store', 'data')]
)

if __name__ == '__main__':
    app.run_server(debug=True)
