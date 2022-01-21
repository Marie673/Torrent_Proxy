#!/bin/bash

# shellcheck disable=SC2034
RATE=110
CONFIG_HZ=250
# shellcheck disable=SC2099
# shellcheck disable=SC1116
BURST=((RATE*1000000)/8)/CONFIG_HZ
# shellcheck disable=SC2125
LIMIT=BURST*2

DELAY=10

# shellcheck disable=SC2154
sudo tc qdisc add dev enp0s9 root handle 1:0 tbf rate ${RATE}mbit burst "${BURST}"b limit "${LIMIT}"b
sudo tc qdisc add dev enp0s9 parent 1:1 handle 10:1 netem delay ${DELAY}ms 0ms distribution normal