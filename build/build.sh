#!/bin/bash

if [ -z ${1} ]; then
    echo "Must provide version as first argument"
    exit 1;
fi

mkdir ~/archlinux
rm -rf ~/archlinux/${1}
mkdir ~/archlinux/${1}
cp archlinux/PKGBUILD ~/archlinux/${1}

rm -rf ~/rpmbuild
cp -r rpmbuild ~
sed -i "s/FIELD_FOR_VERSION/${1}/g" ~/rpmbuild/SPECS/mtvcgui.spec
cd ~/rpmbuild/SOURCES
svn export /mnt/data/santiago/svn/mtvcgui/src mtvcgui-${1}
tar zcvf mtvcgui-${1}.tgz mtvcgui-${1}
rm -rf mtvcgui-${1}
cd ~/rpmbuild/SPECS
rpmbuild -bb --target noarch mtvcgui.spec
cd ~/rpmbuild/RPMS/noarch
sudo alien -d mtvcgui-${1}*

cd ~/archlinux/${1}
sed -i "s/FIELD_FOR_VERSION/${1}/g" PKGBUILD 
sed -i "s/md5sums=()/$(echo $(makepkg -g))/g" PKGBUILD
makepkg -d --source
 
