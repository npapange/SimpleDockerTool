#Using ubuntu as the basis.
FROM ubuntu:latest

#Name of author.
MAINTAINER Nikitas Papangelopoulos "npapange@sdsc.edu"

#Description of image.
LABEL Description="An image to create a container for a simple 'Hello World!' flask webapp"

#Updating ubuntu.
RUN apt-get update -y

#Installing python.
RUN apt-get install -y python-pip python-dev

#Copying just the requirements.txt
COPY requirements.txt /web_app/requirements.txt

#Setting the working directory.
WORKDIR /web_app

#Installing requirements.
RUN pip install -r requirements.txt

#Copying the rest of the files inside the image.
COPY . /web_app

#Exposing the port that the flask server uses.
EXPOSE 5000

#Commands to execute.
ENTRYPOINT [ "python" ]
CMD [ "web_app.py" ]