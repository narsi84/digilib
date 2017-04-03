# Installation
```
git clone https://github.com/narsi84/digilib.git digilib

sudo apt-get install apache2
sudo apt-get install vim
sudo apt-get install python-cffi
sudo apt-get install libffi-dev


sudo pip3 install Django
sudo pip3 install djangorestframework
sudo pip3 install django-cors-headers
sudo pip3 install markdown
sudo pip3 install django-filter
sudo pip3 install --upgrade django-crispy-forms
sudo pip3 install -U pyOpenSSL
sudo pip3 install service_identity
```


# Setup
Make sure VNC server is running, "Preferences->Raspberry pi configuration->Interfaces->VNC->Enabled"

## Start services on boot
In /etc/rc.local, enter following lines above 'exit 0'
```
LOG=/home/pi/startup.log
DJANGO_LOG=/home/pi/django.log

date > $LOG

echo "Starting apache" >> $LOG
sudo service apache2 start >> $LOG 2>&1

echo "Starting ssh" >> $LOG
sudo service ssh start
```

Since we are running with virtualenv, it cannot be loaded by boot. In /home/pi/.bashrc, add these lines at the end
```
echo "Starting Django" >> ~/startup.log
source ~/venv/bin/activate
~/digilib/manage.py runserver 0.0.0.0:8000 > ~/django.log 2>&1 &
```

## Set up django
```
sudo ln -sf /home/pi/digilib/static /var/www/html/digilib
sudo mkdir /var/www/html/imgs
sudo chown pi /var/www/html/imgs

sudo mkdir /var/www/html/test
sudo chown pi /var/www/html/test
```

## Set up opencv
Follow instructions in http://www.pyimagesearch.com/2016/04/18/install-guide-raspberry-pi-3-raspbian-jessie-opencv-3/ to install opencv

```
sudo reboot
```
You should now be able to access http://raspberrypi/digilib from within your home network
