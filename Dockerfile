FROM python:3.9

RUN pip install arkitekt==0.1.91

# Install Arbeid
RUN mkdir /workspace
ADD . /workspace
WORKDIR /workspace



CMD [ "python", "-u", "run.py" ]