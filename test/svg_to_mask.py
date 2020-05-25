
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

images=[]
for imfile in ['assets/test_masks/%d.json' % (d,) for d in range(3)]:
    # get dictionary describing shape
    with open(imfile,'r') as fd:
        shape=json.load(fd)
    # convert extracted svg path to png data
    pngbytes=shape_utils.shape_to_png(shape=shape,width=WIDTH,height=HEIGHT)
    images.append(PIL.Image.open(io.BytesIO(pngbytes)))

mwidth,mheight=[max([im.size[i] for im in images]) for i in range(2)]
mask = np.zeros((mwidth,mheight), dtype=np.uint8)
print('mask.shape',mask.shape)

imarys=[]
for layer_num,im in enumerate(images):
    # layer 0 is reserved for no mask
    layer_num = (layer_num+1)*LAYER_MUL
    imary=skimage.util.img_as_ubyte(np.array(im))
    imary=np.sum(imary,axis=2).T
    imary.resize((mwidth,mheight))
    imarys.append(imary)
    mask[imary!=0]=layer_num

print(imarys[0][0,0])
    
skimage.io.imsave('/tmp/mask.tiff',mask)
