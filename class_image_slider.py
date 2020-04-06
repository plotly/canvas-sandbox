import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash

from skimage import data
from skimage import img_as_ubyte

import plotly.graph_objects as go
import plotly.express as px

# For timestamps
from time import time

img = img_as_ubyte(data.binary_blobs(length=256, n_dim=3))

app = dash.Dash(__name__)


class Slicer():

    def __init__(self, app, img, id='slicer', width=None):
        self.img = img
        self.shape = self.img.shape
        self._slider = dcc.Slider(id=id + '_slider',
                                  min=0, max=self.shape[0] - 1,
                                  value=self.shape[0] // 2)
        self._input = dcc.Input(id=id + '_input', type='number',
                                  min=0, max=self.shape[0] - 1,
                                  value=self.shape[0] // 2)
        self._graph = dcc.Graph(id=id + '_graph')
        self._timer = dcc.Store(id=id + '_timer', data=time())
        self.layout = html.Div(children=[self._graph,
                                         self._input,
                                         self._slider,
                                         self._timer],
                               style={'width':'50%'})
        if app.config.suppress_callback_exceptions:
            self.wrap()


    def update_slider(self, i):
        fig = px.imshow(img[i])
        return fig


    def update_input(self, i):
        return i


    def wrap(self, app):
        @app.callback([Output(self._graph.id, 'figure'),
                       Output(self._input.id, 'value')], 
                      [Input(self._slider.id, 'value')],
                      [State(self._timer.id, 'data')])
        def callback_wrapper(val, timer):
            t = time()
            print(t, timer)
            if (t - timer) < 1000:
                return self.update_slider(val), dash.no_update
            else:
                return self.update_slider(val), val

        @app.callback([Output(self._slider.id, 'value'),
                       Output(self._timer.id, 'data')],
                      [Input(self._input.id, 'value')])
        def callback_wrapper_input(val):
            return self.update_input(val), time()




comp = Slicer(app, img)

app.layout = comp.layout

comp.wrap(app)

if __name__ == '__main__':
    app.run_server(debug=True, port=8099)

