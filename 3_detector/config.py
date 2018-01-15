#################### Configuration File ####################

# Base directory for data formats
#name = 'WBCvsRBC'
name = 'CELL_PATCHES'
data_dir = '/home/mnt/datasets/'
aug_dir = '/home/bumsoo/Data/split/'
test_dir = '/home/bumsoo/Data/test/'

data_base = data_dir + name
aug_base = aug_dir + name
test_base = test_dir + name

# model directory
model_dir = '../4_classifier/checkpoints'
#image_path = '/home/bumsoo/Data/test/CELL_PATCHES/WBC_Neutrophil_Segmented/WBC_SE110.png'
#image_path = '/home/bumsoo/Data/test/CELL_PATCHES/RBC_Target/RBC_TA14.png'
#image_path = './samples/2.png'

# model option
batch_size = 16
num_epochs = 100
lr_decay_epoch=20
feature_size = 500

# Global meanstd
mean = [0.778163803690477, 0.62366406713856704, 0.62748488269742386]
std = [0.18654390350275066, 0.25577185166630317, 0.22957029180170951]
