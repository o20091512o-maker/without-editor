FROM python:3.10-slim

# Install system dependencies + Node.js 20 + Chromium for Remotion rendering
RUN apt-get update && apt-get install -y \
    curl \
    ffmpeg \
    fonts-cairo \
    chromium \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt-get/lists/*

# Set working directory
WORKDIR /app

# Copy Python requirements & install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Remotion project & install npm dependencies
COPY remotion ./remotion
WORKDIR /app/remotion
RUN npm install --no-audit

# Return to root app directory
WORKDIR /app

# Copy the rest of the application
COPY . .

# Create outputs and temp directories with full write permissions
RUN mkdir -p temp outputs remotion_tmp remotion/public/temp && chmod -R 777 temp outputs remotion_tmp remotion/public/temp

# Set environment variables
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium
ENV PORT=7860
ENV TMPDIR=/app/remotion_tmp
ENV TEMP=/app/remotion_tmp
ENV TMP=/app/remotion_tmp

# Expose Hugging Face default port
EXPOSE 7860

# Start FastAPI server
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
