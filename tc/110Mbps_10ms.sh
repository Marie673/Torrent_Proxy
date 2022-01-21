#!/bin/bash

# shellcheck disable=SC2154
sudo tc qdisc add dev enp0s9 root handle 1:0 tbf rate 110mbit burst 50kb limit 100kb
sudo tc qdisc add dev enp0s9 parent 1:1 handle 10:1 netem delay 10ms 0ms distribution normal