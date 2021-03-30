FROM python:3.8

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV PATH /opt/conda/bin:/opt/conda/envs/env/bin:$PATH

RUN apt-get update --fix-missing
RUN apt-get install -y wget bzip2 ca-certificates \
    libglib2.0-0 libxext6 libsm6 libxrender1 \
    python3-pip software-properties-common build-essential \
    make sqlite3 gfortran python-dev \
    git mercurial subversion

RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-py37_4.8.3-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda && \
    rm ~/miniconda.sh && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
    echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc && \
    echo "conda activate base" >> ~/.bashrc

RUN apt-get install -y curl grep sed dpkg && \
    TINI_VERSION=`curl https://github.com/krallin/tini/releases/latest | grep -o "/v.*\"" | sed 's:^..\(.*\).$:\1:'` && \
    curl -L "https://github.com/krallin/tini/releases/download/v${TINI_VERSION}/tini_${TINI_VERSION}.deb" > tini.deb && \
    dpkg -i tini.deb && \
    rm tini.deb && \
    apt-get clean

RUN apt update -y && apt install -y --fix-missing --no-install-recommends \
    python3-pip software-properties-common build-essential \
    cmake sqlite3 gfortran python-dev

# gdal vesion restriction due to fiona not supporting gdal>2.4.3
ARG GDAL_VERSION=3.1.4
ARG CONDA_ENV="base"

COPY environment.yml /src/environment.yml
RUN conda env update -n=$CONDA_ENV -f /src/environment.yml
RUN conda install -n=$CONDA_ENV -c conda-forge gdal=$GDAL_VERSION -y

RUN activate $CONDA_ENV
RUN conda update conda -y
RUN conda info

COPY . /src/

# Updating Anaconda packages
RUN conda install -n=$CONDA_ENV -c conda-forge uwsgi
COPY uwsgi.ini /etc/uwsgi/uwsgi.ini

WORKDIR /src
EXPOSE 8080
#ENTRYPOINT ["uwsgi", "--ini", "/etc/uwsgi/uwsgi.ini"]
#ENTRYPOINT ["flask", "run", "-p", "8080", "-h", "0.0.0.0", "--debugger"]
ENTRYPOINT ["python", "wb_flask.py"]