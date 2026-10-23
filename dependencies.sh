#!/bin/sh
set -eu

apt-get update
apt-get install -y --no-install-recommends \
	ca-certificates \
	cpanminus \
	curl \
	git \
	libconfig-properties-perl \
	libjson-perl \
	libparams-validate-perl \
	libproc-background-perl \
	make \
	perl

cpanm --notest Config::Properties::Simple

git clone --depth 1 https://github.com/web-cat/web-cat-subsystem-PerlForPlugins.git /tmp/PerlForPlugins
mkdir -p /usr/local/lib/site_perl
cp -R /tmp/PerlForPlugins/Resources/lib/. /usr/local/lib/site_perl/
rm -rf /tmp/PerlForPlugins

curl -fsSL -o /tmp/miniforge.sh \
	"https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-$(uname -m).sh"
bash /tmp/miniforge.sh -b -p /opt/conda
rm /tmp/miniforge.sh
/opt/conda/bin/conda create -y -n plugin python=3.8 nbconvert pillow
/opt/conda/bin/conda clean -afy

apt-get purge -y --auto-remove cpanminus curl git make
rm -rf /var/lib/apt/lists/* /root/.cpanm
