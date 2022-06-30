#!/bin/bash

#	.		TIMEOUT    CARONTE_IP
#./caronte.sh 30 caronte.com game

if [[ "$#" -ne 3 ]]; then
	echo "Usage: ./caronte.sh <timeout> <ip:port> <interface>"
	exit 2
fi

TIMEOUT_TCPDUMP="$1"
CARONTE_ADDR="$2"
INTERFACE_NAME="$3"

while true; do
	timeout $TIMEOUT_TCPDUMP tcpdump -w data.pcap -i $INTERFACE_NAME port 80
	curl -F "file=@data.pcap" -F "flush_all=true" "http://$CARONTE_ADDR/api/pcap/upload"
	rm data.pcap
done
