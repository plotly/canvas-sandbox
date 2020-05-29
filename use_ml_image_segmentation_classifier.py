__doc__ = """
Use the classifier that you downloaded from the ml_image_segmentation.py webapp.
Specify files to use on the command line like so:

    CLF_PATH=path/to/classifier.json \\
    IMG_PATH=path/to/image/to/classify.some_image_ending \\
    OUT_IMG_PATH=path/to/where/to/put/classified/image.some_image_ending \\
    python use_ml_image_segmentation_classifier.py

some_image_ending can be a common image format's ending, e.g., png or jpg

"""

import os
import plot_common
import shapes_to_segmentations
import pickle
import image_segmentation
import base64
import io
import skimage.io
import json


def getenv(e):
    try:
        return os.environ[e]
    except KeyError:
        print(__doc__)
        raise


def use_img_classifier_in_mem(
    clf, segmenter_args, label_to_colors_args, img_path, out_img
):
    img = skimage.io.imread(img_path)
    seg, clf = image_segmentation.trainable_segmentation(img, clf=clf, **segmenter_args)
    color_seg = shapes_to_segmentations.label_to_colors(seg, **label_to_colors_args)
    segimgpil = plot_common.img_array_to_pil_image(color_seg)
    segimgpil.save(out_img)


def use_img_classifier(clf_file, img_path, out_img):
    """
    clf_file contains the classifier and other parameters (see below)
    img contains the image we want to run the classifier on
    """
    with open(clf_file, "rb") as fd:
        classr = json.load(fd)
    clfb64 = classr["classifier"]
    segmenter_args = classr["segmenter_args"]
    label_to_colors_args = classr["label_to_colors_args"]
    clf = pickle.load(io.BytesIO(base64.b64decode(clfb64)))
    use_img_classifier_in_mem(
        clf, segmenter_args, label_to_colors_args, img_path=img_path, out_img=out_img
    )


if __name__ == "__main__":
    clf_path = getenv("CLF_PATH")
    img_path = getenv("IMG_PATH")
    out_img_path = getenv("OUT_IMG_PATH")
    use_img_classifier(clf_path, img_path, out_img_path)
