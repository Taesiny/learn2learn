#!/usr/bin/env python3

from __future__ import print_function

import os
import pickle

import numpy as np
import torch
import torch.utils.data as data

from learn2learn.data.utils import download_file_from_google_drive, download_file


def download_pkl(google_drive_id, data_root, mode):
    filename = 'mini-imagenet-cache-' + mode
    file_path = os.path.join(data_root, filename)

    if not os.path.exists(file_path + '.pkl'):
        print('Downloading:', file_path + '.pkl')
        download_file_from_google_drive(google_drive_id, file_path + '.pkl')
    else:
        print("Data was already downloaded")


def index_classes(items):
    idx = {}
    for i in items:
        if (i not in idx):
            idx[i] = len(idx)
    return idx


class MiniImagenet(data.Dataset):
    """
    [[Source]](https://github.com/learnables/learn2learn/blob/master/learn2learn/vision/datasets/mini_imagenet.py)

    **Description**

    The *mini*-ImageNet dataset was originally introduced by Vinyals et al., 2016.


    It consists of 60'000 colour images of sizes 84x84 pixels.
    The dataset is divided in 3 splits of 64 training, 16 validation, and 20 testing classes each containing 600 examples.
    The classes are sampled from the ImageNet dataset, and we use the splits from Ravi & Larochelle, 2017.

    **References**

    1. Vinyals et al. 2016. “Matching Networks for One Shot Learning.” NeurIPS.
    2. Ravi and Larochelle. 2017. “Optimization as a Model for Few-Shot Learning.” ICLR.

    **Arguments**

    * **root** (str) - Path to download the data.
    * **mode** (str, *optional*, default='train') - Which split to use.
        Must be 'train', 'validation', or 'test'.
    * **transform** (Transform, *optional*, default=None) - Input pre-processing.
    * **target_transform** (Transform, *optional*, default=None) - Target pre-processing.
    * **download** (bool, *optional*, default=False) - Download the dataset if it's not available.

    **Example**

    ~~~python
    train_dataset = l2l.vision.datasets.MiniImagenet(root='./data', mode='train')
    train_dataset = l2l.data.MetaDataset(train_dataset)
    train_generator = l2l.data.TaskGenerator(dataset=train_dataset, ways=ways)
    ~~~

    """

    def __init__(
        self,
        root,
        mode='train',
        transform=None,
        target_transform=None,
        download=False,
    ):
        super(MiniImagenet, self).__init__()
        self.root = os.path.expanduser(root)
        if not os.path.exists(self.root):
            os.mkdir(self.root)
        self.transform = transform
        self.target_transform = target_transform
        self.mode = mode
        self._bookkeeping_path = os.path.join(self.root, 'mini-imagenet-bookkeeping-' + mode + '.pkl')
        if self.mode == 'test':
          pickle_file = '/content/learn2learn/learn2learn/data/mini-imagenet-cache-test.pkl'
        elif self.mode == 'train':
          pickle_file = '/content/learn2learn/learn2learn/data/mini-imagenet-cache-train.pkl'
        elif self.mode == 'validation':
          pickle_file = '/content/learn2learn/learn2learn/data/mini-imagenet-cache-validation.pkl'
        else:
            raise ValueError('Needs to be train, test or validation')

        # pickle_file = os.path.join(self.root, 'mini-imagenet-cache-' + mode + '.pkl')

        with open(pickle_file, 'rb') as f:
            self.data = pickle.load(f)

        self.x = torch.from_numpy(self.data["image_data"]).permute(0, 3, 1, 2).float()
        self.y = np.ones(len(self.x))

        # TODO Remove index_classes from here
        self.class_idx = index_classes(self.data['class_dict'].keys())
        for class_name, idxs in self.data['class_dict'].items():
            for idx in idxs:
                self.y[idx] = self.class_idx[class_name]

    def __getitem__(self, idx):
        data = self.x[idx]
        if self.transform:
            data = self.transform(data)
        return data, self.y[idx]

    def __len__(self):
        return len(self.x)

    def _check_exists(self):
        return os.path.exists(os.path.join(self.root, 'mini-imagenet-cache-' + self.mode + '.pkl'))


if __name__ == '__main__':
    mi = MiniImagenet(root='./data', download=True)
    __import__('pdb').set_trace()
