# breast_prediction.py
import os
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image

# Load VGG16 model for breast cancer prediction
def load_breast_model(model_path):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = models.vgg16(weights=models.VGG16_Weights.DEFAULT)
    model.classifier = nn.Sequential(
        nn.Linear(512 * 7 * 7, 4096),
        nn.ReLU(True),
        nn.Dropout(0.5),
        nn.Linear(4096, 1024),
        nn.ReLU(True),
        nn.Dropout(0.5),
        nn.Linear(1024, 256),
        nn.ReLU(True),
        nn.Dropout(0.5),
        nn.Linear(256, 3)  # 3 classes: Benign, Normal, Malignant
    )
    model.load_state_dict(torch.load(model_path, map_location=device))
    model = model.to(device)
    model.eval()
    return model, device

# Class names for breast cancer prediction
class_names = ["Benign","Malignant", "Normal"]

# Image transformation
data_transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

# Prediction function for breast cancer
def predict_breast(image_path, model, device):
    image = Image.open(image_path).convert('RGB')
    image_tensor = data_transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        outputs = model(image_tensor)
        _, predicted = torch.max(outputs, 1)
        predicted_class = class_names[predicted.item()]

    return predicted_class
