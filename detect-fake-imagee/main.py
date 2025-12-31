from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from transformers import AutoModelForImageClassification, AutoImageProcessor
from PIL import Image
import torch
import os
import io

app = FastAPI()

# Path to the downloaded model
model_path = "./ai-image-detector-model2/models--Ateeqq--ai-vs-human-image-detector/snapshots"
# Find the actual snapshot folder (usually only one)
snapshot_dir = os.path.join(model_path, os.listdir(model_path)[0])
# Load model and processor once at startup
model = AutoModelForImageClassification.from_pretrained(snapshot_dir)
processor = AutoImageProcessor.from_pretrained(snapshot_dir, use_fast=True)

@app.post("/analyze-image")
async def analyze_image(file: UploadFile = File(...)):
    try:
        # Read image file
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        # Preprocess and run inference
        inputs = processor(images=image, return_tensors="pt")
        with torch.no_grad():
            outputs = model(**inputs)
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
        # Interpret result
        labels = model.config.id2label
        result = {labels[i]: float(p) for i, p in enumerate(probs[0])}

        # --- Metadata extraction ---
        meta = {}
        try:
            exif_data = image.getexif()
            if exif_data:
                for tag_id, value in exif_data.items():
                    tag = Image.ExifTags.TAGS.get(tag_id, tag_id)
                    meta[str(tag)] = str(value)
            else:
                meta = None
        except Exception as meta_e:
            meta = None

        return JSONResponse(content={"prediction": result, "metadata": meta})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {str(e)}")
