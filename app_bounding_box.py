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
    "Timestamp",
    "Type",
    "X0",
    "Y0",
    "X1",
    "Y1"
]


def format_float(f):
    return '%.2f' % (f,)


def shape_to_table_row(sh):
    return {
        "Timestamp": sh['timestamp'],
        "Type": type_dict[sh['line']['color']],
        "X0": format_float(sh['x1']),
        "Y0": format_float(sh['y1']),
        "X1": format_float(sh['x0']),
        "Y1": format_float(sh['y0'])
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


external_stylesheets = ['assets/style.css', 'assets/app_bounding_box_style.css']
app = dash.Dash(__name__,external_stylesheets=external_stylesheets)

filelist = [app.get_asset_url('driving.jpg'),
            app.get_asset_url(
                'professional-transport-autos-bridge-traffic-road-rush-hour.jpg'),
            app.get_asset_url('rocket.jpg')]

server = app.server

fig = make_figure(filelist[0], mode='layout', show_axes=False)
fig['layout']['newshape']['line']['color'] = color_dict[DEFAULT_ATYPE]

app.layout = html.Div(
    id='main',
    children=[
        # Banner display
        html.Div(
            id="banner",
            children=[
                html.H1("Bounding Box Classification App", id="title"),
                html.Img(
                    id="logo", src=app.get_asset_url("dash-logo-new.png"),
                    ),
            ],
        className="eleven columns"
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
                # Data table
                dash_table.DataTable(
                    id='annotations-table',
                    columns=[
                        dict(
                            name=n,
                            id=n
                        ) for n in columns
                    ]
                )
            ],
        className="six columns"
        ),
        # Sidebar
        html.Div(
            id="sidebar",
            children=[
                dcc.Store(id='graph-copy', data=fig),
                dcc.Store(id='annotations-store',
                          data={filename: {'shapes': []} for filename in filelist}),
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
            ],
        className="five columns"
        )
    ], className="twelve columns"
)


def store_shape_resize(store_data_for_file, fig_data):
    """
    Extract the shape that was resized (its index) and store the resized
    coordinates.
    """
    for key, val in fig_data.items():
        shape_nb, coord = key.split('.')
        # shape_nb is for example 'shapes[2].x0': this extracts the number
        shape_nb = shape_nb.split('.')[0].split('[')[-1].split(']')[0]
        store_data_for_file['shapes'][int(
            shape_nb)][coord] = fig_data[key]
        # update timestamp
        store_data_for_file['shapes'][int(
            shape_nb)]['timestamp'] = time.ctime()
    return store_data_for_file


def shape_data_remove_timestamp(shape):
    """
    go.Figure complains if we include the 'timestamp' key when updating the
    figure
    """
    new_shape = dict()
    for k in (shape.keys() - set(['timestamp'])):
        new_shape[k] = shape[k]
    return new_shape


@app.callback(
    [dash.dependencies.Output('annotations-store', 'data'),
     dash.dependencies.Output('annotations-table', 'data'),
     dash.dependencies.Output('graph', 'figure')],
    [dash.dependencies.Input('graph', 'relayoutData'),
     dash.dependencies.Input('annotation-type-dropdown', 'value'),
     dash.dependencies.Input('image_files', 'data')],
    [dash.dependencies.State('annotations-store', 'data')])
def update_graph_table_store(fig_data, annotation_type, image_files, store_data):
    return_value = None
    filename = image_files['files'][image_files['current']]
    cbcontext = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if cbcontext == 'graph.relayoutData':
        if 'shapes' in fig_data.keys():
            # this means all the shapes have been passed to this function via
            # fig_data, so we store them

            # in the case where shapes have been added, we need to find new
            # shapes to add the timestamp to them
            # we preserve the old shapes because they have the timestamp added
            # to them already, which we don't want to replace

            # find the shapes that are new
            new_shapes = list(filter(
                lambda s: not shape_in(store_data[filename]['shapes'])(s),
                fig_data['shapes']))
            # add timestamps to the new shapes
            for s in new_shapes:
                s['timestamp'] = time.ctime()
            # find the old shapes to preserve them (rather than overwrite their
            # timestamp with the shape lacking a timestamp in fig_data['shapes'])
            old_shapes = list(filter(
                shape_in(fig_data['shapes']),
                store_data[filename]['shapes']))
            store_data[filename]['shapes'] = old_shapes + new_shapes

        elif re.match('shapes\[[0-9]+\].x0', list(fig_data.keys())[0]):
            # this means a shape was updated (e.g., by clicking and dragging its
            # vertices), so we just update the specific shape
            store_data[filename] = store_shape_resize(
                store_data[filename], fig_data)
    return_value = (
        store_data,
        [shape_to_table_row(sh) for sh in store_data[filename]['shapes']]
    )
    fig = make_figure(filename, mode=DEFAULT_FIG_MODE)
    fig.update_layout({'shapes': [shape_data_remove_timestamp(sh) for sh in
                                  store_data[image_files['files']
                                             [image_files['current']]]['shapes']],
                       'newshape.line.color': color_dict[annotation_type],
                       # reduce space between image and graph edges
                       'margin':dict(
                            l=0,
                            r=0,
                            b=0,
                            t=0,
                            pad=4
                        )
                      })
    # append figure data
    new_store_data, new_table_data = return_value
    return_value = (new_store_data, new_table_data, fig)
    return return_value


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
