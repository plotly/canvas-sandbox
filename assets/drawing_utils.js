function set_stroke_color(graph_div,color) {
    Plotly.relayout(graph_div,{
        'newshape.line.color': color
    });
}

