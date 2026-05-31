FROM jupyter/scipy-notebook:latest

USER root
RUN fix-permissions /home/jovyan

USER jovyan
WORKDIR /home/jovyan/work

CMD ["start-notebook.sh", "--ServerApp.allow_origin=*"]
