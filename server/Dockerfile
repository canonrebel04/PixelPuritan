FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for Pillow/Torch
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Pre-download the model during build to speed up startup
# calling a tiny python script to trigger the download
RUN python3 -c "from transformers import pipeline; pipeline('image-classification', model='AdamCodd/vit-base-nsfw-detector')"

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
