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

# Callback called when button pressed to upload images
load_images_test=True
if load_images_test:
	@app.callback(
		dash.dependencies.Output('filenames-display','children'),
		[dash.dependencies.Input('upload-images','filename')])
	def load_new_images(image_upload_filenames):
		if image_upload_filenames is not None:
			filelist = [app.get_asset_url(basename) for basename in image_upload_filenames]
			return str(filelist)
else:
	@app.callback(
		dash.dependencies.Output('image_files','data'),
		[dash.dependencies.Input('upload-images','filename')])
	def load_new_images(image_upload_filenames):
		if image_upload_filenames is not None:
			filelist = [app.get_asset_url(basename) for basename in image_upload_filenames]
			return {
				'files':filelist,
				'current':0
			}


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
        print("storing annotation with %s" % (filename,))
        store_data[filename]['shapes'] = fig_data['shapes']
        return store_data
    elif (fig_data and image_files and 
          re.match('shapes\[[0-9]+\].x0', list(fig_data.keys())[0])):
        filename = image_files['files'][image_files['current']]
        print("recalling stored annotations for %s (?)", (filename,))
        for key, val in fig_data.items():
            shape_nb, coord = key.split('.')
            # shape_nb is for example 'shapes[2].x0' we want the number
            shape_nb = shape_nb.split('.')[0].split('[')[-1].split(']')[0]
            print(key, val, 
                  store_data[filename]['shapes'][int(shape_nb)][coord], fig_data[key])
            store_data[filename]['shapes'][int(shape_nb)][coord] = fig_data[key]
            print(store_data[filename]['shapes'][int(shape_nb)][coord])
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

