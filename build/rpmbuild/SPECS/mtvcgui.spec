Name:		mtvcgui
Version:	1.0
Release:	1%{?dist}
Summary:	A simple GUI for recording TV with mencoder

Group:		Applications/TV
License:	GPLv3
URL:		http://code.google.com/p/mtvcgui/
Source:		http://mtvcgui.googlecode.com/files/%{name}-%{version}.tgz	
BuildRoot:	%(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)

#BuildRequires:	
Requires:	PyQt4
Requires:	mencoder
Requires:	mplayer

%description
This GUI allows the user to capture TV using mencoder. Set different parameters from the UI to generate the mencoder command and execute it or display it.

%prep
%setup -q

%build


%install
rm -rf $RPM_BUILD_ROOT
DESTDIR=$RPM_BUILD_ROOT
echo "DESTDIR=$DESTDIR"
LIBDIR=$DESTDIR/opt/mtvcgui
ICODIR=$DESTDIR/usr/share/icons/hicolor
BINDIR=$DESTDIR/usr/bin
APPNAME=%{name}-%{version}
mkdir -p $LIBDIR
mkdir -p $BINDIR
mkdir -p $ICODIR
mkdir -p $DESTDIR/usr/share/pixmaps
cp ui/icons/128x128/mtvcgui.png $DESTDIR/usr/share/pixmaps
mkdir -p $ICODIR/scalable/apps
cp ui/icons/mtvcgui.svg $ICODIR/scalable/apps
mkdir -p $DESTDIR/usr/share/applications
cp mtvcgui.desktop $DESTDIR/usr/share/applications
mkdir -p $ICODIR/16x16/apps
cp ui/icons/16x16/mtvcgui.png $ICODIR/16x16/apps
mkdir -p $ICODIR/22x22/apps
cp ui/icons/22x22/mtvcgui.png $ICODIR/22x22/apps
mkdir -p $ICODIR/32x32/apps
cp ui/icons/32x32/mtvcgui.png $ICODIR/32x32/apps
mkdir -p $ICODIR/48x48/apps
cp ui/icons/48x48/mtvcgui.png $ICODIR/48x48/apps
mkdir -p $ICODIR/64x64/apps
cp ui/icons/64x64/mtvcgui.png $ICODIR/64x64/apps
mkdir -p $ICODIR/128x128/apps
cp ui/icons/128x128/mtvcgui.png $ICODIR/128x128/apps
cp -r * $LIBDIR/
ln -fs ../../opt/mtvcgui/run.py $BINDIR/mtvcgui

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%doc
/opt/mtvcgui/*
/usr/bin/mtvcgui
/usr/share/applications/mtvcgui.desktop
/usr/share/icons/hicolor/16x16/apps/mtvcgui.png
/usr/share/icons/hicolor/22x22/apps/mtvcgui.png
/usr/share/icons/hicolor/32x32/apps/mtvcgui.png
/usr/share/icons/hicolor/48x48/apps/mtvcgui.png
/usr/share/icons/hicolor/64x64/apps/mtvcgui.png
/usr/share/icons/hicolor/128x128/apps/mtvcgui.png
/usr/share/icons/hicolor/scalable/apps/mtvcgui.svg
/usr/share/pixmaps/mtvcgui.png

%changelog

