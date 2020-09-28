import re
import sys
import logging
import geopandas as gpd
from .utils import Data
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Get')

def parse_date(date):
	date_regex = re.compile('20[0-9]{2}-[0-9]{2}\-[0-9]{2}')
	if date_regex.search(date):
		year, month, day = date.split('-')
	else:
		raise ValueError('Date parameter must be in the format of YYYY-MM-DD')
	return 'total{M}_{D}_{Y}'.format(M = month, D = day, Y = year)



def get(date):
	'''
	Select data from one day and output in the data format
	'''
	logger.info('Downloading %s' %date)
	date = parse_date(date)
	logger.info('Using column %s' %date)
	gpd.read_file(Data().MD_zip_data_url)\
		.filter(['ZIP_CODE',date])\
		.fillna(0)\
		.query('%s>0' %date)\
		.assign(**{date: lambda d: d[date].astype(int).astype(str) + ' Cases'})\
		.to_csv(sys.stdout,sep='\t', index=False, header=False)
