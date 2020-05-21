import dash
from dash.dependencies import Input, Output, State, ClientsideFunction
import dash_html_components as html
import dash_core_components as dcc
import utils
import shape_utils
import plot_common

# specify __root__ as app name to force looking for assets/ folder in directory
# where python was invoked from.
app = dash.Dash("__root__")

print('app_asset_url:',app.get_asset_url('driving.jpg'))
def mf():
    fig=utils.make_figure(app.get_asset_url('driving.jpg'),dragmode='drawopenpath')
    fig.update_layout({
    'newshape.line.color': 'LightSeaGreen',
    'newshape.line.width': 10,
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
            config={'modeBarButtonsToAdd': ['drawopenpath', 'eraseshape']},
        ),
        html.Div(id='dummy')
    ]
)

@app.callback(
[Output('dummy','children'),
 Output('graph','figure')],
[Input('graph','relayoutData')])
def show_line_data(graph_relayoutData):
    fig=mf()
    if (graph_relayoutData is not None):
        print('graph_relayoutData:',graph_relayoutData)
        if ('shapes' in graph_relayoutData.keys()):
            for i,shape in enumerate(graph_relayoutData['shapes']):
                r=shape_utils.shape_to_png(fig,shape,write_to='/tmp/%d.png'%(i,))
            fig.update_layout({
                'shapes': graph_relayoutData['shapes']
            })

    return ("",fig)


if __name__ == '__main__':
    app.run_server(debug=True)
