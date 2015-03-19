# mtvcgui #

## Description ##
**mtvcgui** is a very simple graphical user interface for TV capture using the _mplayer_ encoder (_mencoder_) written in python with _qt4_ libraries, using _qtdesigner_ and _PyQt4_

It allows the user to specify various parameters for the mencoder command line utility using separate widgets, but non covered parameters can still be supplied as extra parameters.

## Installation ##
Provided that you have installed all the dependencies (Python, PyQt4, mplayer and mencoder) you just need to download the .tgz file, extract it into some folder with the command tar zxvf filename.tgz then move to the created folder and execute ./run.py

There are also some other methods of installation for some Linux distributions. In the Downloads section you may find a .rpm file for installation in Red Hat based distributions a .deb file for installation in Debian based distributions like Ubuntu, and a .ebuild file for Gentoo. However these are just tests I made. I have no experience in packaging. If you want to be a maintainer just contact me, that would be a very good help.

## Configuration ##
It has almost no default values. The chosen configuration from the GUI can be
saved at any time to the **mtvcgui.ini** file, which will be stored in the directory
.mtvcgui in the users home directory.
A mtvcgui.ini.sample is provided, with the values I used to test it. It shows
how to add extra parameters for deinterlacing, for example. If you want to user
it, you need to rename it as mtvcgui.ini, change the norm value to the one
corresponding to your country and save it in $HOME/.mtvcgui/mtvcgui.ini

You may get good results with audio codec mp3lame and video codec lavc with the default lavc options.

See README for more info.


## Dependencies ##
PyQt4

## FAQ ##
[FAQ page](http://code.google.com/p/mtvcgui/wiki/FAQ)


## Screenshots ##

![http://bananabruno.googlepages.com/mtvcgui1.png](http://bananabruno.googlepages.com/mtvcgui1.png)

![http://bananabruno.googlepages.com/mtvcgui2.png](http://bananabruno.googlepages.com/mtvcgui2.png)

![http://bananabruno.googlepages.com/mtvcgui3.png](http://bananabruno.googlepages.com/mtvcgui3.png)

![http://bananabruno.googlepages.com/mtvcgui4.png](http://bananabruno.googlepages.com/mtvcgui4.png)