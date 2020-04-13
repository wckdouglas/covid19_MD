import pandas as pd
import glob
import os

class Data():
    def __init__(self, state = 'MD'):
        #data and URL path
        self.data_path = 'data/'
        self.zip_map_url = 'https://public.opendatasoft.com/explore/dataset/us-zip-code-latitude-and-longitude'\
                '/download/?format=csv&timezone=America/New_York'\
                '&lang=en&use_labels_for_header=true&csv_separator=%3B'
        self.zip_census = 'https://data.lacity.org/api/views/nxs9-385f/rows.csv?accessType=DOWNLOAD'

        #actual reading dat
        self.zip_map = self.read_zip_map()
        self.zip_codes = self.zip_map.Zip
        self.zip_covid = self.read_zip_COVID()
        self.zip_census = self.read_zip_stat()

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


    def read_zip_stat(self):
        return pd.read_csv(self.zip_census) \
            .rename(columns = {'Zip Code':'Zip'}) \
            .pipe(lambda d: d[d.Zip.isin(self.zip_codes)])
