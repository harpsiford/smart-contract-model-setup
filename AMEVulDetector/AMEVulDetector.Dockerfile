FROM --platform=linux/x86_64 tensorflow/tensorflow:2.0.0-py3
RUN pip install --upgrade pip
RUN pip install scikit-learn==0.20.2 numpy==1.18 torch
RUN mkdir /app
COPY . /app
WORKDIR /app
RUN chmod +x ./run.sh && echo "run.sh:" && cat ./run.sh
ENTRYPOINT /bin/bash