# Copyright 1999-2007 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

inherit eutils autotools

DESCRIPTION="Mencoder TV Capture GUI"
HOMEPAGE="http://code.google.com/p/mtvcgui"
SRC_URI="http://mtvcgui.googlecode.com/files/${PN}-${PV}.tgz"

LICENSE="GPL-3"
SLOT="0"
KEYWORDS="amd64 x86"

RDEPEND="dev-python/PyQt4
	media-video/mplayer"

DEPEND="${RDEPEND}"

src_unpack() {
	unpack ${A}
}

src_compile() { :; }

src_install() {
	cd ${S}
	insinto /opt/mtvcgui
	doins *
	exeinto /opt/mtvcgui
	doexe run.py
	insinto /opt/mtvcgui/i18n
	doins i18n/*
	insinto /opt/mtvcgui/ui
	doins ui/*

	# Install a symlink /usr/bin/mtvcgui
	dodir /usr/bin
	dosym /opt/mtvcgui/run.py /usr/bin/mtvcgui

	# Install icon and .desktop for menu entry
	insinto /usr/share/pixmaps
	doins ${S}/ui/icons/128x128/mtvcgui.png

	for res in 16 22 32 48 64 128; do
		insinto /usr/share/icons/hicolor/${res}x${res}/apps
		doins ${S}/ui/icons/${res}x${res}/mtvcgui.png
	done

	insinto /usr/share/icons/hicolor/scalable/apps
	doins ${S}/ui/icons/mtvcgui.svg
	insinto /usr/share/applications
	doins ${S}/mtvcgui.desktop

}

pkg_postinst() {
	elog "Custom mtvcgui configuration will be saved in ~/.mtvcgui/mtvcgui.ini"
	echo
}
