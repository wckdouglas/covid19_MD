FROM continuumio/miniconda3:latest

RUN apt-get update && \
    apt-get -y install gcc mono-mcs libz-dev && \
    rm -rf /var/lib/apt/lists/*

ENV PATH="/opt/conda/bin:$PATH"
RUN conda config --add channels conda-forge && \
    conda config --add channels defaults && \
    conda config --add channels anaconda && \
    conda config --set always_yes yes --set changeps1 no && \
    conda install -c conda-forge mamba && \
    mamba install python=3.6 pandas \
        beautifulsoup4 html5lib bokeh lxml \
        numpy requests tqdm pytest-cov libiconv && \
    pip install geopandas==0.7.0

COPY . /opt/covid

ENTRYPOINT ["/opt/conda/bin/python", "/opt/covid/dashboard.py"]
CMD ["--help"]
