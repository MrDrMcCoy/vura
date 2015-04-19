The scripts in this directory will assist you in configuring your own VURA appliance. Please note that they were intended to be run on Ubuntu 14.04, and may need to be adapted to run on your system.

If the partition VURA lives in is a logicial volume dedicated to it, the scripts under linux_suppliments should be copied to another partition to allow them to function properly.

The following additions to rc.local are recommended:

	# Detect new disks and add them to the logical volume you store VURA on. This is optional, and requires configuration to match how you have set up your logical volumes. If you are not using logical volumes, please comment out this command.
	bash /opt/diskadd.sh
	sync
	sleep 5
	mount -a

	# Set the login message to include the local IP address and login info. This is optional, and can be adjusted as you see fit.
	bash /opt/issue.sh

	# Run VURA as the user 'vura'. If the VURA user does not have permissions to bind to port 80, you will need to install and configure authbind or run this as root. 
	su vura -c 'bash -c "cd /data/vura && ./launcher.sh &"'
