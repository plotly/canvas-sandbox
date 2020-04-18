import plotly.graph_objects as go
from skimage import io
from PIL import Image
import numpy as np

def make_figure(filename_uri, mode='layout', dragmode='rectdraw'):
    if mode == 'layout':
        fig = go.Figure()

        # Add trace
        fig.add_trace(
            go.Scatter(x=[], y=[])
        )
        im = Image.open(filename_uri[1:])
        width, height = im.size
        # Add images
        fig.add_layout_image(
                dict(
                    source=filename_uri,
                    xref="x",
                    yref="y",
                    x=0,
                    y=0,
                    sizex=width,
                    sizey=height,
                    sizing="contain",
                    layer="below"
                    )
        )
        fig.update_layout(template=None)
        fig.update_xaxes(showgrid=False, range=(0, width))
        fig.update_yaxes(showgrid=False, scaleanchor='x', range=(height, 0))
    else:
        im = io.imread(filename_uri[1:])
        fig = go.Figure(go.Image(z=im))
    fig.update_layout(margin=dict(t=0, b=0))
    layout = {}
    for key in fig.layout:
        layout[key] = fig.layout[key]
    layout['dragmode'] = dragmode
    layout['newshape'] = {'line':{}}
    layout['activeshape'] = {}
    return {'data':fig.data, 'layout':layout}


def path_to_indices(path):
    """From SVG path to numpy array of coordinates, each row being a (row, col) point
    """
    indices_str = [el.replace('M', '').replace('Z', '').split(',') for el in path.split('L')]
    return np.array(indices_str, dtype=float)


def indices_to_path(indices):
    """From numpy array to SVG path
    """
    path = 'M'
    for row in indices.astype(str):
        path+= row[0] + ',' + row[1] + 'L'
    path = path[:-1] + 'Z'
    return path
