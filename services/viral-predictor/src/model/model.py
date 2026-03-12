import torch
import torch.nn as nn


class ViralNet(nn.Module):

    def __init__(self):

        super().__init__()

        self.net = nn.Sequential(

            nn.Linear(5,64),
            nn.ReLU(),

            nn.Linear(64,32),
            nn.ReLU(),

            nn.Linear(32,1),
            nn.Sigmoid()

        )

    def forward(self,x):

        return self.net(x)


model = ViralNet()

def predict(features):

    x = torch.tensor(features).float()

    with torch.no_grad():

        score = model(x)

    return float(score)
