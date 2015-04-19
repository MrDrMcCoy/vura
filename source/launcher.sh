#!/bin/bash
trap exit SIGKILL SIGTERM SIGINT
echo $$ > vura.pid
if [ "$USER" != root ]; then
	if [ -x "`which authbind`" ]; then
		if [ ! -x "/etc/authbind/byport/80" ]; then
			echo "authbind needs to be configured to allow unprivilidged use of port 80"
			sudo touch /etc/authbind/byport/80
			sudo chown $USER:$USER /etc/authbind/byport/80
			sudo chmod 550 /etc/authbind/byport/80
		fi
		authbind --deep python vura.py
	else
		echo "authbind not available,running as root to allow binding port 80"
		sudo python vura.py
	fi
else
	python vura.py
fi
rm vura.pid
