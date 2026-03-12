import torch
import pandas as pd

from model.model import ViralNet


def train(datafile):

    df = pd.read_csv(datafile)

    X = df[["views","likes","comments","shares","engagement"]].values
    y = df["viral"].values

    model = ViralNet()

    optimizer = torch.optim.Adam(model.parameters())
    loss_fn = torch.nn.BCELoss()

    X = torch.tensor(X).float()
    y = torch.tensor(y).float().unsqueeze(1)

    for epoch in range(100):

        pred = model(X)

        loss = loss_fn(pred,y)

        optimizer.zero_grad()

        loss.backward()

        optimizer.step()

    torch.save(model.state_dict(),"viral_model.pt")
