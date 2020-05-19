import dash
from dash.dependencies import Input, Output, State, ClientsideFunction
import dash_html_components as html
import dash_core_components as dcc
import dash_table
from glob import glob
import numpy as np
from utils import make_figure, path_to_indices
import plotly.graph_objects as go
import plotly.express as px
import os
import re
import uuid
import time

NUM_ATYPES=15
DEFAULT_FIG_MODE='layout'
annotation_colormap=px.colors.qualitative.Light24
annotation_types=[
    'tree',
    'building',
    'sky',
    'road',
    'sidewalk',
    'car',
    'pedestrian',
    'cyclist',
    'stop sign',
    'parking sign',
    'traffic light',
    'lamp post',
    'star', # e.g., sun or moon as to not confuse them with artificial lighting
]
DEFAULT_ATYPE=annotation_types[0]

# prepare bijective type<->color mapping
typ_col_pairs = [(t,annotation_colormap[n%len(annotation_colormap)])
                 for n,t in enumerate(annotation_types)]
# types to colors
color_dict = {}
# colors to types
type_dict = {}
for typ, col in typ_col_pairs:
    color_dict[typ] = col
    type_dict[col] = typ

options = list(color_dict.keys())
columns = [
    "Type",
    "X0",
    "Y0",
    "X1",
    "Y1"
]

def coord_to_tab_column(coord):
    return coord.upper()

def time_passed(start=0):
    return round(time.mktime(time.localtime()))-start


def format_float(f):
    return '%.2f' % (float(f),)


def shape_to_table_row(sh):
    return {
        "Type": type_dict[sh['line']['color']],
        "X0": format_float(sh['x0']),
        "Y0": format_float(sh['y0']),
        "X1": format_float(sh['x1']),
        "Y1": format_float(sh['y1'])
    }


def default_table_row():
    return {
        "Type": DEFAULT_ATYPE,
        "X0": format_float(10),
        "Y0": format_float(10),
        "X1": format_float(20),
        "Y1": format_float(20)
    }

def table_row_to_shape(tr):
    return {
        "editable":True,
        "xref":"x",
        "yref":"y",
        "layer":"above",
        "opacity":1,
        "line":{
            "color":color_dict[tr['Type']],
            "width":4,
            "dash":"solid"
        },
        "fillcolor":"rgba(0, 0, 0, 0)",
        "fillrule":"evenodd",
        "type":"rect",
        "x0":tr['X0'],
        "y0":tr['Y0'],
        "x1":tr['X1'],
        "y1":tr['Y1'],
    }
    
def shape_cmp(s0, s1):
    """ Compare two shapes """
    return (
        (s0['x0'] == s1['x0']) and
        (s0['x1'] == s1['x1']) and
        (s0['y0'] == s1['y0']) and
        (s0['y1'] == s1['y1']) and
        (s0['line']['color'] == s1['line']['color']))


def shape_in(se):
    """ check if a shape is in list (done this way to use custom compare) """
    return lambda s: any(shape_cmp(s, s_) for s_ in se)


def annotations_table_shape_resize(annotations_table_data, fig_data):
    """
    Extract the shape that was resized (its index) and store the resized
    coordinates.
    """
    print('fig_data',fig_data)
    print('table_data',annotations_table_data)
    for key, val in fig_data.items():
        shape_nb, coord = key.split('.')
        # shape_nb is for example 'shapes[2].x0': this extracts the number
        shape_nb = shape_nb.split('.')[0].split('[')[-1].split(']')[0]
        # this should correspond to the same row in the data table
        # we have to format the float here because this is exactly the entry in
        # the table
        annotations_table_data[int(
            shape_nb)][coord_to_tab_column(coord)] = format_float(fig_data[key])
        # (no need to compute a time stamp, that is done for any change in the
        # table values, so will be done later)
    return annotations_table_data


def shape_data_remove_timestamp(shape):
    """
    go.Figure complains if we include the 'timestamp' key when updating the
    figure
    """
    new_shape = dict()
    for k in (shape.keys() - set(['timestamp'])):
        new_shape[k] = shape[k]
    return new_shape


external_stylesheets = ['assets/app_bounding_box_style.css']
app = dash.Dash(__name__,external_stylesheets=external_stylesheets)

filelist = [app.get_asset_url('driving.jpg'),
            app.get_asset_url(
                'professional-transport-autos-bridge-traffic-road-rush-hour.jpg'),
            app.get_asset_url('rocket.jpg')]

server = app.server

fig = make_figure(filelist[0], mode=DEFAULT_FIG_MODE)
fig.update_layout({
    'newshape.line.color': color_dict[DEFAULT_ATYPE],
    'margin': dict(
        l = 0,
        r = 0,
        b = 0,
        t = 0,
        pad = 4)
})

app.layout = html.Div(
    id='main',
    children=[
        # Banner display
        html.Div(
            id="banner",
            children=[
                html.Img(
                    id="logo", src=app.get_asset_url("dash-logo-new.png")
                ),
                html.H2("Bounding Box Classification App", id="title"),
            ],
        ),
        # Main body
        html.Div(
            id="app-container",
            children=[
                # Graph
                dcc.Graph(id='graph',
                    figure=fig,
                    config={'modeBarButtonsToAdd': ['drawrect', 'eraseshape']},
                ),
                html.Div(id='table-container',
                    children=[
                        # Timestamp table
                        dash_table.DataTable(
                            id='timestamp-table',
                            columns=[{
                                'name': 'Timestamp',
                                'id': 'Timestamp'
                            }]
                        ),
                        # Data table
                        dash_table.DataTable(
                            id='annotations-table',
                            columns=[
                                dict(
                                    name=n,
                                    id=n,
                                    presentation=('dropdown' if n == 'Type' else 'input')
                                ) for n in columns
                            ],
                            editable=True,
                            dropdown={
                                'Type': {
                                    'options':[
                                        {'label': o, 'value': o}
                                        for o in annotation_types
                                    ]
                                }
                            }
                        )
                    ]
                )
            ]
        ),
        # Sidebar
        html.Div(
            id="sidebar",
            children=[
                dcc.Store(id='graph-copy', data=fig),
                dcc.Store(id='annotations-store',
                          data=dict(
                            **{filename: {'shapes': []} for filename in filelist},
                            **{'starttime': time_passed()}
                          )
                ),
                dcc.Store(id='image_files', data={'files': filelist, 'current': 0}),
                html.H6("Type of annotation"),
                dcc.Dropdown(
                    id='annotation-type-dropdown',
                    options=[{'label': t, 'value': t} for t in annotation_types],
                    value=DEFAULT_ATYPE,
                    clearable=False
                ),
                html.H6('Choose image'),
                html.Button('Previous', id='previous',className='button'),
                html.Button('Next', id='next',className='button'),
                html.Button('Add Shape', id='add-shape',className='button'),
                html.H6("Annotations"),
                # We use this pattern because we want to be able to download the
                # annotations by clicking on a button
                html.A(id='download', download='annotations.json',
                       # make invisble, we just want it to click on it
                       style={ 'display': 'none' }),
                html.Button('Download annotations',
                            id='download-button',
                            className='button'),
                html.Div(id='dummy',style={'display':'none'})
            ]
        )
    ],
)

@app.callback(
    [Output('annotations-table','data'),
     Output('image_files','data')],
    [Input('add-shape','n_clicks'),
     Input('previous','n_clicks'),
     Input('next','n_clicks'),
     Input('graph','relayoutData')],
    [State('annotations-table','data'),
     State('image_files','data'),
     State('annotations-store','data'),
     State('annotation-type-dropdown','value')]
)
def modify_table_entries(add_shape_n_clicks,
                         previous_n_clicks,
                         next_n_clicks,
                         graph_relayoutData,
                         annotations_table_data,
                         image_files_data,
                         annotations_store_data,
                         annotation_type):
    cbcontext = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if cbcontext == 'graph.relayoutData':
        if 'shapes' in graph_relayoutData.keys():
            # this means all the shapes have been passed to this function via
            # graph_relayoutData, so we store them
            annotations_table_data=[
                shape_to_table_row(sh) for sh in graph_relayoutData['shapes']
            ]
        elif re.match('shapes\[[0-9]+\].x0', list(graph_relayoutData.keys())[0]):
            # this means a shape was updated (e.g., by clicking and dragging its
            # vertices), so we just update the specific shape
            annotations_table_data = annotations_table_shape_resize(
                annotations_table_data,
                graph_relayoutData)
        if annotations_table_data is None:
            return dash.no_update
        else:
            return (annotations_table_data,image_files_data)
    if cbcontext == 'add-shape.n_clicks':
        if annotations_table_data is None:
            annotations_table_data = []
        row=default_table_row()
        row['Type']=annotation_type
        if row not in annotations_table_data:
            annotations_table_data.append(row)
        return (annotations_table_data,image_files_data)
    image_index_change=0
    if cbcontext == 'previous.n_clicks':
        image_index_change=-1
    if cbcontext == 'next.n_clicks':
        image_index_change=1
    image_files_data['current']+=image_index_change
    image_files_data['current']%=len(image_files_data['files'])
    if image_index_change != 0:
        # image changed, update annotations_table_data with new data
        annotations_table_data=[]
        filename=image_files_data['files'][image_files_data['current']]
        print(annotations_store_data[filename])
        for sh in annotations_store_data[filename]['shapes']:
            annotations_table_data.append(shape_to_table_row(sh))
        return (annotations_table_data,image_files_data)
    else:
        return dash.no_update

@app.callback(
    [Output('graph','figure'),
     Output('annotations-store','data'),
     Output('timestamp-table','data')],
    [Input('annotations-table','data'),
     Input('annotation-type-dropdown','value')],
    [State('image_files','data'),
     State('annotations-store','data')]
)
def send_figure_to_graph(annotations_table_data,
                         annotation_type,
                         image_files_data,
                         annotations_store):
    if annotations_table_data is not None:
        filename=image_files_data['files'][image_files_data['current']]
        # convert table rows to those understood by fig.update_layout
        fig_shapes=[table_row_to_shape(sh) for sh in annotations_table_data]
        # find the shapes that are new
        new_shapes = list(filter(
            lambda s: not shape_in(annotations_store[filename]['shapes'])(s),
            fig_shapes))
        # add timestamps to the new shapes
        for s in new_shapes:
            s['timestamp'] = time_passed(annotations_store['starttime'])
        # find the old shapes in order to look up their timestamps
        old_shapes = list(filter(
            shape_in(fig_shapes),
            annotations_store[filename]['shapes']))
        shapes=old_shapes+new_shapes
        fig = make_figure(filename, mode=DEFAULT_FIG_MODE)
        fig.update_layout({
            'shapes': [shape_data_remove_timestamp(sh) for sh in shapes],
            # 'newshape.line.color': color_dict[annotation_type],
            # reduce space between image and graph edges
            'newshape.line.color': color_dict[annotation_type],
            'margin': dict(
                l = 0,
                r = 0,
                b = 0,
                t = 0,
                pad = 4)
        })
        annotations_store[filename]['shapes']=shapes
        return (fig,annotations_store,[{'Timestamp':s['timestamp']} for s in shapes])
    return dash.no_update

# set the download url to the contents of the annotations-store (so they can be
# downloaded from the browser's memory)
app.clientside_callback(
    """
function(the_store_data) {
    let s = JSON.stringify(the_store_data);
    let b = new Blob([s],{type: 'text/plain'});
    let url = URL.createObjectURL(b);
    return url;
}
""",
    Output('download', 'href'),
    [Input('annotations-store', 'data')]
)

# click on download link via button
app.clientside_callback(
"""
function(download_button_n_clicks)
{
    let download_a=document.getElementById("download");
    download_a.click();
    return '';
}
""",
    Output('dummy','children'),
    [Input('download-button','n_clicks')]
)



if __name__ == '__main__':
    app.run_server(debug=True)
