# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/02_explore.ipynb (unless otherwise specified).

__all__ = ['system_info', 'random_', 'get_image_info', 'get_pii', 'instance_sort', 'instance_dcmread', 'instance_show',
           'scaled_px', 'get_dicom_image', 'dicom_convert_3channel', 'show_aspects']

# Cell
from fastai.vision.all import *
from fastai.medical.imaging import *
from torchvision.utils import save_image
import imageio
matplotlib.rcParams['image.cmap'] = 'bone'

from .pipeline import *

# Cell
def system_info():
    RED = '\033[31m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    BOLD   = '\033[1m'
    ITALIC = '\033[3m'
    RESET  = '\033[0m'

    import fastai; print(BOLD + BLUE + "fastai Version: " + RESET + ITALIC + str(fastai.__version__))
    import fastcore; print(BOLD + BLUE + "fastcore Version: " + RESET + ITALIC + str(fastcore.__version__))
    import sys; print(BOLD + BLUE + "python Version: " + RESET + ITALIC + str(sys.version))
    import torchvision; print(BOLD + BLUE + "torchvision: " + RESET + ITALIC + str(torchvision.__version__))
    import torch; print(BOLD + BLUE + "torch version: " + RESET + ITALIC + str(torch.__version__))
    print(BOLD + BLUE + "\nCuda: " + RESET + ITALIC + str(torch.cuda.is_available()))
    print(BOLD + BLUE + "cuda Version: " + RESET + ITALIC + str(torch.version.cuda))
    try:
        print(BOLD + BLUE + "GPU: " + RESET + ITALIC + str(torch.cuda.get_device_name(0)))
    except RuntimeError:
        print(BOLD + BLUE + "No GPU selected" )
    try:
        import pydicom; print(BOLD + BLUE + "\npydicom Version: " + RESET + ITALIC + str(pydicom.__version__))
    except RuntimeError:
        print('Pydicom is not installed')
    try:
        import kornia; print(BOLD + BLUE + "kornia Version: " + RESET + ITALIC + str(kornia.__version__))
    except RuntimeError:
        print('Kornia is not installed')

# Cell
def random_(items, value=10):
    "Helper to generate a random list"
    randomList = []
    for i in range(0,value):
        randomList.append(random.randint(0,len(items)))
    return items[randomList]

# Cell
def get_image_info(file: (L)):
    "Display image specific identifiers in the head of the dicom"
    dcm = file.dcmread()
    try:
        print(f'{dcm[0x08, 0x60]}')
    except KeyError:
        print('No Modality')
    try:
        print(f'{dcm[0x28, 0x04]}')
    except KeyError:
        print('No Photometric Interpretation')
    try:
        print(f'{dcm[0x28, 0x30]}')
    except KeyError:
        print('No Pixel Spacing')
    try:
        print(f'{dcm[0x18, 0x50]}')
    except KeyError:
        print('No SliceThickness')
    try:
        print(f'{dcm[0x28, 0x100]}')
    except KeyError:
        print('No Bits Allocated')
    try:
        print(f'{dcm[0x28, 0x1052]}')
    except KeyError:
        print('No Rescale Intercept')
    try:
        print(f'{dcm[0x28, 0x1053]}')
    except KeyError:
        print('No Rescale Slope')

# Cell
def get_pii(file: (L)):
    "Disply any patient identifiable identifiers in the head of the dicom"
    dcm = file.dcmread()
    try:
        print(f'{dcm[0x10, 0x10]}')
    except KeyError:
        print('No Patient Name')
    try:
        print(f'{dcm[0x10, 0x30]}')
    except KeyError:
        print('No Patient Birth Date')
    try:
        print(f'{dcm[0x10, 0x40]}')
    except KeyError:
        print('No Patient Sex')
    try:
        print(f'{dcm[0x10, 0x1010]}')
    except KeyError:
        print('No patient Age')
    try:
        print(f'{dcm[0x20, 0x4000]}')
    except KeyError:
        print('No Image Comments')

# Cell
def instance_sort(folder:(Path, L)):
    "Helper to sort files by instance number/ID"
    if isinstance(folder, Path): folder = get_dicom_files(folder)
    if isinstance(folder, L): folder = folder
    sorted_files = []
    for file in folder:
        instance = file.dcmread()[0x20, 0x13].value
        sorted_files.append([instance, file])
    return L(sorted(sorted_files))

# Cell
def instance_dcmread(folder:(L)):
    "instance dcmread"
    file = [dcmread(o[1]) for o in folder]
    return file

# Cell
def instance_show(folder: (L), nrows=1):
    "Helper to display sorted files by instance number"
    f_list = []; t_list = []
    for file in instance_sort(folder):
        f = TensorDicom(file[1].dcmread().pixel_array)
        f_list.append(f); t_list.append(file[0])
    return show_images(f_list, titles=t_list, nrows=nrows)

# Cell
@patch(as_prop=True)
def scaled_px(self:DcmDataset):
    "`pixels` scaled by `RescaleSlope` and `RescaleIntercept`"
    img = self.pixels
    if hasattr(self, 'RescaleSlope') and hasattr(self, 'RescaleIntercept') is not None:
        return img * self.RescaleSlope + self.RescaleIntercept
    else: return img

# Cell
@patch
def show(self:DcmDataset, frames=1, scale=True, cmap=plt.cm.bone, min_px=-1100, max_px=None, **kwargs):
    "Adds functionality to view dicom images where each file may have more than 1 frame"
    px = (self.windowed(*scale) if isinstance(scale,tuple)
          else self.hist_scaled(min_px=min_px,max_px=max_px,brks=scale) if isinstance(scale,(ndarray,Tensor))
          else self.hist_scaled(min_px=min_px,max_px=max_px) if scale
          else self.scaled_px)
    if px.ndim > 2:
        gh=[]
        p = px.shape; print(f'{p[0]} frames per file')
        for i in range(frames): u = px[i]; gh.append(u)
        show_images(gh, **kwargs)
    else: show_image(px, cmap=cmap, **kwargs)

# Cell
def get_dicom_image(df, key, nrows=1, source=None, folder_val=None, instance_val=None):
    "Helper to view images by key"
    imgs=[]
    title=[]
    for i in df.index:
        file_path = Path(f"{source}/{df.iloc[i][folder_val]}/{df.iloc[i][instance_val]}.dcm")
        dcc = file_path.dcmread().pixel_array
        imgs.append(dcc)
        pct = df.iloc[i][key]
        title.append(pct)
    return show_images(imgs, titles=title, nrows=nrows)

# Cell
def dicom_convert_3channel(fn:(Path,str), save_dir, show=False, save=False, win1=dicom_windows.lungs, \
                           win2=dicom_windows.liver, win3=dicom_windows.brain):
    "Split a dicom image into 3 windows with one window per channel and saved as jpg"
    data = fn.dcmread()
    file_name = str(fn); name = file_name.split('\\')[-1].split('.')[0]

    chan_one = np.expand_dims(data.windowed(*win1), axis=2)
    chan_two = np.expand_dims(data.windowed(*win2), axis=2)
    chan_three = np.expand_dims(data.windowed(*(win3)), axis=2)
    image = np.concatenate([chan_one, chan_two, chan_three], axis=2)
    ten_image = TensorImage(image).permute(2,0,1)
    if save is not False:
        save_image(ten_image, f'{save_dir}/{name}.jpg')
    else: pass
    if show is not False:
        show_images([chan_one, chan_two, chan_three])
    else: pass

# Cell
def show_aspects(fol: (L, str), show=False, save=False, save_path=None, atype=np.float32):
    "View axial, sagittal and coronal planes"
    if isinstance(fol, str): fol = get_dicom_files(fol)
    if isinstance(fol, L): fol = fol
    slices = []
    for i, s in enumerate(instance_sort(fol)):
        im = s[-1].dcmread(); slices.append(im)
    if len(slices)<=0:
        print('There is only 1 slice')
        pass
    else:
        img_shape = list(slices[0].pixel_array.shape)
        img_shape.append(len(slices))
        img3d = np.zeros(img_shape)
        for i, s in enumerate(slices):
            img2d = s.pixel_array; img3d[:, :, i] = img2d
        axial = img3d[:, :, img_shape[2]//2].astype(atype)
        sagittal = img3d[:, img_shape[1]//2, :].astype(atype)
        coronal = img3d[img_shape[0]//2, :, :].T.astype(atype)
        print(f'Number of slices: {len(fol)}')
        if show is not False: show_images([axial, sagittal, coronal], titles=('axial', 'sagittal', 'coronal'))
        if save is not False:
            if not os.path.exists(save_path):
                os.makedirs(save_path)
            imageio.imwrite(f'{save_path}/axial.jpg', axial.astype(atype))
            imageio.imwrite(f'{save_path}/sagittall.jpg', sagittal.astype(atype))
            imageio.imwrite(f'{save_path}/coronal.jpg', coronal.astype(atype))