# Dockerfile — Bərəkətli Bot for Fly.io
# Use this if flyctl's auto-detection doesn't work cleanly.

FROM python:3.12-slim

# Set working directory inside the container
WORKDIR /app

# Install dependencies first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the bot code
COPY . .

# Fly expects the app to listen on 8080 (our health server does)
EXPOSE 8080

# Start the bot
CMD ["python", "bot.py"]
