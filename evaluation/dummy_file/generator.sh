#!/bin/bash

dd if=/dev/zero of=128MB bs=1M count=128
dd if=/dev/zero of=256MB bs=1M count=256
dd if=/dev/zero of=512MB bs=1M count=512
dd if=/dev/zero of=1024MB bs=1M count=1024
dd if=/dev/zero of=2048MB bs=1M count=2048
