# -*- coding: utf-8 -*-
"""Named-Entity-Recognition_0218.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/18vh0rTs-6k7LXsR_9HC8YVaFL1NdFhir
"""

from typing import Dict, List, Optional
from collections import Counter
import os
import csv
!pip install torchmetrics
!pip install pytorch-metric-learning
import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
!pip install pytorch-lightning
import torch.optim as optim
import torchmetrics
from tqdm import tqdm
import torch
import torch.nn as nn
!pip install CRF

import torch.nn.functional as F
from torch.nn import TransformerEncoder, TransformerEncoderLayer

class Tokenizer:
    def __init__(self):
        # two special tokens for padding and unknown
        self.token2idx = {"<pad>": 0, "<unk>": 1}
        self.idx2token = ["<pad>", "<unk>"]
        self.is_fit = False

    @property
    def pad_id(self):
        return self.token2idx["<pad>"]

    def __len__(self):
        return len(self.idx2token)

    def fit(self, train_texts: List[str]):
        counter = Counter()
        for text in train_texts:
            counter.update(text.lower().split())

        # manually set a vocabulary size for the data set
        vocab_size = 20000
        self.idx2token.extend([token for token, count in counter.most_common(vocab_size - 2)])
        for (i, token) in enumerate(self.idx2token):
            self.token2idx[token] = i

        self.is_fit = True

    def encode(self, text: str, max_length: Optional[int] = None) -> List[int]:
        if not self.is_fit:
            raise Exception("Please fit the tokenizer on the training tokens")

        tokens = text.lower().split()
        token_ids = [self.token2idx.get(token, self.token2idx["<unk>"]) for token in tokens]

        if max_length is not None:
            # truncate or pad the token_ids to max_length
            if len(token_ids) > max_length:
                token_ids = token_ids[:max_length]
            else:
                token_ids += [self.token2idx["<pad>"]] * (max_length - len(token_ids))

        return token_ids

        # TODO: implement the encode method, the method signature shouldn't be changed

def load_raw_data(filepath: str, with_tags: bool = True):
    data = {'text': []}
    if with_tags:
        data['tags'] = []
        with open(filepath) as f:
            reader = csv.reader(f)
            for text, tags in reader:
                data['text'].append(text)
                data['tags'].append(tags)
    else:
        with open(filepath) as f:
            for line in f:
                data['text'].append(line.strip())
    return data

#upload the dataset
#for google colb, use this
#from google.colab import files
#uploaded = files.upload()

#modify as per workspace
tokenizer = Tokenizer()
train_raw = load_raw_data(os.path.join("train.csv"))
val_raw = load_raw_data(os.path.join("val.csv"))
test_raw = load_raw_data(os.path.join("test_tokens.txt"), with_tags=False)
# fit the tokenizer on the training tokens
tokenizer.fit(train_raw['text'])

text = "hello transformers !"
tokenizer.encode(text)                  # example output: [3, 4, 5]
tokenizer.encode(text, max_length=5)    # example output: [3, 4, 5, 0, 0]
tokenizer.encode(text, max_length=2)    # example output: [3, 4]

class NERDataset:
    tag2idx = {'O': 1, 'B-PER': 2, 'I-PER': 3, 'B-ORG': 4, 'I-ORG': 5, 'B-LOC': 6, 'I-LOC': 7, 'B-MISC': 8, 'I-MISC': 9}
    idx2tag = ['<pad>', 'O', 'B-PER', 'I-PER', 'B-ORG', 'I-ORG','B-LOC', 'I-LOC', 'B-MISC', 'I-MISC']

    def __init__(self, raw_data: Dict[str, List[str]], tokenizer: Tokenizer, max_length: int = 128):
        self.tokenizer = tokenizer
        self.token_ids = []
        self.tag_ids = []
        self.with_tags = False
        for text in raw_data['text']:
            self.token_ids.append(tokenizer.encode(text, max_length=max_length))
        if 'tags' in raw_data:
            self.with_tags = True
            for tags in raw_data['tags']:
                self.tag_ids.append(self.encode_tags(tags, max_length=max_length))

    def encode_tags(self, tags: str, max_length: Optional[int] = None):
        tag_ids = [self.tag2idx[tag] for tag in tags.split()]
        if max_length is None:
            return tag_ids
        # truncate the tags if longer than max_length
        if len(tag_ids) > max_length:
            return tag_ids[:max_length]
        # pad with 0s if shorter than max_length
        else:
            return tag_ids + [0] * (max_length - len(tag_ids))  # 0 as padding for tags

    def __len__(self):
        return len(self.token_ids)

    def __getitem__(self, idx):
        token_ids = torch.LongTensor(self.token_ids[idx])
        mask = token_ids == self.tokenizer.pad_id  # padding tokens
        if self.with_tags:
            # for training and validation
            return token_ids, mask, torch.LongTensor(self.tag_ids[idx])
        else:
            # for testing
            return token_ids, mask

tr_data = NERDataset(train_raw, tokenizer)
va_data = NERDataset(val_raw, tokenizer)
te_data = NERDataset(test_raw, tokenizer)

import torch
import torch.nn as nn
import math
from typing import List, Tuple
from torch.utils.data import DataLoader
from tqdm import tqdm

class PositionalEncoding(nn.Module):
    def __init__(self, d_model, dropout=0.1, max_len=5000):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)

        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0).transpose(0, 1)

        self.register_buffer('pe', pe)

    def forward(self, x):
        x = x + self.pe[:x.size(0), :]
        return self.dropout(x)

class TransformerModel(nn.Module):
    def __init__(self, vocab_size: int, embedding_size: int, num_head: int, hidden_size: int,
                 num_layers: int, dropout: float = 0):
        super().__init__()

        self.model_type = 'Transformer'
        self.pos_encoder = PositionalEncoding(embedding_size, dropout)

        self.embedding = nn.Embedding(vocab_size, embedding_size)
        self.transformer_encoder = nn.TransformerEncoder(nn.TransformerEncoderLayer(d_model=embedding_size, nhead=num_head, dim_feedforward=hidden_size, dropout=dropout), num_layers=num_layers)
        self.output_layer = nn.Linear(embedding_size, 10)
        self.src_mask = None
        self.d_model = embedding_size

    def forward(self, src: torch.Tensor, src_mask: torch.Tensor) -> torch.Tensor:
        # Embed the input tokens
        embedded = self.embedding(src)  # (batch_size, seq_len, embedding_dim)
        embedded = embedded.transpose(0, 1)  # (seq_len, batch_size, embedding_dim)
        embedded = self.pos_encoder(embedded)  # Apply the positional encoding to the embedded tokens

        # Apply the transformer encoder layer to the embedded tokens
        output = self.transformer_encoder(embedded, src_key_padding_mask=src_mask)  # (seq_len, batch_size, embedding_dim)

        # Map the transformer output to the number of classes
        logits = self.output_layer(output.transpose(0, 1))  # (batch_size, seq_len, num_classes)

        return logits

#modify as required
def validate(
    model: nn.Module,
    dataloader: DataLoader,
    device: torch.device,
):
    acc_metric = torchmetrics.Accuracy(task = 'multiclass', num_classes = 10, compute_on_step=False).to(device)
    loss_metric = torchmetrics.MeanMetric(compute_on_step=False).to(device)
    model.eval()

    with torch.no_grad():
        for batch in tqdm(dataloader):
            input_ids, input_mask, tags = batch[0].to(device), batch[1].to(device), batch[2].to(device)
            # output shape: (batch_size, max_length, num_classes)
            logits = model(input_ids, input_mask)
            # ignore padding index 0 when calculating loss
            loss = F.cross_entropy(logits.reshape(-1, 10), tags.reshape(-1), ignore_index=0)

            loss_metric.update(loss, input_mask.numel() - input_mask.sum())
            is_active = torch.logical_not(input_mask)  # non-padding elements
            # only consider non-padded tokens when calculating accuracy
            acc_metric.update(logits[is_active], tags[is_active])

    print(f"| Validate | loss {loss_metric.compute():.4f} | acc {acc_metric.compute():.4f} |")

#modify as required
from torch import optim

def train(
    model: nn.Module,
    dataloader: DataLoader,
    optimizer: optim.Optimizer,
    device: torch.device,
    epoch: int,
):
    acc_metric = torchmetrics.Accuracy(task = 'multiclass', num_classes = 10, compute_on_step=False).to(device)
    loss_metric = torchmetrics.MeanMetric(compute_on_step=False).to(device)
    model.train()

    # loop through all batches in the training
    for batch in tqdm(dataloader):
        input_ids, input_mask, tags = batch[0].to(device), batch[1].to(device), batch[2].to(device)
        optimizer.zero_grad()
        # output shape: (batch_size, max_length, num_classes)
        logits = model(input_ids, input_mask)
        # ignore padding index 0 when calculating loss
        loss = F.cross_entropy(logits.reshape(-1, 10), tags.reshape(-1), ignore_index=0)

        loss.backward()
        optimizer.step()

        loss_metric.update(loss, input_mask.numel() - input_mask.sum())
        is_active = torch.logical_not(input_mask)  # non-padding elements
        # only consider non-padded tokens when calculating accuracy
        acc_metric.update(logits[is_active], tags[is_active])

    print(f"| Epoch {epoch} | loss {loss_metric.compute():.4f} | acc {acc_metric.compute():.4f} |")

import torch
from torch import optim
from torch.utils.data import DataLoader

# modify this section to load your dataset and set other hyperparameters

torch.manual_seed(42)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# data loaders
train_dataloader = DataLoader(tr_data, batch_size=16, shuffle=True)
val_dataloader = DataLoader(va_data, batch_size=16)
test_dataloader = DataLoader(te_data, batch_size=16)

# move the model to device
model = TransformerModel(vocab_size=len(tokenizer),
                         embedding_size=256,
                         num_head=4,
                         hidden_size=256,
                         num_layers=2).to(device)


optimizer = optim.Adam(model.parameters(), lr=0.001)

for epoch in range(60):
    train(model, train_dataloader, optimizer, device, epoch)
validate(model, val_dataloader, device)

def predict(model: nn.Module, dataloader: DataLoader, device: torch.device) -> List[List[str]]:
    # Set model to evaluation mode
    model.eval()

    # Initialize empty list to store predictions
    preds = []

    with torch.no_grad():
        for batch in tqdm(dataloader):
            # Move input data to device
            input_ids, input_mask = batch[0].to(device), batch[1].to(device)

            # Compute logits for the input data
            logits = model(input_ids, input_mask)

            # Identify active tokens (i.e., non-padding elements) in the input data
            is_active = torch.logical_not(input_mask)

            # Iterate over the logits and active tokens for each sentence in the batch
            for i in range(logits.shape[0]):
                active_logits = logits[i][is_active[i]]

                # Get the predicted tags for each token
                pred = [NERDataset.idx2tag[word.argmax().item()] for word in active_logits]

                # Append the predicted tags for the sentence to the list of predictions
                preds.append(pred)

    # Return the list of predicted tags for each token in the dataset
    return preds

!wget https://raw.githubusercontent.com/sighsmile/conlleval/master/conlleval.py
from conlleval import evaluate

# use the conlleval script to measure the entity-level f1
pred_tags = []
for tags in predict(model, val_dataloader, device):
    pred_tags.extend(tags)
    pred_tags.append('O')

true_tags = []
for tags in val_raw['tags']:
    true_tags.extend(tags.strip().split())
    true_tags.append('O')

evaluate(true_tags, pred_tags)

# YOU SHOULD NOT CHANGE THIS CODEBLOCK
# make prediction on the test set and save to submission.txt
preds = predict(model, test_dataloader, device)
with open("submission.txt", "w") as f:
    for tags in preds:
        f.write(" ".join(tags) + "\n")

pwd

ls

