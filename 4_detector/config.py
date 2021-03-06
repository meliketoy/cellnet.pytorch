#################### Configuration File ####################

# Base directory for data formats
name = 'Guro_GM'
#name = 'Granulocytes_vs_Mononuclear'
#name = 'Guro_WBC' # No hierarchy

data_dir = '/home/mnt/datasets/'
aug_dir = '/home/bumsoo/Data/_train_val/'

data_base = data_dir + name
aug_base = aug_dir + name

# model directory
model_dir = '../3_classifier/checkpoints'
test_dir = '/home/bumsoo/Data/_test/' # Number on the back

# model option
batch_size = 16
num_epochs = 100
lr_decay_epoch=20
feature_size = 500

if (name == 'Granulocytes_vs_Mononuclear' or name == 'Guro_GM'):
    # Granulocytes_vs_Mononuclear
    mean = [0.75086572277254926, 0.54344990735699861, 0.56189840210810549]
    std = [0.19795568869316291, 0.29897863665208158, 0.26473830163404605]
    #mean = [0.7593608074350131, 0.6122998654014106, 0.6142165029355519]
    #std = [0.22106204895546486, 0.27805751343124707, 0.2522135438853085]
elif (name == 'WBC' or name == 'Guro_WBC'):
    # WBC meanstd
    mean = [0.7593608074350131, 0.6122998654014106, 0.6142165029355519]
    std = [0.22106204895546486, 0.27805751343124707, 0.2522135438853085]
else:
    raise NotImplementedError
