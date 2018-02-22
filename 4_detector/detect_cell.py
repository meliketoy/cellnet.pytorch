# ************************************************************
# Author : Bumsoo Kim, 2017
# Github : https://github.com/meliketoy/cellnet.pytorch
#
# Korea University, Data-Mining Lab
# Deep Convolutional Network Grad CAM Implementation
#
# Description : detect_cell.py
# The main code for grad-CAM image localization.
# ***********************************************************

from __future__ import print_function, division

import cv2
import torch
import torch.nn as nn
import torch.optim as optim
import torch.backends.cudnn as cudnn
import numpy as np
import config as cf
import torchvision
import time
import copy
import os
import sys
import argparse
import csv
import operator

from grad_cam import *
from time import sleep
from progressbar import *
from torchvision import datasets, models, transforms
from networks import *
from torch.autograd import Variable
from PIL import Image
from misc_functions import save_class_activation_on_image
from grad_cam import BackPropagation, GradCAM, GuidedBackPropagation

parser = argparse.ArgumentParser(description='Pytorch Cell Classification weight upload')
parser.add_argument('--net_type', default='resnet', type=str, help='model')
parser.add_argument('--depth', default=50, type=int, help='depth of model')
parser.add_argument('--stepSize', default=50, type=int, help='size of each sliding window steps')
parser.add_argument('--windowSize', default=100, type=int, help='size of the sliding window')
parser.add_argument('--subtype', default='WBC_Neutrophil_Segmented', type=str, help='Type to find')
parser.add_argument('--testNumber', default=1, type=int, help='Test Number')
args = parser.parse_args()

# Phase 1 : Model Upload
print('\n[Phase 1] : Model Weight Upload')
use_gpu = torch.cuda.is_available()

# upload labels
data_dir = cf.aug_base
trainset_dir = cf.data_base.split("/")[-1]+os.sep

dsets = datasets.ImageFolder(data_dir, None)
H = datasets.ImageFolder(os.path.join(cf.aug_base, 'train'))
dset_classes = H.classes

def softmax(x):
    return np.exp(x) / np.sum(np.exp(x), axis=0)

def getNetwork(args):
    if (args.net_type == 'alexnet'):
        file_name = 'alexnet'
    elif (args.net_type == 'vggnet'):
        file_name = 'vgg-%s' %(args.depth)
    elif (args.net_type == 'resnet'):
        file_name = 'resnet-%s' %(args.depth)
    else:
        print('[Error]: Network should be either [alexnet / vgget / resnet]')
        sys.exit(1)

    return file_name

def random_crop(image, dim):
    if len(image.shape):
        W, H, D = image.shape
        w, h, d = dim
    else:
        W, H = image.shape
        w, h = size

    left, top = np.random.randint(W-w+1), np.random.randint(H-h+1)
    return image[left:left+w, top:top+h], left, top

def return_class_idx(class_name):
    global dset_classes

    for i,j in enumerate(dset_classes):
        if class_name == j:
            return i

    print(class_name + " is not an appropriate class to search.")
    sys.exit(1) # Wrong class name input

def generate_sliding_windows(image, stepSize, windowSize):
    list_windows = []
    cnt = 0

    for x in xrange(0, image.size[0], stepSize):
        for y in range(0, image.size[1], stepSize):
            if(x+windowSize <= image.size[0] and y+windowSize <= image.size[1]):
                list_windows.append(image.crop((x,y,x+windowSize,y+windowSize)))

    return list_windows

def generate_padding_image(image, mode='cv2'):
    if (mode == 'cv2'):
        border_x = int((args.stepSize - ((image.shape[0]-args.windowSize)%args.stepSize))/2)
        border_y = int((args.stepSize - ((image.shape[1]-args.windowSize)%args.stepSize))/2)
        #pad_image = cv2.copyMakeBorder(image, border_x, border_x, border_y, border_y, cv2.BORDER_CONSTANT, value=[255,255,255])
        pad_image = cv2.copyMakeBorder(image, 0, border_x*2, 0, border_y*2, cv2.BORDER_CONSTANT, value=[255,255,255])
    elif (mode == 'PIL'):
        border_x = args.stepSize - ((image.size[0]-args.windowSize)%args.stepSize)
        border_y = args.stepSize - ((image.size[1]-args.windowSize)%args.stepSize)
        pad_image = Image.new("RGB", (image.size[0]+border_x, image.size[1]+border_y), color=255)
        #pad_image.paste(image, (int(border_x/2), int(border_y/2)))
        pad_image.paste(image, (0, 0))

    return pad_image

if __name__ == "__main__":
    # uploading the model
    print("| Loading checkpoint model for grad-CAM...")
    assert os.path.isdir('../3_classifier/checkpoint'),'[Error]: No checkpoint directory found!'
    assert os.path.isdir('../3_classifier/checkpoint/'+trainset_dir),'[Error]: There is no model weight to upload!'
    file_name = getNetwork(args)
    checkpoint = torch.load('../3_classifier/checkpoint/'+trainset_dir+file_name+'.t7')
    model = checkpoint['model']

    if use_gpu:
        model.cuda()
        cudnn.benchmark = True

    model.eval()

    sample_input = Variable(torch.randn(1,3,224,224), volatile=False)
    if use_gpu:
        sampe_input = sample_input.cuda()

    def is_image(f):
        return f.endswith(".png") or f.endswith(".jpg")

    test_transform = transforms.Compose([
        transforms.Scale(224),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(cf.mean, cf.std)
    ])

    #@ Code for extracting a grad-CAM region for a given class
    gcam = GradCAM(model._modules.items()[0][1], cuda=use_gpu)

    #print(dset_classes)
    print("\n[Phase 2] : Gradient Detection")
    WBC_id = return_class_idx(args.subtype)
    if not (args.subtype in dset_classes):
        print("The given subtype does not exists!")
        sys.exit(1)

    print("| Checking Activated Regions for " + dset_classes[WBC_id] + "...")

    file_name = cf.test_dir + str(args.testNumber) + os.sep + ('TEST%s.png' %str(args.testNumber))
    #file_name = cf.test_dir + str(args.testNumber) + ".png"
    print("| Opening "+file_name+"...")

    original_image = cv2.imread(file_name)
    PIL_image = Image.open(file_name)
    PIL_image = generate_padding_image(PIL_image, 'PIL')

    lst = generate_sliding_windows(PIL_image, args.stepSize, args.windowSize)

    print("\n[Phase 3] : Sliding Window Heatmaps")
    heatmap_lst = []

    widgets = ['Heatmap Generated: ', Percentage(), ' ', Bar(marker='#', left='[', right=']'), ' ', ETA(), ' ', FileTransferSpeed()]
    pbar = ProgressBar(widgets=widgets, maxval=len(lst))
    pbar.start()
    progress = 0

    # TODO!
    # Change this part to batchwise operation
    for img in lst:
        if (img.size[0] == img.size[1]): # Only consider foursquare regions
            backg = np.asarray(img)

            if test_transform is not None:
                img = test_transform(img)
                backg = cv2.resize(backg, (224, 224))

            inputs = img[:3,:,:]
            inputs = Variable(inputs, requires_grad=True)

            if use_gpu:
                inputs = inputs.cuda()
            inputs = inputs.view(1, inputs.size(0), inputs.size(1), inputs.size(2))

            #print(inputs.size())
            probs, idx = gcam.forward(inputs)

            if ('RBC' in dset_classes[idx[0]] or probs[0] < 0.9):
                heatmap_lst.append(np.uint8(np.zeros((224, 224, 3))))
            else:
                print(dset_classes[idx[0]], probs[0])
                # Grad-CAM
                gcam.backward(idx=idx[0])#WBC_id) # Get gradients for the selected label
                output = gcam.generate(target_layer='layer4.2') # Needs more testout

                #item_id = (np.where(idx.cpu().numpy() == (WBC_id)))[0][0]
                heatmap = cv2.cvtColor(np.uint8(output * 255.0), cv2.COLOR_GRAY2BGR)
                heatmap_lst.append(heatmap)
                #gcam.save("./heatmap/%s.png" %progress, heatmap, backg)
                #cv2.imwrite("./heatmap/%s.png" %progress, heatmap)
                #print('\t| {:5f}\t{}'.format(probs[0], dset_classes[idx[0]]))
            pbar.update(progress)
            progress += 1
    pbar.finish()

    print("\n[Phase 4] : Patching Up Individual Heatmaps")

    img_cnt = 0
    image = original_image
    image = generate_padding_image(image, 'cv2')
    blank_canvas = np.ones_like(image) # blank_canvas to draw the mapo
    original_image = image
    image = cv2.transpose(image)

    for x in xrange(0, image.shape[0], args.stepSize):
        for y in range(0, image.shape[1], args.stepSize):
            f_map = heatmap_lst[img_cnt]
            f_map = cv2.resize(f_map, (args.windowSize, args.windowSize))
            #f_map.fill(250)
            target_window = blank_canvas[y:y+args.windowSize, x:x+args.windowSize]

            if (target_window.shape[0] == target_window.shape[1]): # Only for foursquare windows
                target_window += f_map
                img_cnt += 1

                # Code to see the window flow, activate the f_map.fill code above
                # cv2.imwrite("./results/%s.png" %(str(img_cnt)), blank_canvas)
                #gcam.save("./results/%s.png" %(str(img_cnt)), blank_canvas, original_image)

                if (img_cnt >= len(heatmap_lst)):
                    blank_canvas = cv2.GaussianBlur(blank_canvas, (15,15), 0)
                    save_dir = './results/%s_%s.png' %(file_name.split(".")[-2].split("/")[-1], args.subtype)
                    #print(save_dir)
                    """
                    # Contours
                    _, coins_binary = cv2.threshold(cv2.cvtColor(blank_canvas, cv2.COLOR_BGR2GRAY),
                            100, 255, cv2.THRESH_BINARY)
                    cells_contours, _ = cv2.findContours(coins_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    cells_and_contours = np.copy(original_image)
                    cv2.drawContours(cells_and_contours, cells_contours, -1, (0, 255, 0), 2)
                    cv2.imwrite("./results/contours_%s_%s.png"
                            %(file_name.split(".")[-2].split("/")[-1], args.subtype),
                            cells_and_contours)
                    """
                    gcam.save(save_dir, blank_canvas, original_image)
                    print("| Feature map completed!")
                    sys.exit(0)
