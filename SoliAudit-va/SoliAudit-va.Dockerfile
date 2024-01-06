FROM ubuntu:18.04

# set system env =====================================
SHELL ["/bin/bash", "--login", "-c"]
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
        software-properties-common apt-utils sudo tzdata \
        curl wget iputils-ping net-tools uuid bzip2 unzip gnupg vim \
        git
RUN ln -sf /usr/share/zoneinfo/ROC /etc/localtime && \
    echo "Asia/Taipei" > /etc/timezone
RUN curl -sL https://github.com/ethereum/solidity/releases/download/v0.4.24/solc-static-linux -o /usr/bin/solc && \
    chmod +x /usr/bin/solc


## Anaconda for ML
RUN mkdir -p ~/miniconda3 && \
    wget "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh" -O ~/miniconda3/miniconda.sh && \
    bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3 && \
    rm ~/miniconda3/miniconda.sh && ~/miniconda3/bin/conda init bash
ENV PATH=/root/miniconda3/bin:$PATH
RUN conda create -y -n learning python=3.7 numpy=1.19.5 pandas=1.3.5 matplotlib scikit-learn=0.19.2 word2vec tensorflow keras setuptools=58.0.4

# setting up app home ==============================
WORKDIR /root
COPY ./docker-va/data/utest-config.json .
COPY ./vul-predict ./vul-predict
COPY ./run-anlyzers ./run-anlyzers
COPY ./tools ./tools
COPY ./features ./features
COPY ./run.sh ./run.sh
### uncomment this to copy smart contract source code 
#   into the image (not enabled to preserve space)
# COPY ./sc-src ./sc-src
#   processed datasets are already in features/, but 
#   the trainer also generates a temporary dataset under 
#   ./vul-predict/test-data.csv

### Custom scripts
COPY ./convert*.py ./vul-predict/
RUN chmod +x ./run.sh && echo "run.sh:" && cat ./run.sh
ENTRYPOINT /bin/bash