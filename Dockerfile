FROM php:5-apache

ENV DEBIAN_FRONTEND noninteractive

# install packages
RUN apt-get update
RUN apt-get upgrade
RUN apt-get install -y --no-install-recommends python2.7 pdftk inkscape python-pip python-reportlab python-repoze.lru php5-json python-lxml locales python-pil
RUN pip install oerplib
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
