#!/bin/bash

# shellcheck disable=SC2154
sudo tc qdisc del dev eth1 root
sudo tc qdisc add dev eth1 root handle 1:0 tbf rate 100mbit burst 50kb limit 100kb
sudo tc qdisc add dev eth1 parent 1:1 handle 10:1 netem delay 10ms

sudo tc qdisc del dev eth2 root
sudo tc qdisc add dev eth2 root handle 1:0 tbf rate 100mbit burst 50kb limit 100kb
sudo tc qdisc add dev eth2 parent 1:1 handle 10:1 netem delay 10ms