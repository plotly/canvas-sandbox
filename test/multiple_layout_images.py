import dash
from dash.dependencies import Input, Output, State, ClientsideFunction
import dash_html_components as html
import dash_core_components as dcc
import utils
import shape_utils
import plot_common
import numpy as np

im_shape=(300,400,4)

def new_mask():
    mask=np.zeros(im_shape, dtype=np.uint8)
    if im_shape[2] > 3:
        mask[:,:,3]=0
    return mask


app = dash.Dash("__root__")

fig=plot_common.dummy_fig()

mask1,mask2=[new_mask() for _ in range(2)]
mask1[100:200,100:200,0]=150
mask1[100:200,100:200,3]=128
mask2[150:250,175:350,1]=200
mask2[150:250,175:350,3]=128
images=[plot_common.img_array_to_pil_image(im) for im in [mask1,mask2]]

fig=plot_common.add_layout_images_to_fig(fig,images)

app.layout=html.Div(
    id="app-container",
    children=[
        # Graph
        dcc.Graph(id='graph',
            figure=fig,
            config={'modeBarButtonsToAdd': ['drawopenpath', 'eraseshape']},
        ),
        html.Div(id='dummy')
    ]
)

if __name__ == '__main__':
    app.run_server(debug=True)
