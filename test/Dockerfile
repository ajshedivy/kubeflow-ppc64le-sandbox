# Use an official Python runtime as a parent image, on ppc64le architecture
FROM ppc64le/python:3.8-slim

# Set the working directory in the container
USER root
WORKDIR /root

# Copy the current directory contents into the container at /usr/src/app
COPY test.py .

# Use pip to install tornado
RUN pip install --no-cache-dir tornado


# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir tornado

# Make port 8888 available to the world outside this container
EXPOSE 8888

# Run app.py when the container launches
CMD ["python", "./test.py"]

