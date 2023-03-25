FROM ubuntu:22.04

ENV DEBIAN_FRONTEND noninteractive

# install packages
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends apache2 libapache2-mod-php php-json locales \
    python3 qpdf inkscape python3-pip python3-repoze.lru python3-lxml python3-pil python3-argcomplete python3-setuptools gsfonts python3-requests python3-reportlab cups-bsd fonts-roboto
RUN a2enmod php8.1

# RUN apt-get install -y python3-dev build-essential
RUN pip3 install python-barcode
# configure
RUN ["rm", "-r", "/var/www/html/"]
RUN ["sed", "-i", "s/\\/var\\/www\\/html/\\/var\\/www\\/public/", "/etc/apache2/sites-available/000-default.conf"]
RUN ["sed", "-i", "s/\\/var\\/www\\/html/\\/var\\/www\\/public/", "/etc/apache2/apache2.conf"]


COPY . /var/www/

# configure locales
#RUN ["/var/www/configure_locales.sh"]
# fix permissions
RUN ["chown", "-R", "www-data:www-data", "/var/www/"]
CMD ["apache2ctl", "-D", "FOREGROUND"]
