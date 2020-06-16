from torchvision.datasets import ImageFolder
import os
import shutil
import torch
import torch.nn as nn
from torch.utils.model_zoo import load_url as load_state_dict_from_url
from torchvision.models import alexnet
import torch.nn as nn
from torch.autograd import Function
import os
import logging
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Subset, DataLoader
from torch.backends import cudnn
import torchvision
from torchvision import transforms
from torchvision.models import alexnet
from PIL import Image
from tqdm import tqdm
from torchvision.datasets import VisionDataset
from PIL import Image
import os
import os.path
import sys
import numpy as np
from torch.utils.data import DataLoader
from sklearn.model_selection import train_test_split
from sklearn import utils
from torchvision.transforms.functional import pad
from torchvision import transforms
import numpy as np
import numbers
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models
import matplotlib.pyplot as plt
import types

from rod_utils import * # synROd and ROD useful functions


class SynROD(VisionDataset):
    """
    item_extractor_fn: accepts either a string to specify one of the existing types of task ("rotation", "zoom" or "decentralized_zoom")
                                    and the respective function is automatically selected

                        or specify your own function to do the extraction
                        if it is a function it has to be created following this synthax

                        def func_name(rgb_image, depth_image, original_label, item_extractor_param_values)


    item_extractor_param_values: (dictionary) that specifies for each key, the value of a parameter
                                    that has to be passed to the provided item_extractor_fn

                                ROTATION TASK DICTIONARY MUST SPECIFY THE VALUES FOR THE KEYS:

                                                                                "MAIN_RGB_TRANSFORM": Preprocessing for original RGB image.
                                                                                "MAIN_DEPTH_TRANSFORM": Preprocessing for original D image.
                                                                                "PRETEXT_RGB_TRANSFORM": Preprocessing for rotated RGB image.
                                                                                "PRETEXT_DEPTH_TRANSFORM": : Preprocessing for rotated D image.

                                ZOOM TASK DICTIONARY MUST SPECIFY THE VALUES FOR THE KEYS:

                                                                                "MAX_ZOOM_PERCENTAGE"
                                                                                "PRE_ZOOM_TRANSFORM": Preprocessing before zoom. Same for RGB and D.
                                                                                "MAIN_RGB_TRANSFORM": Preprocessing for original RGB image.
                                                                                "MAIN_DEPTH_TRANSFORM": Preprocessing for original D image.
                                                                                "POST_ZOOM_RGB_TRANSFORM": Preprocessing for zoomed RGB image.
                                                                                "POST_ZOOM_DEPTH_TRANSFORM": Preprocessing for zoomed D image.



    """
    def __init__(self,
                root,
                item_extractor_fn=None,
                item_extractor_param_values=None,
                 ram_mode=False):
        super(SynROD, self).__init__(root)


        if isinstance(item_extractor_fn, types.FunctionType):
            self.item_extractor_fn=item_extractor_fn
        elif isinstance(item_extractor_fn, str):
            if item_extractor_fn == "zoom":
                self.item_extractor_fn = zoom_task_extractor
            elif item_extractor_fn == "decentralized_zoom":
                self.item_extractor_fn = decentralized_zoom_task_extractor
            elif item_extractor_fn == "rotation":
                self.item_extractor_fn = relative_rot_task_extractor
        else:
            self.item_extractor_fn=item_extractor_fn

        self.item_extractor_param_values=item_extractor_param_values


        self.ram_mode = ram_mode

        labels_dict = dict()
        id_to_labels = []
        num_labels = 0
        self.X = []
        self.y_labels = []
        self.y = []
        self.labels_dict = labels_dict
        self.id_to_labels = id_to_labels

        count_not_found = 0
        #enforce a given order for the sequence of labels (the item_directory names)
        for item_directory in sorted(os.listdir( root )):
          if os.path.isdir( os.path.join(root, item_directory) ) :
            curr_path = os.path.join(root, item_directory)
            label = item_directory
            curr_label_id = -1
            if label not in labels_dict:
              labels_dict[label] = num_labels
              curr_label_id = num_labels
              id_to_labels.append(num_labels)
              num_labels += 1
            else:
              curr_label_id = labels_dict[label]

            curr_rgb_path = os.path.join(curr_path, "rgb")
            curr_depth_path = os.path.join(curr_path, "depth")

            for image_file_id in os.listdir(curr_rgb_path):
              rgb_image_file_path = os.path.join(curr_rgb_path, image_file_id)
              depth_image_file_path = os.path.join(curr_depth_path,  image_file_id)
              #ONLY IF BOTH EXIST---> due to a problem in how image ids are assigned in the standard version of the dataset
              # some images do not have both the depth and the rgb image
              if os.path.isfile(rgb_image_file_path) and os.path.isfile(depth_image_file_path):
                if self.ram_mode == True:
                    self.X.append((pil_loader(rgb_image_file_path),pil_loader(depth_image_file_path) ) )
                else:
                    self.X.append((rgb_image_file_path, depth_image_file_path) )
                self.y.append(curr_label_id)
                self.y_labels.append(label)

              else:
                count_not_found += 1
        print("num not found: ", count_not_found)



    def shuffle(self):
      self.X, self.y_labels, self.y = utils.shuffle( self.X, self.y_labels, self.y, random_state=0 )


    def __getitem__(self, index):
        images, object_label = self.X[index], self.y[index]
        if self.ram_mode == True:
            rgb_image = images[0]#pil_loader(images[0])
            depth_image = images[1]#pil_loader(images[1])
        else:
            rgb_image = pil_loader(images[0])
            depth_image = pil_loader(images[1])

        return self.item_extractor_fn(rgb_image, depth_image, object_label, self.item_extractor_param_values)#(rgb_image, depth_image, object_label), (pretext_task_rgb_image, pretext_task_depth_image, pretext_task_label)

    def __len__(self):
        length = len(self.X)
        return length
