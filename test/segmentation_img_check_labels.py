# Just checking to see if the labels we will use to test the image segmentation
# are matching etc.

import shapes_to_segmentations
import json

with open('assets/segmentation_img_labels.json','r') as fd:
    shapes=json.load(fd)
shapes_to_segmentations.compute_segmentations(shapes,
                                              write_debug_images=True)

