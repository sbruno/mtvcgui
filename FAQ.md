# Frequently asked questions #



## Troubles opening /dev/dsp - Cannot open demuxer. - Capturing audio using ALSA ##

Maybe mencoder is trying to capture the audio using oss, and your mencoder or kernel has no support for it. What you can do is to specify to use alsa.

You can do that specifying capturing using **ALSA** in the extra TV parameters tab.

You also need to specify the device. Generally **hw.0**

That will record from the first device.

To get a list of devices you may run:
`arecord -l`

## Recording from another video input ##

TV cards usually have many video inputs such as S-Video, RCA, or others. To record from one of these devices instead of the standard analog cable input, you must change the value of the "Input" edit box which is 0 by default. The value of the other inputs vary between cards, but usually may be 1, 2 or 3.

## Recording from another audio source ##

Currently there is no option to select another audio source, but you can specify it as an extra tv parameter.

For example, if your audio device is /dev/dsp1, in the second tab, in the last edit box of the tab, add:
`adevice=/dev/dsp1`


If you need to add more parameters, join them with a ":", for example:
`outfmt=yuy2:adevice=/dev/dsp1`



## I get a black and white image ##

Black and white image can be probably misconfiguration of the norm.

The program defaults to NTSC (normid=0).

You must adjust this value to the norm used in your country.

A tooltip with normid values will show up if you point over the normid scroll box.