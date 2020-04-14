import pandas as pd
import geopandas as gpd
import glob
import os

class Data():
    def __init__(self, state = 'MD'):
        #data and URL path
        self.state = state
        self.data_path = 'data/'
        self.zip_map_url = 'https://public.opendatasoft.com/explore/dataset/us-zip-code-latitude-and-longitude'\
                '/download/?format=csv&timezone=America/New_York'\
                '&lang=en&use_labels_for_header=true&csv_separator=%3B'
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

