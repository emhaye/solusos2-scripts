SolusOS/Anka Scripts
====================

Currently this repository contains very simple scripts designed to
bootstrap a Pardus environment (and soon Anka/SolusOS 2 bases) to
create and build the initial toolchains, and to enable us to
run "buildfarm" in a chroot'ed environment.

pisistrap
---------
Currently under development. This script simply downloads and extracts
a set of packages and dependencies into a "work" directory.

i.e.:
./pisistrap.py

First run downloads the pisi-index.xml.xz and extracts it. On the second
run it will attempt to download and extract all the required base packages
and dependencies for a working system. Once this is done:

    sudo chroot work/
    pisi install --ignore-comar *.pisi
    rm -f *.pisi
    service dbus start
    pisi configure-pending

This is enough to have a base system to build packages from. It is recommended
to add your distribution repository if possible. 
