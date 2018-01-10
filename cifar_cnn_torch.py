import time
import torch
from torch.autograd import Variable
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torchvision import datasets, transforms


batch_size = 32
epochs = 100
learning_rate =1e-1
class_num = 10
filter1_size = 32
filter2_size = 32
filter3_size = 64
filter4_size = 64
hide1_num = 1600
hide2_num = 512


kwargs = {'num_workers': 1, 'pin_memory': True} if 0 else {}
train_loader = torch.utils.data.DataLoader(
    datasets.CIFAR10('../data', train=True, download=True,
                   transform=transforms.Compose([
                       transforms.ToTensor(),
                       transforms.Normalize((0.1307,), (0.3081,))
                   ])),
    batch_size=batch_size, shuffle=True, **kwargs)
test_loader = torch.utils.data.DataLoader(
    datasets.CIFAR10('../data', train=False, transform=transforms.Compose([
                       transforms.ToTensor(),
                       transforms.Normalize((0.1307,), (0.3081,))
                   ])),
    batch_size=batch_size, shuffle=True, **kwargs)



class Net(nn.Module):
    def __init__(self,filter1_size,filter2_size,filter3_size,filter4_size,hide1_num,hide2_num,class_num):
        super(Net,self).__init__()
        self.conv1 = nn.Sequential(
                        nn.Conv2d(3,filter1_size,kernel_size=3),
                        nn.BatchNorm2d(filter1_size)
                        )
        self.conv2 = nn.Sequential(
                        nn.Conv2d(filter1_size,filter2_size,kernel_size=3),
                        nn.BatchNorm2d(filter2_size)
                        )
        self.conv2_drop = nn.Dropout2d(0.25)

        self.conv3 = nn.Sequential(
                        nn.Conv2d(filter2_size,filter3_size,kernel_size=3),
                        nn.BatchNorm2d(filter3_size)
                        )
        self.conv4 = nn.Sequential(
                        nn.Conv2d(filter3_size,filter4_size,kernel_size=3),
                        nn.BatchNorm2d(filter4_size)
                        )
        self.conv4_drop = nn.Dropout2d(0.25)
        
        self.layer5 = nn.Linear(hide1_num,hide2_num)
        self.layer5_drop = nn.Dropout2d(0.5)
        self.layer6 = nn.Linear(hide2_num,class_num)

    def forward(self,x):
        x = F.relu(self.conv1(x))
        x = F.relu(F.max_pool2d(self.conv2_drop(self.conv2(x)),2))
        x = F.relu(self.conv3(x))
        x = F.relu(F.max_pool2d(self.conv4_drop(self.conv4(x)),2))
        x = x.view(-1, hide1_num)
        x = F.relu(self.layer5_drop(self.layer5(x)))
        x = self.layer6(x)
        return F.log_softmax(x,dim=1)

model = Net(filter1_size,filter2_size,filter3_size,filter4_size,hide1_num,hide2_num,class_num)
optimizer = optim.SGD(model.parameters(), lr=learning_rate)
def train(epoch):
    model.train()
    for batch_idx, (data, target) in enumerate(train_loader):
        data, target = Variable(data), Variable(target)
        optimizer.zero_grad()
        output = model(data)
        loss = F.nll_loss(output, target)
        loss.backward()
        optimizer.step()
        if batch_idx % 1000 == 0:
            print('Train Epoch: {} [{}/{} ({:.0f}%)]\tLoss: {:.6f}'.format(
                epoch, batch_idx * len(data), len(train_loader.dataset),
                100. * batch_idx / len(train_loader), loss.data[0]))


def test():
    model.eval()
    test_loss = 0
    correct = 0
    for data, target in test_loader:
        data, target = Variable(data, volatile=True), Variable(target)
        output = model(data)
        test_loss += F.nll_loss(output, target, size_average=False).data[0] # sum up batch loss
        pred = output.data.max(1, keepdim=True)[1] # get the index of the max log-probability
        correct += pred.eq(target.data.view_as(pred)).cpu().sum()

    test_loss /= len(test_loader.dataset)
    print('\nTest set: Average loss: {:.4f}, Accuracy: {}/{} ({:.0f}%)\n'.format(
        test_loss, correct, len(test_loader.dataset),
        100. * correct / len(test_loader.dataset)))


s_time = int(time.time())
for epoch in range(epochs):
    train(epoch)
    test()
e_time = int(time.time())
print("%02d:%02d:%02d" %((e_time-s_time)/3600,(e_time-s_time)%3600/60,(e_time-s_time)%60))
