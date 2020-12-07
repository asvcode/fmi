# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/03_preprocessing.ipynb (unless otherwise specified).

__all__ = ['mask_and_save_path', 'mask_and_save_df', 'move_files', 'dicomsplit', 'check_duplicate', 'dicom_splitter']

# Cell
import pydicom,kornia,skimage
from fastai.vision.all import *
from fastai.medical.imaging import *
from torchvision.utils import save_image

from .pipeline import *
from .explore import get_dicom_image

# Cell
def mask_and_save_path(file: (L), source=None, show=False, window=dicom_windows.lungs, sigma:float=0.1,\
                  thresh:float=0.9, save=False, save_path=None):
    "Helper to create masks based on dicom window with the option to save the updated image from path"
    image_list = []
    for i in file:
        ##This line will have to be changed depending on what platform is being used
        str_file = str(i); file_name = str_file.split('.')[0].split('\\')[-1] #windows
        #str_file = str(i); file_name = str_file.split('/')[-1].split('.')[0] #kaggle
        dcm = dcmread(i)
        wind = dcm.windowed(*window)
        mask = dcm.mask_from_blur(window, sigma=sigma, thresh=thresh, remove_max=False)
        bbs = mask2bbox(mask)
        lo,hi = bbs
        imh = wind[lo[0]:hi[0],lo[1]:hi[1]]
        if save is not False:
            if not os.path.exists(save_path):
                os.makedirs(save_path)
            save_image(imh, f'{save_path}/{file_name}.png')
        else:
            pass
        image_list.append(imh)
    if show is not False:
        show_images(image_list[:10], nrows=1)
    else:
        pass

# Cell
def mask_and_save_df(file: (pd.DataFrame), source=None, show=False, window=dicom_windows.lungs, sigma:float=0.1,\
                  thresh:float=0.9, save=False, save_path=None):
    "Helper to create masks based on dicom window with the option to save the updated image from a dataframe"
    image_list = []
    for i in file.index:
        file_path = f"{source}/{file.iloc[i]['PatientID']}/{file.iloc[i]['InstanceNumber']}.dcm"
        file_name = file.iloc[i]['InstanceNumber']
        dcm = dcmread(file_path)
        wind = dcm.windowed(*window)
        mask = dcm.mask_from_blur(window, sigma=sigma, thresh=thresh, remove_max=False)
        bbs = mask2bbox(mask)
        lo,hi = bbs
        imh = wind[lo[0]:hi[0],lo[1]:hi[1]]
        if save is not False:
            if not os.path.exists(save_path):
                os.makedirs(save_path)
            save_image(imh, f'{save_path}/{file_name}.png')
        else:
            pass
        image_list.append(imh)
    if show is not False:
        show_images(image_list[:10], nrows=1)
    else:
        pass

# Cell
@patch
def updated_dict(self:DcmDataset, windows=[dicom_windows.lungs]):
    pxdata = (0x7fe0,0x0010)
    vals = [self[o] for o in self.keys() if o != pxdata]
    its = [(v.keyword, v.value) for v in vals]
    res = dict(its)
    res['fname'] = self.filename

    stats = 'min', 'max', 'mean', 'std'
    pxs = self.pixel_array
    for f in stats: res['img_'+f] = getattr(pxs, f)()
    res['img_pct_window'] = self.pct_in_window(*windows)
    return res

# Cell
def _dcm2dict2(fn, windows, **kwargs): return fn.dcmread().updated_dict(windows, **kwargs)

# Cell
@delegates(parallel)
def _from_dicoms2(cls, fns, n_workers=0, **kwargs):
    return pd.DataFrame(parallel(_dcm2dict2, fns, n_workers=n_workers, **kwargs))
pd.DataFrame.from_dicoms2 = classmethod(_from_dicoms2)

# Cell
def move_files(df, source, save_path):
    "helper to move .dcm files"
    try:
        df.PatientID
        for i in df.index:
            #patient ID
            patid = str(df.PatientID[i])
            window = str(df.img_pct_window[i])
            #fname
            #filename = str(df.fname[i]).split('/')[-1] #non windows
            filename = str(df.fname[i]).split('\\')[-1] #windows
            img = filename.split('.')[0]
            print(f'ID: {patid} window: {window} instance: {img}')

            folder_path = save_path + patid
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            img_file = Path(f'{source}/{patid}/{img}.dcm')
            shutil.copy(img_file, folder_path, follow_symlinks=True)
    except AttributeError: print('No PatientID in dataframe')

# Cell
def dicomsplit(valid_pct=0.2, seed=None, **kwargs):
    "Splits `items` between train/val with `valid_pct`"
    "and checks if identical patient IDs exist in both the train and valid sets"
    def _inner(o, **kwargs):
        train_list = []; valid_list = []
        if seed is not None: torch.manual_seed(seed)
        rand_idx = L(int(i) for i in torch.randperm(len(o)))
        cut = int(valid_pct * len(o))
        trn = rand_idx[cut:]; trn_p = o[rand_idx[cut:]]
        val = rand_idx[:cut]; val_p = o[rand_idx[:cut]]
        train_patient = []; train_images = []
        for i, tfile in enumerate(trn_p):
            file = dcmread(tfile)
            tpat = file.PatientID
            train_patient.append(tpat)
            file_array = dcmread(tfile).pixel_array
            train_images.append(file_array)
        val_patient = []; val_images = []
        for i, vfile in enumerate(val_p):
            file2 = dcmread(vfile)
            vpat = file2.PatientID
            val_patient.append(vpat)
            val_array = dcmread(vfile).pixel_array
            val_images.append(val_array)

        print(rand_idx)
        print(f'Train: {trn}, {train_patient}')
        show_images(train_images[:20])
        print(f'Val: {val}, {val_patient}')
        show_images(val_images[:20])
        is_duplicate = set(train_patient) & set(val_patient)
        print(f'Duplicate: {set(train_patient) & set(val_patient)}')
        new_list = []
        if bool(is_duplicate) is not False:
            print('duplicate exists')
            new_list = [elem for elem in train_patient if elem not in val_patient ]
            print(f'New List: {new_list}')
        else:
            print('duplicate does NOT exist')
            new_list = trn
        return new_list, val
    return _inner

# Cell
def check_duplicate(items, seed=5):
    trn, val = dicomsplit(valid_pct=0.2, seed=seed)(items)
    return trn, val

# Cell
def dicom_splitter(items, valid_pct=0.2, seed=77):
    trn, val = dicomsplit(valid_pct=valid_pct)(items)
    valid_idx = val
    def _inner(o):
        train_idx = np.setdiff1d(np.array(range_of(o)), np.array(valid_idx))
        print(f'train:{train_idx} val:{valid_idx}')
        return L(train_idx, use_list=True), L(valid_idx, use_list=True)
    return _inner