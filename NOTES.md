download cloudimg
mount using guestmount
update grub.cfg with nocloud
unmount
qmeu convert to vmdk


---
create meta-data with hostname
create user-data with pwd and scripts,etc
create seed.ISO

on esxi
create folder on datastore1
push vmdk to folder
resize vmdk to sizeX
create vmx with sizing parameters
push seed.iso
attach seed.iso

start server


.encoding = "UTF-8"
config.version = "8"
virtualHW.version = "8"
pciBridge0.present = "TRUE"
pciBridge4.present = "TRUE"
pciBridge4.virtualDev = "pcieRootPort"
pciBridge4.functions = "8"
pciBridge5.present = "TRUE"
pciBridge5.virtualDev = "pcieRootPort"
pciBridge5.functions = "8"
pciBridge6.present = "TRUE"
pciBridge6.virtualDev = "pcieRootPort"
pciBridge6.functions = "8"
pciBridge7.present = "TRUE"
pciBridge7.virtualDev = "pcieRootPort"
pciBridge7.functions = "8"
vmci0.present = "TRUE"
hpet0.present = "TRUE"
nvram = "cloud-init-test.nvram"
virtualHW.productCompatibility = "hosted"
powerType.powerOff = "soft"
powerType.powerOn = "hard"
powerType.suspend = "hard"
powerType.reset = "soft"
displayName = "cloud-init-test"
extendedConfigFile = "cloud-init-test.vmxf"
floppy0.present = "TRUE"
memsize = "2048"
ide0:0.present = "TRUE"
ide0:0.fileName = "trusty-server-nocloud-amd64-disk1.vmdk"
ide1:0.present = "TRUE"
ide1:0.clientDevice = "FALSE"
ide1:0.deviceType = "cdrom-image"
ide1:0.startConnected = "TRUE"
floppy0.startConnected = "FALSE"
floppy0.fileName = ""
floppy0.clientDevice = "TRUE"
ethernet0.present = "TRUE"
ethernet0.virtualDev = "e1000"
ethernet0.networkName = "VM Network"
ethernet0.addressType = "vpx"
guestOS = "ubuntu-64"
uuid.location = "56 4d 69 5d 63 26 1b 9e-10 5d b7 a4 c4 33 13 b3"
uuid.bios = "56 4d 69 5d 63 26 1b 9e-10 5d b7 a4 c4 33 13 b3"
vc.uuid = "52 c3 ba 06 20 09 6e 7b-eb d3 5e 6c 44 16 b3 56"
ethernet0.generatedAddress = "00:50:56:98:1e:83"
ide1:0.fileName = "/vmfs/volumes/5579c5e8-b7a239da-c3ce-7845c4f8a1d5/seeds/seed.iso"
ethernet0.pciSlotNumber = "32"
vmci0.id = "-1003285581"
vmci0.pciSlotNumber = "33"
tools.syncTime = "FALSE"
cleanShutdown = "TRUE"
replay.supported = "FALSE"
sched.swap.derivedName = "/vmfs/volumes/5579c5e8-b7a239da-c3ce-7845c4f8a1d5/cloud-init-test/cloud-init-test-0fec0c96.vswp"
replay.filename = ""
ide0:0.redo = ""
pciBridge0.pciSlotNumber = "17"
pciBridge4.pciSlotNumber = "21"
pciBridge5.pciSlotNumber = "22"
pciBridge6.pciSlotNumber = "23"
pciBridge7.pciSlotNumber = "24"
tools.remindInstall = "TRUE"
hostCPUID.0 = "0000000d756e65476c65746e49656e69"
hostCPUID.1 = "000206d70020080017bee3ffbfebfbff"
hostCPUID.80000001 = "0000000000000000000000012c100800"
guestCPUID.0 = "0000000d756e65476c65746e49656e69"
guestCPUID.1 = "000206d700010800969822030fabfbff"
guestCPUID.80000001 = "00000000000000000000000128100800"
userCPUID.0 = "0000000d756e65476c65746e49656e69"
userCPUID.1 = "000206d700200800169822030fabfbff"
userCPUID.80000001 = "00000000000000000000000128100800"
evcCompatibilityMode = "FALSE"
vmotion.checkpointFBSize = "4194304"
softPowerOff = "TRUE"

guestmount -a trusty-server-cloudimg-amd64-disk1.img -m /dev/sdx1 /large/trusty/tmpmount
sed -i "s/ttyS0/ttyS0 ds=nocloud/g" /large/trusty/tmpmount/boot/grub/grub.cfg
umount /large/trusty/tmpmount
mv trusty-server-cloudimg-amd64-disk1.img trusty-server-nocloud-amd64-disk1.img
qemu-img convert -f qcow2 trusty-server-nocloud-amd64-disk1.img -O vmdk trusty-server-nocloud-amd64-disk1.vmdk


cat > meta-data << EOF
instance-id: iid-local01
local-hostname: nocloud
hostname: nocloud
EOF

cat > user-data << EOF
#cloud-config
password: ubuntu
chpasswd: { expire: False }
ssh_pwauth: True
write_files:
  - path: /tmp/cloud-script.sh
    permissions: '0755'
    owner: root:root
    content: |
      #!/bin/bash
runcmd:
  - /tmp/cloud-script.sh
EOF

genisoimage -output seed.iso -volid cidata -joliet -rock user-data meta-data






config.version = "8"
virtualHW.version = "7"
vmci0.present = "TRUE"
displayName = "${NAME}"
floppy0.present = "FALSE"
numvcpus = "${CPU}"
scsi0.present = "TRUE"
scsi0.sharedBus = "none"
scsi0.virtualDev = "lsilogic"
memsize = "${RAM}"
scsi0:0.present = "TRUE"
scsi0:0.fileName = "${NAME}.vmdk"
scsi0:0.deviceType = "scsi-hardDisk"
ide1:0.present = "TRUE"
ide1:0.fileName = "${ISO}"
ide1:0.deviceType = "cdrom-image"
pciBridge0.present = "TRUE"
pciBridge4.present = "TRUE"
pciBridge4.virtualDev = "pcieRootPort"
pciBridge4.functions = "8"
pciBridge5.present = "TRUE"
pciBridge5.virtualDev = "pcieRootPort"
pciBridge5.functions = "8"
pciBridge6.present = "TRUE"
pciBridge6.virtualDev = "pcieRootPort"
pciBridge6.functions = "8"
pciBridge7.present = "TRUE"
pciBridge7.virtualDev = "pcieRootPort"
pciBridge7.functions = "8"
ethernet0.pciSlotNumber = "32"
ethernet0.present = "TRUE"
ethernet0.virtualDev = "e1000"
ethernet0.networkName = "Inside"
ethernet0.generatedAddressOffset = "0"
guestOS = "other26xlinux-64"


