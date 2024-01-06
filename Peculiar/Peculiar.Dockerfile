FROM python:3.6.9-slim
RUN mkdir -p /app/dataset /app/SASC_dataset
COPY ./src/ /app
COPY ./run.sh /app
COPY ./dataset/ /app/dataset/
COPY ./SASC_dataset/ /app/SASC_dataset/
COPY ./validate_resnet.cfg /app
WORKDIR /app
RUN python3 -m pip install -U pip
RUN python3 -m pip install -r requirements.txt
RUN chmod +x ./run.sh && echo "run.sh:" && cat ./run.sh
ENTRYPOINT /bin/bash