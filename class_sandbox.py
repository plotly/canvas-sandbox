import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash

app = dash.Dash(__name__)


class SliderInput():

    def __init__(self, app, id='slider_input'):
        self._slider = dcc.Slider(id=id + '_slider')
        self._input = dcc.Input(id=id + '_input')
        self.layout = html.Div(children=[self._slider, self._input])
        if app.config.suppress_callback_exceptions:
            self.wrap()


    def update_slider(self, i):
        return i


    def wrap(self, app):
        @app.callback(Output(self._input.id, 'value'), 
                      [Input(self._slider.id, 'value')])
        def callback_wrapper(val):
            return self.update_slider(val)



comp = SliderInput(app)

app.layout = comp.layout

comp.wrap(app)

if __name__ == '__main__':
    app.run_server(debug=True, port=8099)

