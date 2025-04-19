FROM docker.io/python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY src/ /app/src/
COPY data/ /app/data/
COPY .env /app/.env
COPY EU-Ai-Act.pdf /app/EU-Ai-Act.pdf
COPY prompts.pdf /app/prompts.pdf
COPY EU-Ai-Act.txt /app/EU-Ai-Act.txt
COPY prompts.txt /app/prompts.txt

# Create necessary directories
RUN mkdir -p /app/output 

# Set the entrypoint to run the test suite
ENTRYPOINT ["python", "-m", "src.run_test_suite"]

# Default command with skip-retrieval flag to avoid Pinecone dependency
CMD ["--debug"]
