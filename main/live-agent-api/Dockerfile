FROM python:3.12-slim

WORKDIR /app

# Install curl for healthcheck and libopus for audio encoding
RUN apt-get update && apt-get install -y --no-install-recommends curl libopus0 && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy project files
COPY . /app/

# Install dependencies using uv
RUN uv sync --no-dev

# Expose port
EXPOSE 8080

# Make start script executable
RUN chmod +x start.sh

# Run the application using start script
CMD ["./start.sh"]
