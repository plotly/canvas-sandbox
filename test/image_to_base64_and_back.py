import numpy as np
import skimage.data
import plot_common
import base64
import PIL.Image
import io

origimg=skimage.data.astronaut()
img=np.concatenate((origimg,
                    np.ones(origimg.shape[:2]+(1,),dtype=origimg.dtype)*128),axis=2)

imgpng=plot_common.img_array_to_pil_image(img)

bytes_to_encode=io.BytesIO()
imgpng.save(bytes_to_encode,format='png')
bytes_to_encode.seek(0)
imgpngb64=base64.b64encode(bytes_to_encode.read()).decode()
imgpng_bytes=base64.b64decode(imgpngb64)
imgpng2=PIL.Image.open(io.BytesIO(imgpng_bytes))
imgpng2.save('/tmp/imgpng2.png')

print('hi')
