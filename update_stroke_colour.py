import plotly.express as px
import dash
from dash.dependencies import Input, Output, State, ClientsideFunction
import dash_html_components as html
import dash_core_components as dcc
import dash_utils
import utils
import shape_utils
import plot_common
import flask
import os

DEFAULT_LINE_WIDTH=5

# the number of different classes for labels
NUM_LABEL_CLASSES=15
DEFAULT_LABEL_CLASS=0
class_label_colormap=px.colors.qualitative.Light24
class_labels=list(range(NUM_LABEL_CLASSES))
# we can't have less colors than classes
assert(NUM_LABEL_CLASSES<=len(class_label_colormap))
def class_to_color(n):
    return class_label_colormap[n]
def color_to_class(c):
    return class_label_colormap.index(c)

images=[
    'driving.jpg',
    'rocket.jpg',
    'professional-transport-autos-bridge-traffic-road-rush-hour.jpg'
]

app = dash.Dash(__name__)

def mf():
    fig=utils.make_figure(app.get_asset_url(images[0]),dragmode='drawopenpath')
    fig.update_layout({
    'newshape.line.color': class_to_color(DEFAULT_LABEL_CLASS),
    'newshape.line.width': DEFAULT_LINE_WIDTH,
    'margin': dict(
        l = 0,
        r = 0,
        b = 0,
        t = 0,
        pad = 4)
    })
    print('fig:',fig)
    return fig
fig=mf()

app.layout=html.Div(
    id="app-container",
    children=[
        # Graph
        dcc.Graph(id='graph',
            figure=fig,
            config={'modeBarButtonsToAdd': ['drawrect','drawopenpath', 'eraseshape']},
        ),
        # Store for user created masks
        dcc.Store(id='masks',data=[]),
        #html.Div(id='dummy'),
        # Dropdown for selecting the label class
        dcc.Dropdown(
            id='label-class',
            options=[{'label': t, 'value': t} for t in class_labels],
            value=DEFAULT_LABEL_CLASS,
            clearable=False,
        ),
        # Dropdown for selecting the image
        dcc.Dropdown(
            id='image-selector',
            options=[{'label': t, 'value': app.get_asset_url(t)} for t in images],
            value=app.get_asset_url(images[0]),
            clearable=False,
        )
    ]
)

app.clientside_callback(
"""
function (label_class_value,image_selector_value,figure)
{
    const colormap = %s;
    figure.layout.newshape.line.color = colormap[label_class_value];
    figure.layout.images[0].source = image_selector_value;
    console.log(figure);
    return figure;
}
"""%(str(class_label_colormap),),
    Output('graph','figure'),
    [Input('label-class','value'),
     Input('image-selector','value')],
    [State('graph','figure')]
)

# kept this around: a simpler example

#app.clientside_callback(
#"""
#function (image_selector_value,figure)
#{
#    console.log(figure);
#    return figure;
#}
#""",
#    Output('graph','figure'),
#    [Input('image-selector','value')],
#    [State('graph','figure')]
#)

if __name__ == '__main__':
    app.run_server(debug=True)

