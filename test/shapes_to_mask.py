# Combine a bunch of shapes into a mask
# The mask is a single channel 8-bit image (so up to 255 mask classes are available)
# the masks are listed from bottom to top, so if overlap occurs between masks,
# the one that comes later in the list will be the one present in the file

import numpy as np
import shape_utils
import json
import PIL.Image
import skimage
import skimage.io
import plot_common

# made up dimensions because we don't have a figure
WIDTH=800
HEIGHT=600

with open('/tmp/shapes.json','r') as fd:
    shapes=json.load(fd)
    
# layer value multiplier so they don't all look white
LAYER_MUL=255/(len(shapes)+1)

shape_args=[{
    'width':WIDTH,
    'height':HEIGHT,
    'shape':s
} for s in shapes]
shape_layers=[(n+1)*LAYER_MUL for n in range(len(shapes))]

mask=shape_utils.shapes_to_mask(shape_args,shape_layers)

skimage.io.imsave('/tmp/mask.tiff',mask)

