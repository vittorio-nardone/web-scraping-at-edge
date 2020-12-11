FROM arm32v7/python:3.8

RUN apt-get -y update
RUN apt-get -y upgrade

# Install Firefox and Selenium
RUN apt-get install -y firefox-esr

RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.23.0/geckodriver-v0.23.0-arm7hf.tar.gz
RUN tar -xf geckodriver-v0.23.0-arm7hf.tar.gz
RUN rm geckodriver-v0.23.0-arm7hf.tar.gz
RUN chmod a+x geckodriver
RUN mv geckodriver /usr/local/bin/

RUN apt-get install -y xvfb

RUN pip install selenium==3.141.0
RUN pip install pyvirtualdisplay

# Install boto3
RUN apt-get install -y python3-boto3

RUN mkdir root/.aws/
COPY .aws-credentials /root/.aws/credentials
COPY .aws-config /root/.aws/config

RUN pip install --upgrade pip

COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

COPY src/ /app
WORKDIR /app

CMD ["python", "-u", "./paradox.py"]