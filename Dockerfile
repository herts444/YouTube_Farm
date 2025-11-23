# YouTube Farm - Telegram Bot for Automated Video Generation
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (ffmpeg, imagemagick, Manim dependencies, etc.)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    git \
    build-essential \
    pkg-config \
    libcairo2-dev \
    libpango1.0-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p output/cuts output/reddit output/educational output/horror output/facts output/history output/news \
    && mkdir -p assets/cartoons assets/films \
    && mkdir -p db

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8

# Expose port (if needed for health checks)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import os; exit(0 if os.path.exists('main.py') else 1)"

# Run the bot
CMD ["python", "main.py"]
