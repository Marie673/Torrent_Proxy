FROM ubuntu:20.04
ENV TZ=Asia/Tokyo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN mkdir -p /cefore
WORKDIR /cefore
RUN apt-get update
RUN apt-get install -y git build-essential libssl-dev libtool
RUN apt-get install -y emacs
RUN apt-get install -y iputils-ping net-tools ifstat
RUN apt-get install -y python3
RUN apt-get install -y cmake python3-pip
RUN pip3 install --upgrade pip
RUN pip3 install setuptools click numpy

#RUN apt-get install -y automake autoconf m4

RUN apt-get install -y wget
RUN apt-get install -y perl
RUN apt-get install -y autoconf
RUN wget -q https://ftp.gnu.org/gnu/automake/automake-1.15.1.tar.gz
RUN tar -xzvf automake-1.15.1.tar.gz
WORKDIR /cefore/automake-1.15.1
RUN ./configure
RUN make
RUN make install

RUN apt-get -y clean

WORKDIR /cefore
RUN git clone https://github.com/cefore/cefore.git
RUN git clone https://github.com/cefore/cefpyco.git

WORKDIR /cefore/cefore
# RUN autoreconf -f -i
RUN autoconf
RUN automake
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