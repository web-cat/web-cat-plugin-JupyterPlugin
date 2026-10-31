# Dockerfile for Web-CAT JupyterPlugin grading container
# Based on the official full Anaconda3 image
FROM continuumio/anaconda3:latest

# Set environment
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/opt/webcat/pythonlib:${PYTHONPATH}"

# Install Web-CAT python libraries into /opt/webcat/pythonlib
RUN mkdir -p /opt/webcat/pythonlib
COPY pythonlib /opt/webcat/pythonlib

# Set default working directory
WORKDIR /sandbox

# Default entrypoint
CMD ["python", "-m", "pythy.runner"]

