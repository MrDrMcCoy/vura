About

The VAMI Update Repository Appliance is a tool to help you create a portable update repository for VAMI-enabled VMware appliances. This allows you to transport the necessary bits to perform upgrades to network locations without internet access.

Prerequisites:
* VMware ESXi (www.vmware.com)
* VMware vSphere client (www.vmware.com)
* 7-zip (www.7-zip.org)

Usage

0. Extract vura.7z on a machine that can deploy VMs in your environment. 
1. Deploy the appliance image on a host and network with internet access.
2. Configure the networking settings with SSH/Console access, if desired. The root password is "vura" by default. The system is Ubuntu in case you need to make adjustments that are not covered here.
3. Expand the /data volume of this appliance by adding a disk and rebooting or using LVM. You can verify that the disk space has been added by typing "df -h" on the command line of the appliance.
4. Navigate to the VAMI page of your desired appliance and locate the RepositoryURL on the Update>Settings tab. The page can usually be accessed by navigating to https://[Appliance IP Address]:5480.
5. Copy the RepositoryURL from the VAMI appliance to the URL field on the web page of your vura appliance.
6. Enter a repository name to help you identify the product name and version. No spaces, please.
7. Press the Create button.
8. Wait until the status under Current Repositories shows "Ready".
9. Move this appliance to your desired network location.
10a. Copy the URL of your new repo from the VURA status page into the VAMI Update page of your appliance. 
10b. Download the ISO image and attach it to your VM. The Update page 
11. Update and enjoy!

Dependencies for running source version:
*Linux
*Nginx
*fcgiwrap
*python2
*coreutils
*aria2c
*genisoimage
