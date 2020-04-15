import pandas as pd
import geopandas as gpd
import glob
import os
from bs4 import BeautifulSoup
import requests

class Data():
    def __init__(self, state = 'MD'):
        #data and URL path
        self.state = state
        self.data_path = 'data/'
        self.zip_map_url = 'https://public.opendatasoft.com/explore/dataset/us-zip-code-latitude-and-longitude'\
                '/download/?format=csv&timezone=America/New_York'\
                '&lang=en&use_labels_for_header=true&csv_separator=%3B'
        self.population_url = 'https://www.maryland-demographics.com/zip_codes_by_population'

        #actual reading dat
        self.geo = self.read_map()
        self.zip_map = self.read_zip_map()
        self.zip_codes = self.zip_map.Zip
        self.zip_covid = self.read_zip_COVID()
        self.zip_population = self.read_population()
        
    def read_map(self):
        #geo shape: https://catalog.data.gov/dataset/tiger-line-shapefile-2016-2010-nation-u-s-2010-census-5-digit-zip-code-tabulation-area-zcta5-na
        return gpd.read_file('zip://{}/tl_2019_us_zcta510.zip'.format(self.data_path)) \
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

    def read_population(self):
        http = requests.get(self.population_url)
        soup = BeautifulSoup(http.content)
        table = soup.find_all('table')
        table = pd.read_html(str(table))[0] \
            .filter(['Zip Code','Population'])\
            .rename(columns = {'Zip Code':'Zip'})\
            .iloc[:-1,:]
        rows = []
        for i, row in table.iterrows():
            row_dict = {}
            if 'and' not in row['Zip']:
                row_dict['Zip'] = row['Zip']
                row_dict['Population'] = row['Population']
            else:
                for zip_code in row['Zip'].split(' and '):
                    row_dict['Zip'] = zip_code
                    row_dict['Population'] = int(row['Population'])/2
            rows.append(row_dict)
        return pd.DataFrame(rows)