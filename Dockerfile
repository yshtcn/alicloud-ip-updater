# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Install any needed packages specified in requirements.txt
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application files into the container
COPY AliCloudIPUpdater.py /app/
COPY config.sample.json /app/

# Create directories for config and logs
RUN mkdir -p /app/config

# Run AliCloudIPUpdater.py when the container launches
CMD ["python", "AliCloudIPUpdater.py"]
