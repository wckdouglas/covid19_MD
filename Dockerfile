FROM continuumio/miniconda:latest

RUN apt-get update && \
    apt-get -y install gcc mono-mcs libz-dev && \
    rm -rf /var/lib/apt/lists/*

ENV PATH="/opt/conda/bin:$PATH"
RUN conda config --add channels conda-forge && \
    conda config --add channels defaults && \
    conda config --add channels anaconda && \
    conda config --set always_yes yes --set changeps1 no  

COPY . /opt/covid
RUN conda env create -f /opt/covid/environment.yml
RUN conda init bash
RUN conda activate covid

ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "covid","/opt/conda/bin/python", "/opt/covid/dashboard.py"]
CMD ["--help"]
