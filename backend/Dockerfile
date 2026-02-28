FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

# Install PyTorch with CUDA 12.4 support.
# nvidia-container-toolkit on the host injects the driver libraries at runtime.
RUN pip install --no-cache-dir \
    torch --index-url https://download.pytorch.org/whl/cu124

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure data directories exist for named-volume mountpoints.
RUN mkdir -p /app/data /app/chroma_data

EXPOSE 8000

CMD ["gunicorn", "-c", "gunicorn.conf.py", "main:app"]
