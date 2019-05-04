#!/bin/bash
while ! ./app.py
do
	sleep 1
	echo "Restarting......"
done
