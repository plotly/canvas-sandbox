from cairosvg import svg2png

def shape_to_svg_code(fig,shape):
    """
    fig is the figure which shape resides in (to get width and height) and shape
    is one of the shapes the figure contains.
    """
    # get width and height
    wrange=next(fig.select_xaxes())['range']
    hrange=next(fig.select_yaxes())['range']
    width,height=[max(r)-min(r) for r in [wrange,hrange]]
    fmt_dict=dict(
        width=width,
        height=height,
        stroke_color=shape['line']['color'],
        stroke_width=shape['line']['width'],
        path=shape['path']
    )
    return """
<svg
    width="{width}" 
    height="{height}" 
    viewBox="0 0 {width} {height}" 
>
<path
    stroke="{stroke_color}"
    stroke-width="{stroke_width}"
    d="{path}"
    fill-opacity="0"
/>
</svg>
""".format(**fmt_dict)

def shape_to_png(fig,shape,write_to=None):
    """
    Like svg2png, if write_to is None, returns a bytestring. If it is a path
    to a file it writes to this file and returns None.
    """
    svg_code=shape_to_svg_code(fig,shape)
    r=svg2png(bytestring=svg_code,write_to=write_to)
    return r
