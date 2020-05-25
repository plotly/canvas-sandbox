import plotly.express as px
import dash
from dash.dependencies import Input, Output, State, ClientsideFunction
import dash_html_components as html
import dash_core_components as dcc
import dash_utils
import utils
import shape_utils
import plot_common
from PIL import Image
import json
from shapes_to_segmentations import compute_segmentations

DEFAULT_LINE_WIDTH=5

DEFAULT_IMAGE_PATH='assets/segmentation_img.jpg'

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

app = dash_utils.new_dash_app(__file__)
server=app.server
print('root_path:',app.server.root_path)
print('assets_folder:',app.config['assets_folder'])

def mf(images=[Image.open(DEFAULT_IMAGE_PATH)],
       stroke_color=class_to_color(DEFAULT_LABEL_CLASS),
       stroke_width=DEFAULT_LINE_WIDTH,
       shapes=[]):
    fig=plot_common.dummy_fig()
    plot_common.add_layout_images_to_fig(fig,images)
    fig.update_layout({
        'dragmode': 'drawopenpath',
        'shapes': shapes,
        'newshape.line.color': stroke_color,
        'newshape.line.width': stroke_width,
        'margin': dict(
            l = 0,
            r = 0,
            b = 0,
            t = 0,
            pad = 4)
    })
    print('fig:',fig)
    return fig

app.layout=html.Div(
    id="app-container",
    children=[
        # Graph
        dcc.Graph(id='graph',
            figure=mf(),
            config={'modeBarButtonsToAdd': ['drawrect','drawopenpath', 'eraseshape']},
        ),
        # Store for user created masks
        # data is a list of dicts describing shapes
        dcc.Store(id='masks',data={'shapes':[]}),
        # Store for storing most recently computed segmentation
        # data is label_class: base64_encoded_png pairs where label_class is the
        # key
        dcc.Store(id='segmentation',data={}), 
        html.H6('Label class'),
        # Dropdown for selecting the label class
        dcc.Dropdown(
            id='label-class',
            options=[{'label': t, 'value': t} for t in class_labels],
            value=DEFAULT_LABEL_CLASS,
            clearable=False,
        ),
        html.H6('Stroke width'),
        # Slider for specifying stroke width
        dcc.Slider(
            id='stroke-width',
            min=1,
            max=10,
            step=1,
            value=1
        ),
        # Indicate showing most recently computed segmentation
        dcc.Checklist(
            id='show-segmentation',
            options=[
                {'label': 'Show segmentation', 'value': 'Show segmentation'}
            ],
            value=[]
        ),
        html.Div(id='dummy')
    ]
)

def show_segementation(fig,
                       image_path,
                       mask_shapes):
    """ adds an image showing segmentations to a figure's layout """
    segimg=compute_segmentations(mask_shapes,img_path=image_path)[0]
    segimgpng=plot_common.img_array_to_pil_image(segimg)
    return plot_common.add_layout_images_to_fig(fig,[segimgpng])

@app.callback(
    [Output('graph','figure'),
     Output('masks','data'),
     Output('segmentation','data')],
    [Input('graph','relayoutData'),
     Input('label-class','value'),
     Input('stroke-width','value'),
     Input('show-segmentation','value')],
    [State('masks','data'),
     State('segmentation','data')]
)
def annotation_react(
    graph_relayoutData,
    label_class_value,
    stroke_width_value,
    show_segmentation_value,
    masks_data,
    segmentation_data):
    cbcontext = [p['prop_id'] for p in dash.callback_context.triggered][0]
    print('graph_relayoutData',graph_relayoutData)
    if cbcontext == 'graph.relayoutData' and 'shapes' in graph_relayoutData.keys():
        masks_data['shapes']=graph_relayoutData['shapes']
    images=[Image.open(DEFAULT_IMAGE_PATH)]
    fig=mf(stroke_color=class_to_color(label_class_value),
           stroke_width=stroke_width_value,
           shapes=masks_data['shapes'])
    if 'Show segmentation' in show_segmentation_value:
        fig=show_segementation(fig,DEFAULT_IMAGE_PATH,masks_data['shapes'])
    with open('/tmp/shapes.json','w') as fd:
        json.dump(masks_data['shapes'],fd)
    return (fig,masks_data,dash.no_update)

if __name__ == '__main__':
    app.run_server(debug=True)

