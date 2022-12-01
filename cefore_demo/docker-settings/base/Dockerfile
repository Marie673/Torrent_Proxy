FROM ubuntu:18.04
RUN mkdir -p /cefore
WORKDIR /cefore
RUN apt-get update
RUN apt-get install -y git build-essential libssl-dev
RUN apt-get install -y automake
RUN apt-get install -y iputils-ping net-tools ifstat
RUN apt-get install -y emacs
RUN apt-get install -y python3
RUN apt-get -y clean
RUN git clone https://github.com/cefore/cefore.git
RUN git clone https://github.com/cefore/cefpyco.git
WORKDIR /cefore/cefpyco
RUN apt-get install -y cmake python3-pip
RUN apt-get -y clean
RUN pip3 install --upgrade pip
RUN pip3 install setuptools click numpy
WORKDIR /cefore/runner_test
RUN apt-get -y clean
WORKDIR /cefore/cefore
RUN ./configure --enable-cache --enable-csmgr
RUN make
RUN make install
RUN make clean
RUN ldconfig
WORKDIR /cefore/cefpyco
RUN git pull
RUN cmake .
RUN make install
ENV USER root
ENV LC_ALL C.UTF-8
ENV LANG=C.UTF-8