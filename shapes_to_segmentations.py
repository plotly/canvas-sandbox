import PIL.Image
import numpy as np
import json
import skimage
import skimage.util
import skimage.io
import skimage.color
from skimage import segmentation
import io
import shape_utils
from image_segmentation import trainable_segmentation
import plotly.express as px


def img_to_ubyte_array(img):
    ret_ = skimage.util.img_as_ubyte(np.array(PIL.Image.open(img)))
    return ret_


def fromhex(n):
    return int(n, base=16)


def label_to_colors(
    img, colormap=px.colors.qualitative.Light24, alpha=128, color_class_offset=0
):
    """
    Take MxN matrix containing integers representing labels and return an MxNx4
    matrix where each label has been replaced by a color looked up in colormap.
    colormap entries must be strings like plotly.express style colormaps.
    alpha is the value of the 4th channel
    color_class_offset allows adding a value to the color class index to force
    use of a particular range of colors in the colormap. This is useful for
    example if 0 means 'no class' but we want the color of class 1 to be
    colormap[0].
    """
    colormap = [
        tuple([fromhex(h[s : s + 2]) for s in range(0, len(h), 2)])
        for h in [c.replace("#", "") for c in colormap]
    ]
    cimg = np.zeros(img.shape[:2] + (3,), dtype="uint8")
    minc = np.min(img)
    maxc = np.max(img)
    for c in range(minc, maxc + 1):
        cimg[img == c] = colormap[(c + color_class_offset) % len(colormap)]
    return np.concatenate(
        (cimg, alpha * np.ones(img.shape[:2] + (1,), dtype="uint8")), axis=2
    )


def grey_labels(img):
    minc = np.min(img)
    maxc = np.max(img)
    img -= minc
    img += 1
    img *= 255 // (maxc - minc + 1)
    return img


def compute_segmentations(
    shapes,
    img_path="assets/segmentation_img.jpg",
    segmenter_args={},
    shape_layers=None,
    label_to_colors_args={},
):

    # load original image
    img = img_to_ubyte_array(img_path)
    blank_img = np.zeros_like(img)

    # load labels
    label_imgs = []
    for shape in shapes:
        lab = img_to_ubyte_array(
            io.BytesIO(
                shape_utils.shape_to_png(
                    shape=shape, width=img.shape[1], height=img.shape[0], write_to=None
                )
            )
        )
        label_imgs.append(lab)

    shape_args = [
        {"width": img.shape[1], "height": img.shape[0], "shape": shape}
        for shape in shapes
    ]
    if (shape_layers is None) or (len(shape_layers) != len(shapes)):
        shape_layers = [(n + 1) for n, _ in enumerate(shapes)]
    mask = shape_utils.shapes_to_mask(shape_args, shape_layers)

    # do segmentation and return this
    seg, clf = trainable_segmentation(img, mask, **segmenter_args)
    color_seg = label_to_colors(seg, **label_to_colors_args)
    # color_seg is a 3d tensor representing a colored image whereas seg is a
    # matrix whose entries represent the classes
    return (color_seg, seg, clf)
