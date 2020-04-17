import plotly.graph_objects as go
from skimage import io
from PIL import Image


def make_figure(filename_uri, mode='layout'):
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
                    y=height,
                    sizex=width,
                    sizey=height,
                    sizing="contain",
                    layer="below"
                    )
        )
        fig.update_layout(template=None)
        fig.update_xaxes(showgrid=False, range=(0, width))
        fig.update_yaxes(showgrid=False, scaleanchor='x', range=(0, height))
    else:
        im = io.imread(filename_uri[1:])
        fig = go.Figure(go.Image(z=im))
    fig.update_layout(margin=dict(t=0, b=0))
    layout = {}
    for key in fig.layout:
        layout[key] = fig.layout[key]
    layout['dragmode'] = 'rectdraw'
    layout['newshape'] = {'line':{}}
    layout['activeshape'] = {}
    return {'data':fig.data, 'layout':layout}

