FROM continuumio/anaconda3

ENV PYTHONUNBUFFERED 1

WORKDIR /usr/src/coopy

RUN apt-get update && apt-get install -y --no-install-recommends \
  net-tools \
  sudo \
  bzip2 \
  curl \
  gcc \
  git \
  python3-dev \
  vim \
  && \
  apt-get clean && \
  pip install --upgrade pip && \
  pip install django-pure-pagination gunicorn && \
  conda update -n base conda && \
  conda install anaconda && \
  conda update --all && \
  conda clean --all -y && \
  conda install -c conda-forge nodejs=10.13.0 && \
  conda install -c anaconda django && \
  conda install -c conda-forge django-environ && \
  conda install -c conda-forge django-heroku && \
  conda install -c conda-forge dj-static && \
  conda install -c conda-forge whitenoise && \
  conda install -c conda-forge dj-database-url

ENV DJANGO_ENV production

COPY . .
RUN python manage.py collectstatic --noinput
MAINTAINER admin

ENV USER admin


RUN useradd -m ${USER}
RUN gpasswd -a ${USER} sudo
RUN echo "${USER}:test_pass" | chpasswd
USER ${USER}

CMD gunicorn -b 0.0.0.0:$PORT coopy.wsgi
