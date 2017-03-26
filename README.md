# Installation

git clone https://github.com/narsi84/digilib.git .

sudo apt-get install apache2
sudo apt-get install vim

sudo pip3 install Django
sudo pip3 install djangorestframework
sudo pip3 install django-cors-headers
sudo pip3 install markdown
sudo pip3 install django-filter
sudo pip install --upgrade django-crispy-forms



# Setup
Make sure VNC server is running, "Preferences->Raspberry pi configuration->Interfaces->VNC->Enabled"

## Start services on boot
In /etc/rc.local, enter following lines above 

==========
LOG=/home/pi/startup.log
DJANGO_LOG=/home/pi/django.log

date > $LOG

echo "Starting apache" >> $LOG
sudo service apache2 start >> $LOG 2>&1

echo "Starting ssh" >> $LOG
sudo service ssh start

echo "Starting Django" >> $LOG
python3 /home/pi/digilib/manage.py runserver 0.0.0.0:8000 > $DJANGO_LOG 2>&1 &
==========

## Set up django
sudo ln -sf /home/pi/digilib/static /var/www/html/digilib

sudo reboot

You should now be able to access http://raspberrypi/digilib from within your home network
