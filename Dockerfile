FROM python:3.11-slim

# Set working directory
WORKDIR /app

# System deps (if voice or opus is ever needed in future)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run the bot
CMD ["python", "dwbot.py"]
