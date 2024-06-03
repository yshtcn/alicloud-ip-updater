# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the sample config file into the image
COPY config.sample.json /app/config.sample.json

# Run update_aliyun.py when the container launches
CMD ["python", "AliCloudIPUpdater.py"]
