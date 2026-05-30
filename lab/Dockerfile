FROM jupyter/scipy-notebook:latest

USER jovyan
WORKDIR /home/jovyan/work

ENV JUPYTER_TOKEN=""

CMD ["start-notebook.sh", "--NotebookApp.token=''", "--NotebookApp.password=''", "--NotebookApp.allow_origin='*'"]
