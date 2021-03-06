import argparse
import os
import cv2
import csv
import sys
import operator
import numpy as np
import config as cf

import torch
import torch.nn as nn
import torch.backends.cudnn as cudnn
import torchvision

from torchvision import datasets, models, transforms
from networks import *
from torch.autograd import Variable
from PIL import Image

count = 0
parser = argparse.ArgumentParser(description='Pytorch Cell Classification weight upload')
parser.add_argument('--net_type', default='resnet', type=str, help='model')
parser.add_argument('--depth', default=50, type=int, help='depth of model')
args = parser.parse_args()

if (sys.version_info > (3,0)):
    test_transform = transforms.Compose([
        transforms.Resize(224),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(cf.mean, cf.std)
    ])
else:
    test_transform = transforms.Compose([
        transforms.Scale(224),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(cf.mean, cf.std)
    ])


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

model_dir = '../3_classifier/checkpoint/'
model_name = cf.name
file_name = getNetwork(args)

def check_and_mkdir(in_dir):
    if not os.path.exists(in_dir):
        print("Creating %s..." %in_dir)
        os.makedirs(in_dir)

def softmax(x):
    return np.exp(x) / np.sum(np.exp(x), axis=0)

def inference_crop(model, cropped_img):
    # check if cropped img is a torch Variable, if not, convert
    use_gpu = torch.cuda.is_available()

    if test_transform is not None:
        img = test_transform(Image.fromarray(cropped_img, mode='RGB'))

    inputs = img

    with torch.no_grad():
        inputs = Variable(inputs)

        if use_gpu:
            inputs = inputs.cuda()

        inputs = inputs.view(1, inputs.size(0), inputs.size(1), inputs.size(2))

        outputs = model(inputs)
        softmax_res = softmax(outputs.data.cpu().numpy()[0])
        index, score = max(enumerate(softmax_res), key=operator.itemgetter(1))

    return index, score

def bbox(base, original_img, mask_img, model):
    ret, threshed_img = cv2.threshold(cv2.cvtColor(mask_img, cv2.COLOR_BGR2GRAY), 127, 255, cv2.THRESH_BINARY)
    kernel = np.ones((3,3), np.uint8)
    closing = cv2.morphologyEx(threshed_img, cv2.MORPH_CLOSE, kernel, iterations=1)

    _, contours, _ = cv2.findContours(closing, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    copy_img = original_img.copy()

    for cnt_idx, cnt in enumerate(contours):
        area = cv2.contourArea(cnt)

        if area < 4000:
            continue

        x, y, w, h = cv2.boundingRect(cnt)
        crop = copy_img[y:y+h, x:x+w]
        cv2.imwrite("./results/ALL_IDB1/%s/cropped/%s-%d.png" %(model_name, base, cnt_idx), crop)
        crop = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)

        idx, score = inference_crop(model, crop)
        answ = dset_classes[idx]

        cv2.rectangle(original_img, (x,y), (x+w, y+h), (0,255,0), 2)
        #cv2.putText(original_img, "%s = %s" %(answ, str(score)), (x,y),
        #    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2, cv2.LINE_AA)

    return original_img

if __name__ == "__main__":

    # Upload model
    trainset_dir = cf.data_base.split("/")[-1]+os.sep
    dsets = datasets.ImageFolder(os.path.join(cf.aug_base, 'train'))
    dset_classes = dsets.classes

    assert os.path.isdir(model_dir), '[Error]: No checkpoint dir found!'
    assert os.path.isdir(os.path.join(model_dir, model_name)), '[Error]: There is no model weight to upload!'
    checkpoint = torch.load(os.path.join(model_dir, model_name, file_name+".t7"))
    model = checkpoint['model']

    check_and_mkdir('./results/ALL_IDB1/%s/inferenced/' %model_name)
    check_and_mkdir('./results/ALL_IDB1/%s/cropped/' %model_name)

    # Iterate files
    #for subdir, dirs, files in os.walk('/home/bumsoo/Data/_test/ALL_IDB1/im/'):
    for subdir, dirs, files in os.walk('/home/bumsoo/Github/cellnet.pytorch/4_detector/results/ALL_IDB1/%s/masks/' %model_name):
        for f in files:
            if f.endswith(".jpg") == False and f.endswith(".png") == False:
                continue

            in_dir = './results/ALL_IDB1/%s/' %model_name
            if not os.path.exists(in_dir):
                print("There is no result directory")
                sys.exit(1)

            img = cv2.imread(os.path.join('/home/bumsoo/Data/_test/ALL_IDB1/im/', f))
            mask_img = cv2.imread(in_dir + 'masks/' + f.split(".")[0] + ".png")

            back_img = img[:]
            marked_img = bbox(f.split(".")[0], back_img, mask_img, model)
            print("Bounding Box Inference for %s" %f)
            cv2.imwrite(in_dir + "/inferenced/" + f, marked_img)
