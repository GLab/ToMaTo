#!/bin/bash
#
# modes.
#  assumption: only one mode file.
#  the modes are: prepare-install, prepare-upgrade, install
#  mode is selected by presence of mode file. filenames:
#   toinstall - prepare-install; file contains whitespace-seperated packet list
#   upgrade - prepare-upgrade; content does not matter.
#   installorder - install; packet filenames in installation order. linebreak-seperated
#
# identifiers
apt_get_ident="aptget"



# handlers for apt-get
need_apt_get () {
	if which apt-get; then
		return 0;
	else
		return 1;
	fi
}

update_apt_get () {
	apt-get update
}
setstatus_prepare_upgrade_apt_get () {
	archive_setstatus "$apt_get_ident.$(apt-get --print-uris -y -qq upgrade)"
}
setstatus_prepare_install_apt_get() {
	archive_setstatus "$apt_get_ident.$(apt-get --print-uris -y -qq install $@)"
}
install_file_apt_get() {
	dpkg -i $1
}



echo "TODO: find out which packet manager."

if [ -e $archive_dir/toinstall ]; then
	update_apt_get
	setstatus_prepare_install_apt_get $(cat $archive_dir/toinstall)
fi

if [ -e $archive_dir/upgrade ]; then
	update_apt_get
	setstatus_prepare_upgrade_apt_get
fi

if [ -e $archive_dir/installorder ]; then
	for i in $(cat $archive_dir/installorder); do
		install_file_apt_get $archive_dir/packages/$i
	done
fi
