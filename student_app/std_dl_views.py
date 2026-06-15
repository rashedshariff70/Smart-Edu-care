import os
import numpy as np

from django.shortcuts import render
from django.conf import settings
from django.core.files.storage import FileSystemStorage

# ================================
# KERAS / TENSORFLOW IMPORTS
# ================================
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from tensorflow.keras.preprocessing.image import ImageDataGenerator

# ================================
# CUSTOM MODEL LOGIC
# ================================
from .lung_prediction import load_lung_model, predict_lung
from .breast_prediction import load_breast_model, predict_breast


# ================================
# MODEL PATHS (UPDATED)
# ================================
BREAST_MODEL_PATH = os.path.join(
    settings.BASE_DIR,
    "static", "models", "DL", "breast", "breast_vgg.pth"
)

LUNG_MODEL_PATH = os.path.join(
    settings.BASE_DIR,
    "static", "models", "DL", "lung", "lung_cnn.pth"
)

BRAIN_MODEL_PATH = os.path.join(
    settings.BASE_DIR,
    "static", "models", "DL", "brain_tumour", "mobilenetv2.h5"
)

BRAIN_LABELS_PATH = os.path.join(
    settings.BASE_DIR,
    "static", "models", "DL", "brain_tumour", "class_indices.npy"
)


# ================================
# LOAD MODELS ONCE
# ================================
breast_model, breast_device = load_breast_model(BREAST_MODEL_PATH)
lung_model, lung_device = load_lung_model(LUNG_MODEL_PATH)
brain_model = load_model(BRAIN_MODEL_PATH, compile=False)
brain_input_shape = brain_model.input_shape
BRAIN_IMG_SIZE = (brain_input_shape[1], brain_input_shape[2])


# ================================
# LOAD / GENERATE BRAIN CLASS LABELS
# ================================
if not os.path.exists(BRAIN_LABELS_PATH):
    train_dir = os.path.join(settings.BASE_DIR, "Training")

    datagen = ImageDataGenerator(rescale=1.0 / 255)
    temp_gen = datagen.flow_from_directory(
        train_dir,
        target_size=BRAIN_IMG_SIZE,
        batch_size=1,
        class_mode="categorical"
    )
    np.save(BRAIN_LABELS_PATH, temp_gen.class_indices)

class_indices = np.load(BRAIN_LABELS_PATH, allow_pickle=True).item()
brain_class_labels = {v: k for k, v in class_indices.items()}


# ================================
# COMMON UPLOAD DIRECTORY (STATIC)
# ================================
UPLOAD_DIR = os.path.join(
    settings.BASE_DIR, "static", "uploads", "DL"
)
os.makedirs(UPLOAD_DIR, exist_ok=True)

fs = FileSystemStorage(location=UPLOAD_DIR)


# ================================
# BREAST CANCER VIEW
# ================================
def breast_prediction_view(request):
    context = {}

    if request.method == "POST" and request.FILES.get("image"):
        image = request.FILES["image"]

        filename = fs.save(image.name, image)
        filepath = fs.path(filename)

        prediction = predict_breast(filepath, breast_model, breast_device)

        context["prediction"] = prediction
        context["uploaded_image"] = f"/static/uploads/DL/{filename}"

    return render(request, "breast.html", context)


# ================================
# LUNG CANCER VIEW
# ================================
def lung_prediction_view(request):
    context = {}

    if request.method == "POST" and request.FILES.get("image"):
        image = request.FILES["image"]

        filename = fs.save(image.name, image)
        filepath = fs.path(filename)

        prediction = predict_lung(filepath, lung_model, lung_device)

        context["prediction"] = prediction
        context["uploaded_image"] = f"/static/uploads/DL/{filename}"

    return render(request, "lung.html", context)


# ================================
# BRAIN TUMOR VIEW
# ================================
def brain_tumor_prediction_view(request):
    prediction = None
    probabilities = None
    img_url = None

    if request.method == "POST" and request.FILES.get("image"):
        image = request.FILES["image"]

        filename = fs.save(image.name, image)
        img_path = fs.path(filename)

        # Preprocess image
        img = load_img(img_path, target_size=BRAIN_IMG_SIZE)
        img_array = img_to_array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)

        # Prediction
        preds = brain_model.predict(img_array, verbose=0)
        class_id = np.argmax(preds)

        prediction = brain_class_labels[class_id]

        probabilities = {
            brain_class_labels[i]: round(float(preds[0][i]) * 100, 2)
            for i in range(len(brain_class_labels))
        }

        img_url = f"/static/uploads/DL/{filename}"

    return render(
        request,
        "brain_tumor.html",
        {
            "prediction": prediction,
            "probs": probabilities,
            "img_path": img_url,
        }
    )
