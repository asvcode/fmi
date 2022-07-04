# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/05_train.ipynb (unless otherwise specified).

__all__ = ['EpochIteration', 'EpochImageCounter']

# Cell
from fastai.vision.all import *
from timm import create_model
from fastai.vision.learner import _update_first_layer

# Cell
class EpochIteration(Callback):
    "Display Epoch and Iteration with option to display images"
    def __init__(self, show_img=False):
        self.show_img = show_img
    def before_batch(self):
        if self.training is not False:
            b = f'Training: Epoch: {self.epoch} Iter: {self.iter} Loss:{self.loss}'
        else:
            b = f'Validation: Epoch: {self.epoch} Iter: {self.iter} Loss:{self.loss}'

        if self.show_img is not False:
            show_images(self.learn.xb[0], suptitle=b)
        else:
            print(b)

# Cell
class EpochImageCounter(Callback):
    "Count the number of images in each class after each training epoch"
    def __init__(self, dls):
        self.r = []
        self.all_i = [i[-1].item() for i in dls.train_ds]
        self.tds = [dls.vocab[i[-1].item()] for i in dls.train_ds]
        print(f'Train DS Size: {len(dls.train_ds)}')
        print(f'Batch Size: {dls.bs}')
    def before_batch(self):
        if self.training is not False:
                [self.r.append(i.item()) for i in self.yb[0]]
    def after_train(self):
        is_in = [dls.vocab[i] for i in self.r if i in self.all_i]
        print(Counter(is_in))