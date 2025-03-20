# Use an official Python image
FROM python:3.11

# Set the working directory inside the container
WORKDIR /app

# Install uv (equivalent of pip but in rust but faster)
RUN pip install uv

# Ensure ~/.local/bin is in PATH
ENV PATH="/root/.local/bin:${PATH}"

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN uv pip install --system --no-cache-dir -r requirements.txt