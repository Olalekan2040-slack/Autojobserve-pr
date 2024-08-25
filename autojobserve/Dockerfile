# Use a base image with Python 3.11
FROM python:3.11.0

# Set the working directory
WORKDIR /AUTOJOBSERVE

# Copy requirements.txt to the container
COPY ./requirements.txt /AUTOJOBSERVE/requirements.txt

# Install required dependencies
RUN apt-get update \
    && apt-get install -y gcc wget unzip \
    && apt-get clean \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --upgrade setuptools \
    && pip install --no-cache-dir --upgrade wheel \
    && pip install --no-cache-dir --upgrade -r /AUTOJOBSERVE/requirements.txt


# Copy the rest of the application code to the container
COPY ./autojobserve /AUTOJOBSERVE/autojobserve
COPY ./selenium_scripts /AUTOJOBSERVE/selenium_scripts
COPY ./scripts/01.sql /AUTOJOBSERVE/scripts/01.sql     
COPY ./CV /AUTOJOBSERVE/CV 

# Set environment variables
ENV GLASSDOOR_USER="victoriadappa5@gmail.com"
ENV GLASSDOOR_PASSWORD="Vickyblessed!"

# Expose port 8000
EXPOSE 8000

CMD ["uvicorn", "autojobserve.app:app", "--host", "0.0.0.0", "--port", "8000"]



# # Use a base image with Python 3.11
# FROM python:3.11.0

# # Set the working directory
# WORKDIR /PROJECT

# # Copy requirements.txt to the container
# COPY ./requirements.txt /PROJECT/requirements.txt

# # Install required dependencies
# RUN apt-get update \
#     && apt-get install -y gcc wget unzip \
#     && apt-get clean \
#     && pip install --no-cache-dir --upgrade pip \
#     && pip install --no-cache-dir --upgrade setuptools \
#     && pip install --no-cache-dir --upgrade wheel \
#     && pip install --no-cache-dir --upgrade -r /PROJECT/requirements.txt

# # Copy the rest of the application code to the container
# COPY ./autojobserve /autojobserve
# COPY ./autojobserve/scripts/01.sql /autojobserve/scripts/01.sql
# COPY ./autojobserve/selenium_scripts /autojobserve/selenium_scripts

# ENV GLASSDOOR_USER="victoriadappa5@gmail.com"        
# ENV GLASSDOOR_PASSWORD="Vickyblessed!"        
                                              
# # Expose port 8000                
# EXPOSE 8000

# CMD ["uvicorn", "autojobserve.app:app", "--host", "0.0.0.0", "--port", "8000"]




# # Use a base image with Python 3.11
# FROM python:3.11.0

# # Set the working directory
# WORKDIR /PROJECT

# # Copy requirements.txt to the container
# COPY ./requirements.txt /PROJECT/requirements.txt

# # Install required dependencies
# RUN apt-get update \
#     && apt-get install -y gcc wget unzip \
#     && apt-get clean \
#     && pip install --no-cache-dir --upgrade pip \
#     && pip install --no-cache-dir --upgrade setuptools \
#     && pip install --no-cache-dir --upgrade wheel \
#     && pip install --no-cache-dir --upgrade -r /PROJECT/requirements.txt

# # Copy the rest of the application code to the container
# COPY ./PROJECT /autojobserve
# COPY ./PROJECT/autojobserve/scripts/01.sql /autojobserve/scripts/01.sql
# COPY ./PROJECT/autojobserve/selenium_scripts /autojobserve/selenium_scripts

# ENV GLASSDOOR_USER="victoriadappa5@gmail.com"
# ENV GLASSDOOR_PASSWORD="Vickyblessed!"

# # Expose port 8000
# EXPOSE 8000

# CMD ["uvicorn", "autojobserve.app:app", "--host", "0.0.0.0", "--port", "8000"]




