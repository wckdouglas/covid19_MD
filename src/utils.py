import pandas as pd
<<<<<<< HEAD
import geopandas as gpd
=======
>>>>>>> 860ea881f47a828b8cb4b8fca8356c1f34ff2575
import glob
import os

class Data():
    def __init__(self, state = 'MD'):
        #data and URL path
<<<<<<< HEAD
        self.state = state
=======
>>>>>>> 860ea881f47a828b8cb4b8fca8356c1f34ff2575
        self.data_path = 'data/'
        self.zip_map_url = 'https://public.opendatasoft.com/explore/dataset/us-zip-code-latitude-and-longitude'\
                '/download/?format=csv&timezone=America/New_York'\
                '&lang=en&use_labels_for_header=true&csv_separator=%3B'
<<<<<<< HEAD
        #geo shape: https://catalog.data.gov/dataset/tiger-line-shapefile-2016-2010-nation-u-s-2010-census-5-digit-zip-code-tabulation-area-zcta5-na

        #actual reading dat
        self.geo = self.read_map()
        self.zip_map = self.read_zip_map()
        self.zip_codes = self.zip_map.Zip
        self.zip_covid = self.read_zip_COVID()
        
    def read_map(self):
        return gpd.read_file('{}/tl_2016_us_zcta510.shp'.format(self.data_path)) \
            .rename(columns = {'ZCTA5CE10':'Zip'}) \
            .assign(Zip = lambda d: d.Zip.astype(int))
        
=======
        self.zip_census = 'https://data.lacity.org/api/views/nxs9-385f/rows.csv?accessType=DOWNLOAD'

        #actual reading dat
        self.zip_map = self.read_zip_map()
        self.zip_codes = self.zip_map.Zip
        self.zip_covid = self.read_zip_COVID()
        self.zip_census = self.read_zip_stat()
>>>>>>> 860ea881f47a828b8cb4b8fca8356c1f34ff2575

    def read_zip_COVID(self):
        covid_data = {}
        for csv in glob.glob(self.data_path + '/*csv'):
            date = os.path.basename(csv.replace('.csv',''))
            covid_data[date] = pd.read_csv(csv, names = ['Zip','Cases']) \
                .assign(Cases = lambda d: d.Cases.str.replace(' Cases','').astype(int))

        return pd.concat(date_data.assign(Date = date) for date, date_data in covid_data.items()) \
            .assign(Date = lambda d: pd.to_datetime(d.Date, format = '%Y-%m-%d'))


    def read_zip_map(self):
        return pd.read_csv(self.zip_map_url, sep=';') \
            .query('State == "%s"' %self.state)

<<<<<<< HEAD
=======

    def read_zip_stat(self):
        return pd.read_csv(self.zip_census) \
            .rename(columns = {'Zip Code':'Zip'}) \
            .pipe(lambda d: d[d.Zip.isin(self.zip_codes)])
>>>>>>> 860ea881f47a828b8cb4b8fca8356c1f34ff2575
