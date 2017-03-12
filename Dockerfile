FROM continuumio/miniconda:4.1.11

ENV install_dir=/home/app

RUN apt-get update && apt-get install -y gcc rlwrap vim

ADD requirements.txt $install_dir/

RUN pip install --no-cache-dir -r $install_dir/requirements.txt

ADD . $install_dir/

WORKDIR $install_dir

EXPOSE 80

CMD uwsgi --socket :80 --manage-script-name --mount /=app:app