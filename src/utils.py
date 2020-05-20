import glob
import os
import requests
import logging
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import geopandas as gpd
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
        os.system('unzip  %s -d data' %zipfile)
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
        for i, csv in enumerate(glob.glob(self.data_path + '/*.tsv')):
            date = os.path.basename(csv.replace('.tsv',''))
            covid_data[date] = pd.read_csv(csv, names = ['Zip','Cases'],sep='\t') \
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


def get_data(ts_data_file = '../data/ts.csv', map_data_file = '../data/MD.geojson'):
    maryland = Data(state='MD')
    data = maryland.geo\
        .merge(maryland.zip_map, on ='Zip', how = 'right')\
        .merge(maryland.zip_covid, on ='Zip', how ='left')\
        .merge(maryland.zip_population.assign(Zip = lambda d: d.Zip.astype(int)), on ='Zip') \
        .assign(Date = lambda d: d.Date.fillna(d.Date.max())) \
        .filter(['Zip','City','State','Cases','Date','geometry', 'Population']) 

    total_case_data = data \
        .pipe(lambda d: d[d.Date==d.Date.max()]) \
        .assign(Cases = lambda d: d.Cases.fillna(0)) \
        .pipe(lambda d: d[~pd.isnull(d.geometry)]) \
        .assign(per_population = lambda d: d.Cases / d.Population.astype(int) * 1e6)
    today = str(total_case_data.Date.astype(str).unique()[0])

    per_day_increase_data =  data \
        .groupby(['Zip'], as_index=False)\
        .apply(lambda d: d.nlargest(2, 'Date') \
                        .assign(increase = lambda d: d.Cases.max() - d.Cases.min()) \
                        .assign(increase = lambda d: np.where(pd.isnull(d.increase), d.Cases, d.increase))\
                        .assign(increase = lambda d: d.increase.fillna(0))\
                        .pipe(lambda d: d[d.Date == d.Date.max()])) \
        .pipe(lambda d: d[~pd.isnull(d.geometry)]) \
        .assign(per_population = lambda d: d.increase / d.Population.astype(int) * 1e6) \
        .assign(Date = lambda d: d.Date.astype(str))

    ts_data = maryland.zip_covid\
        .merge(maryland.zip_map.filter(['Zip','City']), on = 'Zip') \
        .groupby(['Zip','City'], as_index=False)\
        .apply(lambda d: d.sort_values('Date')  \
        .assign(Cases = lambda d: d.Cases.fillna(method='ffill', axis=0)\
        .fillna(0))) \
        .reset_index(drop=True) \
        .assign(formatted_date = lambda d: d.Date.astype(str)) 
    ts_data.to_csv(ts_data_file, index=False)
    logger.info('Written %s' %ts_data_file)

    map_df = total_case_data\
        .merge(per_day_increase_data.filter(['Zip','increase']))\
        .assign(per_population_increase = lambda d: 1e6*d['increase'].astype(int)/d.Population.astype(int))
    map_df.to_file(map_data_file, driver='GeoJSON')
    logger.info('Written %s' %map_data_file)


if __name__ == '__main__':
    get_data()
