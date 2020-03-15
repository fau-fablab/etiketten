FROM ubuntu:18.04

ENV DEBIAN_FRONTEND noninteractive

# install packages
RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install -y --no-install-recommends apache2 libapache2-mod-php7.2 php7.2-json locales \
        python2.7 qpdf inkscape python-pip python-reportlab python-repoze.lru python-lxml python-pil python-argcomplete python-setuptools gsfonts
RUN a2enmod php7.2
RUN pip install oerplib
# necessary???:
RUN pip install argcomplete

# configure
RUN ["rm", "-r", "/var/www/html/"]
RUN ["sed", "-i", "s/\\/var\\/www\\/html/\\/var\\/www\\/public/", "/etc/apache2/sites-available/000-default.conf"]
RUN ["sed", "-i", "s/\\/var\\/www\\/html/\\/var\\/www\\/public/", "/etc/apache2/apache2.conf"]

COPY . /var/www/

# configure locales
RUN ["/var/www/configure_locales.sh"]
# fix permissions
RUN ["chown", "-R", "www-data:www-data", "/var/www/"]
CMD apache2ctl -D FOREGROUND
