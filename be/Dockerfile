FROM python:3.10-slim-buster AS production

WORKDIR /ws
COPY be be/
COPY langs langs/
COPY libs libs/
COPY dbm dbm/
COPY grpc_lib grpc_lib/
COPY config.py config.py

WORKDIR /ws/be

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
