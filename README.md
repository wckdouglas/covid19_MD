# Maryland zip-code level COVID19 cases #

[![poetry CI](https://github.com/wckdouglas/covid19_MD/actions/workflows/poetry_CI.yml/badge.svg)](https://github.com/wckdouglas/covid19_MD/actions/workflows/poetry_CI.yml)[![miniconda CI](https://github.com/wckdouglas/covid19_MD/actions/workflows/miniconda_CI.yml/badge.svg)](https://github.com/wckdouglas/covid19_MD/actions/workflows/miniconda_CI.yml)[![codecov](https://codecov.io/gh/wckdouglas/covid19_MD/branch/master/graph/badge.svg)](https://codecov.io/gh/wckdouglas/covid19_MD)[![Docker Pulls](https://img.shields.io/docker/pulls/wckdouglas/md_covid19)](https://hub.docker.com/repository/docker/wckdouglas/md_covid19)


Maryland government is releasing daily zip-code level data since 4/12. I copy and save the data everyday in this [github repo](https://github.com/wckdouglas/covid19_MD/tree/master/data), feel free to use these data!

The different data sources used in this project are:

1. Maryland COVID19 cases ([Data source](https://coronavirus.maryland.gov/))
2. Zip code geographic shape data from Census ([Data source](https://www2.census.gov/geo/tiger/TIGER2019/ZCTA5/tl_2019_us_zcta510.zip))
3. Population data ([Data source](https://www.maryland-demographics.com/zip_codes_by_population))
4. Zip code and City information ([Data source](https://public.opendatasoft.com/explore/dataset/us-zip-code-latitude-and-longitude/table/))
5. Cases by Zip code: [MD opendata](https://coronavirus.maryland.gov/datasets/md-covid-19-cases-by-zip-code/geoservice)) or [./data](https://github.com/wckdouglas/covid19_MD/tree/master/data), I'm experimenting to see if the MD opendata is updated promptly after the updating [MD COVID19 dashboard](https://coronavirus.maryland.gov/).


To build the dashboard, do:

```
python dashboard.py update --use-db #using MD opendata
```

or

```
python dashboard.py update #using data collected from MD gov website
```

both of the commands will generate a html file: ```dashboard.html```

## Docker ##

The code can be run as docker image:

```
git clone git@github.com:wckdouglas/covid19_MD.git
cd covid19_MD
docker pull wckdouglas/md_covid19
docker run -v "$(pwd):/data" md_covid19 update -o /data/dashboard.html
```



## Poetry ##

```
pip install poetry
git clone git@github.com:wckdouglas/covid19_MD.git
cd covid_MD
poetry install
poetry run python dashboard.py update -o /data/dashboard.html
