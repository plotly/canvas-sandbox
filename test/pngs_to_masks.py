# Combine a bunch of png into a mask
# The mask is a single channel 8-bit image (so up to 255 mask classes are available)
# the masks are listed from bottom to top, so if overlap occurs between masks,
# the one that comes later in the list will be the one present in the file

import numpy as np
#from PIL import Image
import PIL.Image
import skimage
import skimage.io
import plot_common

images=[]
for imfile in ['assets/test_masks/mask-%d.png' % (d,) for d in range(3)]:
    fd=open(imfile,'rb')
    images.append(PIL.Image.open(fd))

mwidth,mheight=[max([im.size[i] for im in images]) for i in range(2)]
mask = np.zeros((mwidth,mheight), dtype=np.uint8)
print('mask.shape',mask.shape)

imarys=[]
for layer_num,im in enumerate(images):
    # layer 0 is reserved for no mask
    layer_num = 255-layer_num
    imary=skimage.util.img_as_ubyte(np.array(im))
    imary=np.sum(imary,axis=2).T
    imary.resize((mwidth,mheight))
    imarys.append(imary)
    mask[imary!=0]=layer_num

print(imarys[0][0,0])
    
skimage.io.imsave('/tmp/mask.tiff',mask)
