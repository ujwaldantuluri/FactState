import os
from transformers import AutoImageProcessor, AutoModelForImageClassification

# Define the cache directory
cache_dir = "models_cache"
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)

# Specify the model name
model_name = "Ateeqq/ai-vs-human-image-detector"

try:
    # Download and cache the image processor
    print("Downloading image processor...")
    image_processor = AutoImageProcessor.from_pretrained(model_name, cache_dir=cache_dir)
    print("Image processor downloaded successfully.")

    # Download and cache the model
    print("Downloading model...")
    model = AutoModelForImageClassification.from_pretrained(model_name, cache_dir=cache_dir)
    print("Model downloaded successfully.")

except Exception as e:
    print(f"An error occurred: {e}")