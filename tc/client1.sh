#!/bin/bash
sudo tc qdisc del dev enp0s9 root
sudo tc qdisc add dev enp0s9 root handle 1:0 tbf rate 100mbit burst 50kb limit 100kb