# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/06_examine.ipynb (unless otherwise specified).

__all__ = ['visualize_layers']

# Cell
from fastai.layers import flatten_model
from fastai.vision.all import *

# Cell
def visualize_layers(fn, nrows=5, ncols=5):
    "Visualize how an image is transformed as it goes through the layers in the model"
    img_list = []; size_list = []
    head_layer = flatten_model(learn.model[0])
    print(f'Number of Layers: {len(head_layer)}')
    for layer in head_layer:
        layer_name = str(layer)
        custom_hook = hook_output(layer)
        learn.predict(fn)
        activation = custom_hook.stored[0][0]
        layimg = TensorImage(activation)
        sh = layimg.shape
        img_list.append(layimg)
        size_list.append(sh)
    show_images(img_list, titles=size_list, nrows=nrows, ncols=ncols);