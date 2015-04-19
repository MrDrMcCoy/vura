#!/bin/bash

VOLUME_GROUP=vg0
VOLUME_NAME=data
MOUNT_PATH=/data
LOG="/var/log/diskadd.log"

exitfunc() {
   echo $1 | tee -a $LOG
   #always try and mount the data disk
   mount /dev/$VOLUME_GROUP/$VOLUME_NAME $MOUNT_PATH -o defaults,nodev,noacl,nosuid,exec | tee -a $LOG  2>&1
   exit 1
}

echo "Running diskadd at `date`" | tee -a $LOG

#activate the logical volume
lvchange -ay /dev/$VOLUME_GROUP/$VOLUME_NAME  | tee -a $LOG  2>&1
if [ $? -ne 0 ]; then
   exitfunc "Could not activate logical volume"
fi

#identify all disks with no partitions (leave out /dev/dm-0 as that is not a disk we have added)
disks=(`fdisk -l 2>&1 | grep -v '/dev/dm-'| grep 'contain a valid partition table' | grep -v "/dev/mapper/$VOLUME_GROUP-" | awk '{print $2}' |tr '\n' ' '`)
#Get the list of LVM physical volumes
pvolumes=(`pvdisplay | grep 'PV Name' | awk '{print $3}'`)
expanded=false
if [ ${#disks[*]} -ne 0 ]
then
   #unmount the data disk
   umount /dev/$VOLUME_GROUP/$VOLUME_NAME | tee -a  $LOG  2>&1
   if [ $? -ne 0 ]; then
      exitfunc "Could not unmount data disk"
   fi

   #for all disks with no partition check to see if there is a lvm physical volume with the same name, if not create one
   for disk in ${disks[@]}
   do
      echo Processing $disk | tee -a $LOG
      found=false;
      for volume in ${pvolumes[@]}
      do
         if [ $disk == $volume ]; then
            found=true;
            break;
         fi
      done
      # new disk with no LVM physical volume. Create one and add it to the volume group
      if [ $found == false ]; then
         echo "Adding new disk $disk to the LVM logical group"
         echo "Adding new disk $disk to the LVM logical group" | tee -a $LOG
         expanded=true;
         # create a physical volume.
         pvcreate $disk  | tee -a $LOG  2>&1
         if [ $? -ne 0 ]; then
            echo "Could not create Physical Volume" | tee -a $LOG
            continue
         fi

         vgextend $VOLUME_GROUP $disk  | tee -a $LOG  2>&1
         if [ $? -ne 0 ]; then
            echo "Could not extend Volume Group" | tee -a $LOG
            continue
         fi
         extents=`pvdisplay $disk | grep "Free PE" | awk '{print $3}'`
         lvextend -fnrl +${extents} /dev/$VOLUME_GROUP/$VOLUME_NAME | tee -a $LOG  2>&1
         if [ $? -ne 0 ]; then
            echo "Could not extend Logical Volume" | tee -a $LOG
            continue
         fi
      fi
   done
fi

#finally mount the data disk
mount -a 2>&1 | tee -a $LOG  2>&1

exit 0
