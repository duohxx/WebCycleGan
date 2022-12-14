#!/usr/bin/python3

import argparse
import sys
import os

import torchvision.transforms as transforms
from torchvision.utils import save_image
from torch.utils.data import DataLoader
from torch.autograd import Variable
import torch

from models import Generator
from datasets import ImageDataset
from PIL import Image
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

img_path = "1.jpg"
sample_path = "vg.png"
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--batchSize', type=int, default=1, help='size of the batches')
    parser.add_argument('--dataroot', type=str, default='datasets/', help='root directory of the dataset')
    parser.add_argument('--input_nc', type=int, default=3, help='number of channels of input data')
    parser.add_argument('--output_nc', type=int, default=3, help='number of channels of output data')
    parser.add_argument('--size', type=int, default=300, help='size of the data (squared assumed)')
    parser.add_argument('--cuda', default=1, help='use GPU computation')
    parser.add_argument('--n_cpu', type=int, default=8, help='number of cpu threads to use during batch generation')
    parser.add_argument('--generator_A2B', type=str, default='models/netG_A2B.pth', help='A2B generator checkpoint file')
    parser.add_argument('--generator_B2A', type=str, default='models/netG_B2A.pth', help='B2A generator checkpoint file')
    parser.add_argument('--input', default=1, help='please input a image')
    opt = parser.parse_args()
    print(opt)

    if torch.cuda.is_available() and not opt.cuda:
        print("WARNING: You have a CUDA device, so you should probably run with --cuda")

    ###### Definition of variables ######
    # Networks
    netG_A2B = Generator(opt.input_nc, opt.output_nc)
    netG_B2A = Generator(opt.output_nc, opt.input_nc)

    if opt.cuda:
        netG_A2B.to(device)
        netG_B2A.to(device)

    # Load state dicts
    netG_A2B.load_state_dict(torch.load(opt.generator_A2B, map_location='cpu'))
    netG_B2A.load_state_dict(torch.load(opt.generator_B2A, map_location='cpu'))

    # Set model's test mode
    netG_A2B.eval()
    netG_B2A.eval()

    # Inputs & targets memory allocation
    # Tensor = torch.cuda.FloatTensor if opt.cuda else torch.Tensor
    Tensor = torch.Tensor
    input_A = Tensor(opt.batchSize, opt.input_nc, opt.size, opt.size)
    input_B = Tensor(opt.batchSize, opt.output_nc, opt.size, opt.size)

    transforms_ = [#transforms.Resize(int(opt.size * 1.12), Image.BICUBIC),
                   transforms.RandomCrop(opt.size),
      #             transforms.RandomHorizontalFlip(),
                   transforms.ToTensor(),
                   transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))]
    dataloader = DataLoader(ImageDataset(opt.dataroot, transforms_=transforms_, mode='test'),
                            batch_size=opt.batchSize, shuffle=False, num_workers=opt.n_cpu)
    ###### Testing######

    # Create output dirs if they don't exist
    if not os.path.exists('output/A'):
        os.makedirs('output/A')
    if not os.path.exists('output/B'):
        os.makedirs('output/B')

    real_A = Image.open(img_path)
    real_A = real_A.resize((300, 300))
    real_A = transforms.ToTensor()(real_A).unsqueeze(0)
    real_A = Variable(input_A.copy_(real_A))

    real_B = Image.open(sample_path)
    real_B = real_B.resize((300, 300))
    real_B = transforms.ToTensor()(real_B).unsqueeze(0)
    real_B = Variable(input_B.copy_(real_B))

    fake_B = 0.5*(netG_A2B(real_A).data + 1.0)
    fake_A = 0.5*(netG_B2A(real_B).data + 1.0)
    cycle_A = 0.5*(netG_B2A(fake_B).data + 1.0)

    # Save image files
    save_image(fake_B, 'output/A/1.png')
    save_image(cycle_A, 'output/B/1.png')

    sys.stdout.write('\rGenerated images %04d of %04d' % (1, len(dataloader)))


    '''
    for i, batch in enumerate(dataloader):
        # Set model input
        #  real_A = Variable(input_A.copy_(batch['A']))
        real_A = Variable(input_A.copy_(batch['A']))
        real_B = Variable(input_B.copy_(batch['B']))

        # Generate output
        fake_B = 0.5*(netG_A2B(real_A).data + 1.0)
        fake_A = 0.5*(netG_B2A(real_B).data + 1.0)
        cycle_A = 0.5*(netG_B2A(fake_B).data + 1.0)

        # Save image files
        save_image(fake_B, 'output/A/%04d.png' % (i+1))
        save_image(cycle_A, 'output/B/%04d.png' % (i+1))

        sys.stdout.write('\rGenerated images %04d of %04d' % (i+1, len(dataloader)))
    '''
    sys.stdout.write('\n')
    ###################################
