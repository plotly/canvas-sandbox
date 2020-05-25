# Just checking to see if the labels we will use to test the image segmentation
# are matching etc.

import PIL.Image
import numpy as np
import json
import skimage
import skimage.util
import skimage.io
import io
import shape_utils
from image_segmentation import trainable_segmentation
from skimage import segmentation
import plotly.express as px


def img_to_ubyte_array(img):
    ret_=skimage.util.img_as_ubyte(np.array(PIL.Image.open(img)))
    return ret_

def fromhex(n):
    return int(n,base=16)

def label_to_colors(img,colormap=px.colors.qualitative.Light24):
    """
    Take MxN matrix containing integers representing labels and return an MxNx3
    matrix where each label has been replaced by a color looked up in colormap.
    colormap entries must be strings like plotly.express style colormaps.
    """
    colormap=[tuple([fromhex(h[s:s+2]) for s in range(0,len(h),2)])
           for h in [c.replace('#','') for c in colormap]]
    cimg=np.zeros(img.shape[:2]+(3,),dtype='uint8')
    minc=np.min(img)
    maxc=np.max(img)
    for c in range(minc,maxc+1):
        cimg[img==c]=colormap[c%len(colormap)]
    return cimg

if __name__ == '__main__':

    # load original image
    img=img_to_ubyte_array('assets/segmentation_img.jpg')
    blank_img=np.zeros_like(img)
    print('img.shape',img.shape)

    # load labels
    label_imgs=[]
    with open('assets/segmentation_img_labels.json','r') as fd:
        shapes=json.load(fd)
    for shape in shapes:
        lab=img_to_ubyte_array(
            io.BytesIO(
                shape_utils.shape_to_png(
                    shape=shape,
                    width=img.shape[1],
                    height=img.shape[0],
                    write_to=None
                )
            )
        )
        print('lab.shape',lab.shape)
        label_imgs.append(lab)

    # make image where labels are superimposed on image
    for lab in label_imgs:
        lab_=lab[:,:,:img.shape[2]]
        labmsk=lab[:,:,3]!=0
        img[labmsk]=lab_[labmsk]
        blank_img[labmsk]=lab_[labmsk]

    skimage.io.imsave('/tmp/overlay.tiff',img)
    skimage.io.imsave('/tmp/labels_only.tiff',blank_img)

    shape_args=[{
        'width': img.shape[1],
        'height': img.shape[0],
        'shape': shape
    } for shape in shapes]
    shape_layers=[(n+1) for n,_ in enumerate(shapes)]
    mask=shape_utils.shapes_to_mask(shape_args,shape_layers)

    # do segmentation and plot it (export the image)
    seg,clf=trainable_segmentation(img, mask.T)
    skimage.io.imsave('/tmp/segmentation.tiff',
    label_to_colors(seg))
