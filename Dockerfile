FROM continuumio/miniconda3:4.5.4

ENV install_dir=/home/app

# RUN apt-get update && apt-get install -y gcc rlwrap vim

RUN conda install -c conda-forge -y pywavelets uwsgi

ADD requirements.txt $install_dir/

RUN pip install -r $install_dir/requirements.txt

ADD ./yyy $install_dir/

WORKDIR $install_dir

EXPOSE 80

CMD uwsgi --socket :80 --manage-script-name --mount /=app:app