1. Download CorePlus.iso
  $> wget http://distro.ibiblio.org/tinycorelinux/6.x/x86/release/CorePlus-current.iso

2. Create an empty qcow2 drive
  $> qemu-img create -f qcow2 tinycore.qcow2 1G
  
3. Boot TinyCore
  $> kvm -hda tinycore.qcow2 -cdrom CorePlus-current.iso -boot d -m 200
  * Select default boot mode

4. Install TinyCore
  * Select installer from bottom menu
  * 1st screen: "Frugal", "Whole disk", "sda"
  * 2nd screen: "ext4"
  * 3rd screen: "kmap=qwertz/de-latin1-nodeadkeys superuser"
  * 4th screen: "Core only", "Non-US keyboard layout support"
  * Shutdown TinyCore after installation
  
5. Compress plain tinycore  
  $> qemu-img convert -c -O qcow2 tinycore.qcow2 tinycore-6.3.qcow2
 
6. Create OpenVSwitch template
  $> kvm -hda tinycore.qcow2 -m 1500 &
  $> python -c "import SimpleHTTPServer;SimpleHTTPServer.test()" 8123
  KVM:$> wget -q http://10.0.2.2:8123/create-ovs.sh -O - | sudo -u tc sh
  $> #(crtl-c)
  $> qemu-img convert -c -O qcow2 tinycore.qcow2 tinycore-6.3-openvswitch-2.4.qcow2