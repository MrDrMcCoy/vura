#!/bin/bash

ip="`ifconfig eth0 | grep 'inet addr' | cut -d ':' -f2 | awk '{ print $1 }'`"
echo "Welcome to the VAMI Update Repository Appliance!
To access the UI, please direct your browser to http://$ip/ or log in to configure.
The default root password is vura.

`df -h`" | tee /etc/issue
