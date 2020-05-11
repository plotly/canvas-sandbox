import plotly.graph_objects as go
import dash
import dash_html_components as html
import dash_core_components as dcc

fig = go.Figure()
text="Click and drag here <br> to draw a rectangle <br><br> or select another shape <br>in the modebar"
fig.add_annotation(
            x=0.5,
            y=0.5,
            text=text,
            xref="paper",
            yref="paper",
            showarrow=False,
            font_size=20
)
# shape defined programatically
fig.add_shape(editable=True,
              x0=-1, x1=0, y0=2, y1=3,
              xref='x1', yref='y1')
# define dragmode and add modebar buttons
fig.update_layout(dragmode='drawrect')
fig.show(config={'modeBarButtonsToAdd':['drawline',
                                        'drawopenpath',
                                        'drawclosedpath',
                                        'drawcircle',
                                        'drawrect',
                                        'eraseshape'
                                       ]})

app = dash.Dash(__name__)
app.layout=html.Div(
        [html.Button("Add Shape",id='button-addshape'),
         dcc.Graph(id='graph',
                  figure=fig,
                  config={'modeBarButtonsToAdd':['drawrect', 'eraseshape']})])
