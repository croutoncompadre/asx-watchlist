# Use a slim Python 3.11 image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all app code
COPY . .

# Set default environment variables
ENV CONFIG_PATH="/app/config.yaml"

# Command is no longer backgrounding multiple scripts.
# We'll run each bot in its own service via docker-compose
CMD ["python", "asx_catalyst_bot.py"]
