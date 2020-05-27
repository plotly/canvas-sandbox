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
import io
import base64
import PIL.Image

DEFAULT_STROKE_WIDTH = 3 # gives line width of 2^3 = 8

DEFAULT_IMAGE_PATH = "assets/segmentation_img.jpg"

# the number of different classes for labels
NUM_LABEL_CLASSES = 15
DEFAULT_LABEL_CLASS = 0
class_label_colormap = px.colors.qualitative.Light24
class_labels = list(range(NUM_LABEL_CLASSES))
# we can't have less colors than classes
assert NUM_LABEL_CLASSES <= len(class_label_colormap)


def class_to_color(n):
    return class_label_colormap[n]


def color_to_class(c):
    return class_label_colormap.index(c)


app = dash_utils.new_dash_app(__file__)
server = app.server


def mf(
    images=[DEFAULT_IMAGE_PATH],
    stroke_color=class_to_color(DEFAULT_LABEL_CLASS),
    stroke_width=DEFAULT_STROKE_WIDTH,
    shapes=[],
):
    fig = plot_common.dummy_fig()
    plot_common.add_layout_images_to_fig(fig, images)
    fig.update_layout(
        {
            "dragmode": "drawopenpath",
            "shapes": shapes,
            "newshape.line.color": stroke_color,
            "newshape.line.width": stroke_width,
            "margin": dict(l=0, r=0, b=0, t=0, pad=4),
        }
    )
    return fig


def shapes_to_key(shapes):
    return json.dumps(shapes)


def store_shapes_seg_pair(d, key, seg, remove_old=True):
    """
    Stores shapes and segmentation pair in dict d
    seg is a PIL.Image object
    if remove_old True, deletes all the old keys and values.
    """
    # TODO alternatively, if given a numpy array, we could serialize its raw
    # representation
    bytes_to_encode = io.BytesIO()
    seg.save(bytes_to_encode, format="png")
    bytes_to_encode.seek(0)
    data = base64.b64encode(bytes_to_encode.read()).decode()
    if remove_old:
        return {key: data}
    d[key] = data
    return d


def look_up_seg(d, key):
    """ Returns a PIL.Image object """
    data = d[key]
    img_bytes = base64.b64decode(data)
    img = PIL.Image.open(io.BytesIO(img_bytes))
    return img


app.layout = html.Div(
    id="app-container",
    children=[
        # Graph
        dcc.Graph(
            id="graph",
            figure=mf(),
            config={"modeBarButtonsToAdd": ["drawrect", "drawopenpath", "eraseshape"]},
        ),
        # Store for user created masks
        # data is a list of dicts describing shapes
        dcc.Store(id="masks", data={"shapes": []}),
        # Store for storing segmentations from shapes
        # the keys are hashes of shape lists and the data are pngdata
        # representing the corresponding segmentation
        # this is so we can download annotations and also not recompute
        # needlessly old segmentations
        dcc.Store(id="segmentation", data={}),
        html.H6("Label class"),
        # Dropdown for selecting the label class
        dcc.Dropdown(
            id="label-class",
            options=[{"label": t, "value": t} for t in class_labels],
            value=DEFAULT_LABEL_CLASS,
            clearable=False,
        ),
        html.H6(id="stroke-width-display"),
        # Slider for specifying stroke width
        dcc.Slider(id="stroke-width", min=0, max=6, step=0.1, value=DEFAULT_STROKE_WIDTH),
        # Indicate showing most recently computed segmentation
        dcc.Checklist(
            id="show-segmentation",
            options=[{"label": "Show segmentation", "value": "Show segmentation"}],
            value=[],
        ),
        html.Div(id="dummy"),
    ],
)


def show_segmentation(fig, image_path, mask_shapes):
    """ adds an image showing segmentations to a figure's layout """
    segimg = compute_segmentations(mask_shapes, img_path=image_path)[0]
    segimgpng = plot_common.img_array_to_pil_image(segimg)
    return segimgpng


@app.callback(
    [
        Output("graph", "figure"),
        Output("masks", "data"),
        Output("segmentation", "data"),
        Output("stroke-width-display","children")
    ],
    [
        Input("graph", "relayoutData"),
        Input("label-class", "value"),
        Input("stroke-width", "value"),
        Input("show-segmentation", "value"),
    ],
    [State("masks", "data"), State("segmentation", "data")],
)
def annotation_react(
    graph_relayoutData,
    label_class_value,
    stroke_width_value,
    show_segmentation_value,
    masks_data,
    segmentation_data,
):
    cbcontext = [p["prop_id"] for p in dash.callback_context.triggered][0]
    if cbcontext == "graph.relayoutData" and "shapes" in graph_relayoutData.keys():
        masks_data["shapes"] = graph_relayoutData["shapes"]
    images = [DEFAULT_IMAGE_PATH]
    stroke_width=int(round(2**(stroke_width_value)))
    fig = mf(
        stroke_color=class_to_color(label_class_value),
        stroke_width=stroke_width,
        shapes=masks_data["shapes"],
    )
    if ("Show segmentation" in show_segmentation_value) and (
        len(masks_data["shapes"]) > 0
    ):
        # to store segmentation data in the store, we need to base64 encode the
        # PIL.Image and hash the set of shapes to use this as the key
        # to retrieve the segmentation data, we need to base64 decode to a PIL.Image
        # because this will give the dimensions of the image
        sh = shapes_to_key(masks_data["shapes"])
        if sh in segmentation_data.keys():
            print("key found")
            segimgpng = look_up_seg(segmentation_data, sh)
        else:
            print("computing new segmentation")
            try:
                segimgpng = show_segmentation(
                    fig, DEFAULT_IMAGE_PATH, masks_data["shapes"]
                )
                segmentation_data = store_shapes_seg_pair(
                    segmentation_data, sh, segimgpng
                )
            except ValueError:
                # if segmentation fails, draw nothing
                segimgpng = None
        images_to_draw = []
        if segimgpng is not None:
            images_to_draw = [segimgpng]
        fig = plot_common.add_layout_images_to_fig(fig, images_to_draw)
    return (fig, masks_data, segmentation_data, "Stroke width: %d"%(stroke_width,))


if __name__ == "__main__":
    app.run_server(debug=True)
