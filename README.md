Installation notes
-----

Several environment variable are used for configuration/running. Please set
the following in your ~/.bashrc (or wherever else is appropriate):

```bash
export PCAM_USER="camera login user name"
export PCAM_PASSWORD="camera login password"
export PCAM_NAS_USER="ftp server user"
export PCAM_NAS_PASSWORD="ftp server password"
```

# Data

- snapshots:
  - full res (~0.7 MB per image)
  - 1 every 10 seconods
  - save detection results
- short videos
  - 5 fps
  - 1 sec pre-record
  - trigger processed 1/sec
  - max length?
  - max duty cycle?


## Format

- partitions:
  - per group (separate storage: mac address?)
  - camera (ip or mac address?)
  - time (requires RTC per group, to second)
- types
  - detection results: npy
  - snapshots: jpg
  - videos: mp4


# System architecture

- hardware:
  - Coral Dev board (in enclosure)
    - connected storage
    - power supply
    - interface?
  - Security cameras
    - POE
    - ethernet feedthroughs

- nodes: 
  - tensorflow processor
  - (N) grabbers
  - FTP server


# Camera setup

- Adjust lens to correct focus
- One time setup
  - user/password
  - extraformat h265
  - extraformat bitrate
  - extraformat dimensions
  - extraformat fps
  - mainformat h265
  - mainformat bitrate
  - mainformat dimensions
  - mainformat fps
  - disable motion detection
  - remove videowidget overlays
  - enable ftp settings
  - snapshot schedule
  - snapshot saving
  - snapshot period


# Failure modes

- Camera dies
- Main node dies (loss of data)
- Stream disconnects
  - gstreamer drops
  - substream drops
- out of storage
- TPU hangs
- TPU disconnects
- Grabber disconnects from main node (sharedmem failure)
- Saving video fails

Installation notes
-----

# Install OS

Install latest Pi OS (Desktop: tested March 2020)
Setup locale, timezone, keyboard, hostname, ssh

# Environment variables

Several environment variable are used for configuration/running. Please set
the following in your ~/.bashrc (or wherever else is appropriate):

```bash
export PCAM_USER="camera login user name"
export PCAM_PASSWORD="camera login password"
export PCAM_NAS_USER="ftp server user"
export PCAM_NAS_PASSWORD="ftp server password"
```

# Clone this repository

Prepare for and clone this repository
```bash
mkdir -p ~/r/cbs-ntcore
cd ~/r/cbs-ntcore
git clone https://github.com/cbs-ntcore/pollinatorcam.git
```

# Install pre-requisites

```bash
sudo apt install python3-numpy python3-opencv python3-requests python3-flask python3-systemd nginx-full vsftpd virtualenvwrapper apache2-utils python3-gst-1.0 gstreamer1.0-tools nmap
```

# Setup virtualenv

```bash
mkvirtualenv --system-site-packages pollinatorcam -p `which python3`
activate pollinatorcam
echo "mkvirtualenv --system-site-packages pollinatorcam -p `which python3`" >> ~/.bashrc
```

# Install tfliteserve

```bash
mkdir -p ~/r/braingram
cd ~/r/braingram
git clone https://github.com/braingram/tfliteserve.git
cd tfliteserve
pip3 install https://dl.google.com/coral/python/tflite_runtime-2.1.0.post1-cp37-cp37m-linux_armv7l.whl
pip3 install -e .
# get model (TODO 404 permission denied, host this in repo or publicly)
wget https://github.com/cbs-ntcore/pollinatorcam/releases/download/v0.1/200123_2035_model.tar.xz
tar xvJf 200123_2035_model.tar.xz
```

# Install this repository

```bash
cd ~/r/cbs-ntcore/pollinatorcam
pip install -e .
pip install uwsgi
```

# Setup storage location

This assumes you're using an external storage drive that shows up as /dev/sda1

```bash
echo "/dev/sda1 /mnt/data auto defaults,user,uid=1000,gid=117,umask=002  0 0" | sudo tee -a /etc/fstab
```

# Setup FTP server

```bash
echo "
write_enable=YES
local_umask=011
local_root=/mnt/data" | sudo tee -a /etc/vsftpd.conf

sudo adduser $PCAM_NAS_USER
sudo adduser $PCAM_NAS_USER ftp
sudo passwd $PCAM_NAS_USER $PCAM_NAS_PASSWORD
sudo mkdir /mnt/data
sudo chgrp ftp /mnt/data
sudo chown pi /mnt/data
sudo chmod 755 /mnt/data
```

# Setup web server (for UI)

```bash
sudo htpasswd -c /etc/apache2/.htpasswd pcam $PCAM_PASSWORD
sudo rm /etc/nginx/sites-enabled/default
sudo ln -s ~/r/cbs-ntcore/pollinatorcam/services/pcam-ui.nginx /etc/nginx/sites-enabled/
```

TODO Setup uwsgi... (anything to do?)
TODO Setup gstreamer... (anything to do?)

# Setup systemd services

```bash
cd ~/r/cbs-ntcore/pollinatorcam/services
for S in 
    tfliteserve.service
    pcam-discover.service
    pcam-overview.service
    pcam-overview.timer
    pcam@.service
    pcam-ui.service; do
  sudo ln -s ~/r/cbs-ntcore/pollinatorcam/services/$S /etc/systemd/system/$S
done
# enable services to run on boot
for S in
    tfliteserve.service
    pcam-discover.service
    pcam-overview.timer
    pcam-ui.service; do
  sudo systemctl enable $S
done
# start services
for S in
    tfliteserve.service
    pcam-discover.service
    pcam-ui.service; do
  sudo systemctl start $S
done
sudo systemctl restart nginx
```
