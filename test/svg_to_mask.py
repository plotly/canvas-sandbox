
# Combine a bunch of svg into a mask
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
import io

# made up dimensions because we don't have a figure
WIDTH=400
HEIGHT=300
# layer value multiplier so they don't all look white
LAYER_MUL=60

shapes=[]
for imfile in ['assets/test_masks/%d.json' % (d,) for d in range(3)]:
    # get dictionary describing shape
    with open(imfile,'r') as fd:
        shape=json.load(fd)
    shapes.append(shape)

shape_args=[{
    'width':WIDTH,
    'height':HEIGHT,
    'shape':s
} for s in shapes]
shape_layers=[(n+1)*LAYER_MUL for n in range(len(shapes))]

mask=shape_utils.shapes_to_mask(shape_args,shape_layers)

skimage.io.imsave('/tmp/mask.tiff',mask)
