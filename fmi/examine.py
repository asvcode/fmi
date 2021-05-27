# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/06_examine.ipynb (unless otherwise specified).

__all__ = ['visualize_layers', 'view_layers', 'view_activations']

# Cell
from fastai.layers import flatten_model
from fastai.vision.all import *

# Cell
def visualize_layers(fn, learn, nrows=5, ncols=5):
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

# Cell
def view_layers(image, layer:int, layers, learn):
    lsl = []
    custom_hook = hook_outputs(layers)
    pre = learn.predict(image)
    _,s,w,h = custom_hook.stored[layer].shape
    for i in range(s):
        acts = custom_hook.stored[layer][0][i]
        lsl.append(acts)
    print(f'Layer: {layers[layer]}')
    print(f'Number of activations: {s}')
    print(f'Image shape: {w, h}')
    show_images(lsl, nrows=1)

# Cell
def view_activations(dls, learn, layer):
    "View activations by layer by image"
    print(layer)
    with HookBwd(layer) as hookg:
        with Hook(layer) as hook:
            output = learn.model.eval()(x.cuda())
            act = hook.stored
        output[0,cls].backward()
        grad = hookg.stored

    w = grad[0].mean(dim=[1,2], keepdim=True)
    cam_map = (w * act[0]).sum(0)

    x_dec = TensorImage(dls.train.decode((x,))[0][0])

    _,ax = plt.subplots()
    x_dec.show(ctx=ax)
    ax.imshow(cam_map.detach().cpu(), alpha=0.6, extent=(0,224,224,0),
              interpolation='bilinear', cmap='magma');