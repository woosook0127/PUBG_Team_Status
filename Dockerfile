# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
# Ensures Python prints everything to stdout/stderr immediately (good for logging in containers)
ENV PYTHONUNBUFFERED 1
# Environment variable for the API key (will be passed during `docker run`)
ENV PUBG_API_KEY=""

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# --no-cache-dir: Disables the cache, which is good for keeping image size down.
# --upgrade pip: Upgrades pip to the latest version before installing packages.
RUN pip install --no-cache-dir --upgrade pip -r requirements.txt

# Copy the rest of the application code into the container at /app
# This includes the 'app/' directory, 'static/' directory, and other root files.
COPY ./app ./app
COPY ./static ./static
# Optional: Copy other useful files like README or testing guide if desired in image
# COPY README.md .
# COPY MANUAL_TESTING_GUIDE.md .

# Expose port 8000 to the outside world once the container has launched
EXPOSE 8000

# Define the command to run the application
# This command will be executed when the container starts.
# It runs Uvicorn, telling it where to find the FastAPI application (app.main:app),
# to listen on all network interfaces (--host 0.0.0.0), and on port 8000.
# --reload is typically not used in production Docker images; remove it for production builds.
# For this task, including it is acceptable for easier development/testing if the image is used for that.
# However, for a "production-ready" Dockerfile, --reload should be omitted.
# Let's omit --reload for a cleaner production-like image.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
