FROM tensorflow/tensorflow:1.14.0-py3
RUN mkdir /app
COPY . /app
WORKDIR /app
RUN pip install --upgrade pip
RUN pip install pip install keras==2.2.4 scikit-learn==0.20.2 docopt pandas
RUN chmod +x ./run.sh && echo "run.sh:" && cat ./run.sh
ENTRYPOINT /bin/bash