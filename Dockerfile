# Use the official Python image as the base image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements.txt file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Flask application code into the container
COPY app.py .

# Expose the port that Flask will be running on
EXPOSE 5000

# Set the command to run the Flask application
CMD ["flask", "run", "--host=0.0.0.0"]
