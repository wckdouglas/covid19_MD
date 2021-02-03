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
RUN conda install python=3.6 pandas geopandas=0.7.0 \
        beautifulsoup4 html5lib bokeh lxml \
        numpy requests tqdm pytest-cov libiconv

ENTRYPOINT ["/opt/conda/bin/python", "/opt/covid/dashboard.py"]
CMD ["--help"]
