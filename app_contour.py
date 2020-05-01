import dash
from dash.dependencies import Input, Output, State
import dash_html_components as html
import dash_core_components as dcc
from glob import glob
import numpy as np
from utils import make_figure, path_to_indices, indices_to_path
import json
from skimage import io, filters, segmentation
import plotly.graph_objects as go
from scipy.interpolate import interp1d
import os

color_dict = {'car':'blue', 'truck':'red', 'building':'yellow', 'tree':'green'}
options = ['car', 'truck', 'building', 'tree']

app = dash.Dash(__name__,
    external_stylesheets = [
        {
            'href': 'https://unpkg.com/purecss@1.0.1/build/pure-min.css',
            'rel': 'stylesheet',
            'integrity': 'sha384-oAOxQR6DkCoMliIh8yFnu25d7Eq/PHS21PClpwjOTeU2jRSq11vu66rf90/cZr47',
            'crossorigin': 'anonymous'
        },
        'https://unpkg.com/purecss@1.0.1/build/grids-responsive-min.css',
        #'https://unpkg.com/purecss@1.0.1/build/base-min.css',
    ],
)


filelist = [
            app.get_asset_url('lung_ct.jpg'),
            app.get_asset_url('mri_head.jpg'),
            app.get_asset_url('astronaut.png'),
            app.get_asset_url('rocket.jpg')]

server = app.server

fig = make_figure(filelist[0], mode='layout', dragmode='drawclosedpath')
fig['layout']['newshape']['line']['color'] = color_dict['car']

app.layout=html.Div(children=[
    html.Div(children=[
        html.H3("Outline the contour of objects"),
        html.Button('Magic scissors', id='snap'),
        html.H5("How to display images", style={'margin-top':'2em'}),
        dcc.RadioItems(id='mode',
            options=[{'label':'trace', 'value':'trace'},
                     {'label':'layout', 'value':'layout'}],
            value='layout',
            labelStyle={'display': 'inline-block'}
        ),
        ], className="pure-u-1 pure-1-sm-1 pure-u-lg-6-24 pure-u-xl-6-24",
        style={'background-color':'azure', 'height':'100%', 'padding':'3em'}),
    html.Div([
        dcc.Graph(id='graph', figure=fig, config={'modeBarButtonsToAdd':['drawclosedpath', 'eraseshape']}),
        html.Div(children=[
        html.Button('<< Previous', id='previous'),
        html.Button('Next >>', id='next'),
        ], style={'margin':'auto', 'text-align': 'center'}),
        dcc.Store(id='graph-copy', data=fig),
        dcc.Store(id='annotations-store', 
            data={filename:{'shapes':[]} for filename in filelist}),
        dcc.Store(id='image_files', data={'files':filelist, 'current':0}),
        
        ],
        className="pure-u-1 pure-u-sm-1 pure-u-lg-15-24 pure-u-xl-15-24")
])

@app.callback(
    dash.dependencies.Output('annotations-store', 'data'),
    [dash.dependencies.Input('graph', 'relayoutData')],
    [dash.dependencies.State('annotations-store', 'data'),
     dash.dependencies.State('image_files', 'data')
     ]
    )
def shape_added(fig_data, store_data, image_files):
    print(fig_data)
    if fig_data and image_files and 'shapes' in fig_data:
        filename = image_files['files'][image_files['current']]
        store_data[filename]['shapes'] = fig_data['shapes']
        return store_data
    else:
        return dash.no_update


@app.callback(
    dash.dependencies.Output('graph', 'figure'),
    [
     dash.dependencies.Input('image_files', 'data'),
     dash.dependencies.Input('mode', 'value'),
     dash.dependencies.Input('snap', 'n_clicks')
     ],
    [dash.dependencies.State('annotations-store', 'data')]
    )
def radio_pressed(image_files, mode, snap, store_data):
    """
    When radio button changed OR current file changed, update figure.
    """
    ctx = dash.callback_context

    if not ctx.triggered:
        button_id = 'No clicks yet'
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    print(button_id)
    path = None
    if image_files:
        filename = image_files['files'][image_files['current']]
    else:
        filename = filelist[0]
    fig = make_figure(filename, mode=mode, dragmode='drawclosedpath')
    fig['layout']['shapes'] = store_data[image_files['files'][image_files['current']]]['shapes']
    fig['layout']['newshape']['line']['color'] = color_dict['car']
    fig['layout']['uirevision'] = filename
    short_filename = os.path.join('assets', os.path.basename(filename))
    if button_id == 'snap':
        path = path_to_indices(store_data[filename]['shapes'][-1]['path'])
        t = np.linspace(0, 1, len(path))
        t_full = np.linspace(0, 1, 80)
        interp_row = interp1d(t, path[:, 0])
        interp_col = interp1d(t, path[:, 1])
        path = np.array([interp_row(t_full), interp_col(t_full)]).T
    if path is not None:
        img = io.imread(short_filename, as_gray=True)
        snake = segmentation.active_contour(
                filters.gaussian(img, 3),
                path[:, ::-1],
                alpha=0.002, 
                beta=0.001,
                #gamma=0.001,
                coordinates='rc')
        path = indices_to_path(snake[:, ::-1])
        new_shape = dict(store_data[filename]['shapes'][-1])
        new_shape['path'] = path
        new_shape['line']['color'] = 'orange'
        fig['layout']['shapes'] += (new_shape,)


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
    app.run_server(port=8051, debug=True)

