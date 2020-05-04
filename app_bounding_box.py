import dash
from dash.dependencies import Input, Output, State
import dash_html_components as html
import dash_core_components as dcc
from glob import glob
import numpy as np
from utils import make_figure, path_to_indices
import plotly.graph_objects as go
import os
import re
import pdb


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
        dcc.Graph(id='graph', figure=fig,
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
        html.H6("Load image set"),
		dcc.Upload(
			id='upload-images',
			children=html.Div([
				html.Button('Load...', id='load-images-button')
			]),
			# Allow multiple files to be uploaded
			multiple=True
		),
		html.Div(id='filenames-display'),

        ],
        style={'width':'50%'})

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
    fig['layout']['shapes'] = store_data[
        image_files['files'][image_files['current']]]['shapes']
    fig['layout']['newshape']['line']['color'] = color_dict[val]
    return fig


@app.callback(
    [dash.dependencies.Output('image_files', 'data'),
     dash.dependencies.Output('annotations-store', 'data')],
    [dash.dependencies.Input('previous', 'n_clicks'),
     dash.dependencies.Input('next', 'n_clicks'),
     dash.dependencies.Input('upload-images','filename'),
     dash.dependencies.Input('graph', 'relayoutData')],
    [dash.dependencies.State('image_files', 'data'),
     dash.dependencies.State('annotations-store', 'data')]
    )
def images_annotations_update(
    # inputs
    n_clicks_back,
    n_clicks_fwd,
    image_upload_filenames,
    graph_relayoutData,
    # states
    image_files,
    annotations_store_data):
    """
    Update current file when next or previous button is pressed, or new images loaded. 
    """
    #pdb.set_trace()
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if (changed_id == 'upload-images.filename') and (image_upload_filenames is not None):
        filelist = [app.get_asset_url(basename) for basename in image_upload_filenames]
        # TODO Here we should ask if we want to save the current annotations
        return ({
            'files':filelist,
            'current':0
        },{
            filename:{'shapes':[]} for filename in filelist
        })
    elif changed_id == 'next.n_clicks':
        l = len(image_files['files'])
        current = image_files['current']
        image_files['current'] = (current + 1) % l    
        return (image_files,annotations_store_data)
    elif changed_id == 'previous.n_clicks':
        l = len(image_files['files'])
        current = image_files['current']
        image_files['current'] = (current - 1) % l    
        return (image_files,annotations_store_data)
    if changed_id == 'graph.relayoutData':
        if 'shapes' in graph_relayoutData:
            filename = image_files['files'][image_files['current']]
            print("storing annotation with %s" % (filename,))
            annotations_store_data[filename]['shapes'] = graph_relayoutData['shapes']
        return (image_files,annotations_store_data)
    if changed_id == 'graph.relayoutData':
        if re.match('shapes\[[0-9]+\].x0', list(graph_relayoutData.keys())[0]):
            filename = image_files['files'][image_files['current']]
            print("recalling stored annotations for %s (?)", (filename,))
            for key, val in graph_relayoutData.items():
                shape_nb, coord = key.split('.')
                # shape_nb is for example 'shapes[2].x0' we want the number
                shape_nb = shape_nb.split('.')[0].split('[')[-1].split(']')[0]
                print(key, val, 
                      annotations_store_data[filename]['shapes'][int(shape_nb)][coord],
                      graph_relayoutData[key])
                annotations_store_data[filename]['shapes'][int(shape_nb)][coord] = \
                    graph_relayoutData[key]
                print(annotations_store_data[filename]['shapes'][int(shape_nb)][coord])
        return (image_files,annotations_store_data)
    else:
        return dash.no_update

if __name__ == '__main__':
    app.run_server(debug=True,threaded=False)
