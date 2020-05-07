import pandas as pd
import geopandas as gpd
import glob
import os
from bs4 import BeautifulSoup
import requests
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Data collector')

class Data():
    def __init__(self, state = 'MD'):
        #data and URL path
        self.state = state
        self.data_path = 'data/'
        self.zip_map_url = 'https://public.opendatasoft.com/explore/dataset/us-zip-code-latitude-and-longitude'\
                '/download/?format=csv&timezone=America/New_York'\
                '&lang=en&use_labels_for_header=true&csv_separator=%3B'
        self.population_url = 'https://www.maryland-demographics.com/zip_codes_by_population'
        self.geo_shape_url = 'https://www2.census.gov/geo/tiger/TIGER2019/ZCTA5/tl_2019_us_zcta510.zip'

        #actual reading dat
        self.geo = self.read_map()
        self.zip_map = self.read_zip_map()
        self.zip_codes = self.zip_map.Zip
        self.zip_covid = self.read_zip_COVID()
        self.zip_population = self.read_population()
        
    def download_zipfile(self, zipfile):
        with open(zipfile, 'wb') as out:
            downloaded = requests.get(self.geo_shape_url)
            out.write(downloaded.content)
        logger.info('Downloaded %s' %zipfile)
        os.system('unzip %s' %zipfile)
        logger.info('unzipped %s' %zipfile)

        
    def read_map(self):
        zipfile = self.data_path + '/tl_2019_us_zcta510.zip'
        shapefile = zipfile.replace('.zip','.shp')
        if not os.path.isfile(shapefile):
            self.download_zipfile(zipfile)
        #out = gpd.read_file('zip://' + zipfile) \
        out = gpd.read_file(shapefile) \
            .rename(columns = {'ZCTA5CE10':'Zip'}) \
            .assign(Zip = lambda d: d.Zip.astype(int))
        logger.info('Loaded geo shape')
        return out

    def read_zip_COVID(self):
        covid_data = {}
        for i, csv in enumerate(glob.glob(self.data_path + '/*.csv')):
            date = os.path.basename(csv.replace('.csv',''))
            covid_data[date] = pd.read_csv(csv, names = ['Zip','Cases']) \
                .assign(Cases = lambda d: d.Cases.str.replace(' Cases','').astype(int))
        logger.info('Loaded daily COVID cases (%i days)' %(i+1))
        return pd.concat(date_data.assign(Date = date) for date, date_data in covid_data.items()) \
            .assign(Date = lambda d: pd.to_datetime(d.Date, format = '%Y-%m-%d'))


    def read_zip_map(self):
        out =  pd.read_csv(self.zip_map_url, sep=';') \
            .query('State == "%s"' %self.state)
        logger.info('Retrieved map info')
        return out

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
        logger.info('Retrieved populations')
        return pd.DataFrame(rows)
    
    
    
def markdown_html(html_file, out_file):
    with open(html_file) as html,\
            open(out_file, 'w') as out_html:
        out = 1
        outline = 0
        inline = 0
        for line in html:
            inline += 1
            if not '<!DOCTYPE html>' in line.strip():
                outline += 1
                print(line.strip(), file = out_html)
    logger.info('Written %i lines from %i lines to %s' %(outline, inline, out_file))
