# -------------------------------------------------------------------
# Autonomous AI Lead Acquisition & 24/7 Inbox Sentinel Container
# -------------------------------------------------------------------
FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=America/New_York

# Install system dependencies & timezone configuration
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Ensure entrypoint has execution permissions
RUN chmod +x entrypoint.sh 2>/dev/null || true

# Web Dashboard Port
EXPOSE 8000

# Start both 24/7 Background Daemon & Web Dashboard
CMD ["bash", "entrypoint.sh"]
