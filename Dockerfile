# Dockerfile for Web-CAT JupyterPlugin grading container
# Pinned to the official Anaconda3 2024.10-1 release (Python 3.12.7)
FROM continuumio/anaconda3:2024.10-1

# Set environment
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/opt/webcat/pythonlib"

# Install Web-CAT python libraries into /opt/webcat/pythonlib
RUN mkdir -p /opt/webcat/pythonlib
COPY pythonlib /opt/webcat/pythonlib

# Set default working directory
WORKDIR /sandbox

# Default entrypoint
CMD ["python", "-m", "pythy.runner"]
