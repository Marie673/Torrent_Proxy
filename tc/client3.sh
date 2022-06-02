#!/bin/bash
sudo tc qdisc del dev eth1 root
sudo tc qdisc add dev eth1 root handle 1:0 tbf rate 100mbit burst 50kb limit 100kb