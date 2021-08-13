# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/06_examine.ipynb (unless otherwise specified).

__all__ = ['visualize_layers', 'view_layers', 'Hook', 'HookBwd', 'view_activations', 'get_cmaps', 'get_boxes']

# Cell
from fastai.layers import flatten_model
from fastai.vision.all import *
from .explore import draw_outline, draw_rect, TensorBBox, LabeledBBox
import pydicom

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
def view_layers(image, layer:int, layers, learn, nrows=1, imgs=1, stats=False):
    lsl = []
    custom_hook = hook_outputs(layers)
    pre = learn.predict(image)
    _,s,w,h = custom_hook.stored[layer].shape
    for i in range(s):
        acts = custom_hook.stored[layer][0][i]
        lsl.append(acts)
    if stats is not False:
        print(f'Layer: {layers[layer]}')
        print(f'Number of activations: {s}')
        print(f'Image shape: {w, h}')
    show_images(lsl[:imgs], nrows=nrows)

# Cell
class Hook():
    def __init__(self, m):
        self.hook = m.register_forward_hook(self.hook_func)
    def hook_func(self, m, i, o): self.stored = o.detach().clone()
    def __enter__(self, *args): return self
    def __exit__(self, *args): self.hook.remove()

# Cell
class HookBwd():
    def __init__(self, m):
        self.hook = m.register_backward_hook(self.hook_func)
    def hook_func(self, m, gi, go): self.stored = go[0].detach().clone()
    def __enter__(self, *args): return self
    def __exit__(self, *args): self.hook.remove()

# Cell
def view_activations(x, cls, dls, learn, layer):
    "View activations by layer by image"
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
    ax.imshow(cam_map.detach().cpu(), alpha=0.6, extent=(0,x_dec.shape[1],x_dec.shape[2],0),
              interpolation='bilinear', cmap='magma');

# Cell
def get_cmaps(fn, dls, learn, layer, sanity=False, show_maps=False, show_cmap=False):
    "view cmaps for all classes in an image"
    cf = []; ci = []
    try:
        x, = first(dls.test_dl([fn]))
        x_dec = TensorImage(dls.train.decode((x,))[0][0])
        c = len(dls.vocab)
        cl, pred, probs = learn.predict(fn)
        oo = L(torch.topk(probs, c))
        if sanity is not False:
            print(f'{cl}\n{oo[-1]}\n{oo[0]}')
        for i in range(c):
            with HookBwd(layer) as hookg:
                with Hook(layer) as hook:
                    output = learn.model.eval()(x.cuda())
                    act = hook.stored
                output[0, oo[-1][i]].backward()
                grad = hookg.stored
            w = grad[0].mean(dim=[1,2], keepdim=True)
            cam_map = (w * act[0]).sum(0)
            cf.append(cam_map)
            ci.append([oo[-1][i].item(), format(oo[0][i].item(), '.2f')])

        if show_maps is not False:
            show_images(cf, titles=ci, suptitle=cl)

        if show_cmap is not False:
            for file in cf:
                _,ax = plt.subplots()
                x_dec.show(ctx=ax)
                ax.imshow(file.detach().cpu(), alpha=0.6, extent=(0, x_dec.shape[1], x_dec.shape[2],0),
                          interpolation='bilinear', cmap='magma');
    except RuntimeError:
        print('error')

# Cell
def get_boxes(fn, dls, learn, layer, sanity=False, show_maps=False, show_img=False, color='white'):
    "Get the location of bounding boxes in each class within an image"
    cf = []; ci = []; ar = []
    try:
        x, = first(dls.test_dl([fn]))
        x_dec = TensorImage(dls.train.decode((x,))[0][0])
        imz = pydicom.dcmread(fn).pixel_array
        c = len(dls.vocab)
        cl, pred, probs = learn.predict(fn)
        oo = L(torch.topk(probs, c))
        for i in range(c):
            with HookBwd(layer) as hookg:
                with Hook(layer) as hook:
                    output = learn.model.eval()(x.cuda())
                    act = hook.stored
                output[0, oo[-1][i]].backward()
                grad = hookg.stored
            w = grad[0].mean(dim=[1,2], keepdim=True)
            cam_map = (w * act[0]).sum(0)
            cf.append(cam_map)
            ci.append([oo[-1][i].item(), format(oo[0][i].item(), '.2f')])
            cms = cam_map.shape[0]
            xx = imz.shape[1] // cms
            yy = imz.shape[0] // cms
            t = np.array(cam_map.cpu())
            tr = tensor(t)
            val = []
            for i in range(0, tr.shape[0]):
                index, value = max(enumerate(tr[i]), key=operator.itemgetter(1))
                val.append(value)
                y_index, y_value = max(enumerate(val), key=operator.itemgetter(1))
                x_index, x_value = max(enumerate(tr[y_index]), key=operator.itemgetter(1))
                xx1 = x_index * xx
                yy1 = y_index * yy
                array_ = np.array([xx1, yy1, (xx1 + (imz.shape[0]//cms)), (yy1 + (imz.shape[1]//cms))])
            ar.append(array_)
        comb = L(oo[-1], oo[0], ar)
        if sanity is not False:
            print(f'Predicted: {cl}\n{oo[-1]}\nProbs: {oo[0]}\nArray Boxes: {ar}')
            for a, b, c in zip(comb[0], comb[1], comb[-1]): print(f'\n{a}\nTensor: {b}\nBox: {c}')
        if show_maps is not False:
            show_images(cf, titles=ci, suptitle=f'Predicted: {cl}')
        if show_img is not False:
            ctx = show_image(imz)
            box = LabeledBBox(TensorBBox(comb[-1]), comb[0])
            box.show(ctx=ctx, color=color)
        return ar
    except RuntimeError:
        print('error')