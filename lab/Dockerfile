FROM jupyter/scipy-notebook:latest

USER root

CMD ["bash", "-c", "chown -R jovyan:users /home/jovyan/work && exec start-notebook.sh --ServerApp.allow_origin=*"]
