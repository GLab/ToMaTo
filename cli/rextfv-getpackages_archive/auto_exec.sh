#!/bin/bash
#
# modes.
#  assumption: only one mode file.
#  the modes are: prepare-install, prepare-upgrade, install
#  mode is selected by presence of mode file. filenames:
#   toinstall - prepare-install; file contains whitespace-seperated packet list
#   upgrade - prepare-upgrade; content does not matter.
#   packages - install; packages is a directory.
#			there must be a installorder_$os_id file, which is a 
#			linebreak-seperated file list of files inside the packages directory
#
# identifiers
apt_get_ident="aptget"

get_os_id() {
	DISTRO=""
	ISSUE=$(cat /etc/issue)
	case "$ISSUE" in
	  Debian*5.0*)
	    DISTRO="debian_5"
	    ;;
	  Debian*6.0*)
	    DISTRO="debian_6"
	    ;;
	  Debian*7*)
	    DISTRO="debian_7"
	    ;;
	  Ubuntu*10.04*)
	    DISTRO="ubuntu_1004"
	    ;;
	  Ubuntu*10.10*)
	    DISTRO="ubuntu_1010"
	    ;;
	  Ubuntu*11.04*)
	    DISTRO="ubuntu_1104"
	    ;;
	  Ubuntu*11.10*)
	    DISTRO="ubuntu_1110"
	    ;;
	  Ubuntu*12.04*)
	    DISTRO="ubuntu_1204"
	    ;;
	  Ubuntu*12.10*)
	    DISTRO="ubuntu_1210"
	    ;;
	  Ubuntu*13.04*)
	    DISTRO="ubuntu_1304"
	    ;;
	  Ubuntu*13.10*)
	    DISTRO="ubuntu_1310"
	    ;;
	  *)
	    DISTRO="UNKNOWN"
	esac
	echo "${DISTRO}_$(uname -m)"
}

os_id=$(get_os_id)



# handlers for apt-get
need_apt_get () {
	if which apt-get; then
		return 0;
	else
		return 1;
	fi
}

update_apt_get () {
	dhclient eth0
	apt-get update
}
setstatus_prepare_upgrade_apt_get () {
	archive_setstatus "$apt_get_ident.$os_id.$(apt-get --print-uris -y -qq upgrade)"
}
setstatus_prepare_install_apt_get() {
	archive_setstatus "$apt_get_ident.$os_id.$(apt-get --print-uris -y -qq install $@)"
}
install_file_apt_get() {
	dpkglist=""
	for i in $(cat $archive_dir/installorder_$os_id); do
		dpkglist="${dpkglist} $archive_dir/packages/$i"
	done
	dpkg -i $dpkglist
}

if [ -e $archive_dir/toinstall ]; then
	update_apt_get
	setstatus_prepare_install_apt_get $(cat $archive_dir/toinstall)
fi

if [ -e $archive_dir/upgrade ]; then
	update_apt_get
	setstatus_prepare_upgrade_apt_get
fi


if [ -d $archive_dir/packages ]; then
	if [ ! -e $archive_dir/installorder_$os_id ]; then
		echo "no installorder for this OS: $os_id"
		exit 1
	fi
	install_file_apt_get $archive_dir/installorder_$os_id
fi
