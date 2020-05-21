#!/usr/bin/env python

import os
import datetime
import pandas as pd
import geopandas as gpd
import numpy as np
from bokeh.layouts import column
from bokeh.io import output_file, save
from bokeh.models.widgets import Tabs, Panel
from src.plotting import plot_map, plot_time_series
from src.utils import Data, markdown_html, get_data
import logging

logging.basicConfig(level = logging.INFO)
logger = logging.getLogger('Update plot')
today = datetime.date.today()
def is_updated(filename):
    '''
    check if the file exist
    if yes, check if it's updated today
    '''
    if os.path.isfile(filename):
        creation_date = os.path.getmtime(filename)
        creation_date = datetime.datetime.fromtimestamp(creation_date)
        return today == creation_date.date() 
    else:
        return False


ts_data = 'data/ts.csv'
map_data = 'data/MD.geojson'
if not (is_updated(ts_data) or is_updated(map_data)):
    logger.info('Updating data: %s' %str(today))
    #daily update!!
    get_data(ts_data_file = ts_data,
            map_data_file = map_data) 

# read time series data and plot
ts_data = pd.read_csv('data/ts.csv') \
    .assign(Date = lambda d: pd.to_datetime(d.Date)) \
    .assign(Zip = lambda d: d.Zip.astype(str))
new_zip_df = ts_data\
    .assign(increase = lambda d: d.groupby('Zip').Cases.transform(lambda x: x - np.roll(x,1)))\
    .query('increase>=0')
zip_ts_plot = plot_time_series(ts_data, new_zip_df, grouping='Zip')

city_df = ts_data\
    .groupby(['City','Date','formatted_date'], as_index=False)\
    .agg({'Cases':'sum'})
new_city_df = new_zip_df\
    .groupby(['City','Date','formatted_date'], as_index=False)\
    .agg({'Cases':'sum','increase':'sum'})
city_ts_plot = plot_time_series(city_df, new_city_df, grouping='City')



# read map data and plot
map_df = gpd.read_file('data/MD.geojson') \
    .rename(columns = {'per_population':'Total',
                        'increase':'Daily'})
today = str(map_df.Date.astype(str).unique()[0]).split('T')[0]
zip_map_plot = plot_map(map_df, with_zip = True, today = today)

map_df = gpd.read_file('data/MD.geojson') \
    .rename(columns = {'per_population':'Total',
                        'increase':'Daily'}) \
    .drop('Zip', axis=1)\
    .assign(Population = lambda d: d.Population.astype(float))\
    .dissolve(by = ['City', 'State'], aggfunc='sum')\
    .assign(Total = lambda d: d.Cases/d.Population)\
    .assign(per_populatin_increase = lambda d: d.Daily/d.Population) \
    .reset_index()
city_map_plot = plot_map(map_df, with_zip = False, today = today)


# combined figure
Zip_panel = Panel(child=column(zip_ts_plot, zip_map_plot,sizing_mode="stretch_both"), title='By zip code')
City_panel = Panel(child=column(city_ts_plot, city_map_plot,sizing_mode="stretch_both"), title='By City')
dashboard = Tabs(tabs=[Zip_panel, City_panel])

#p = column(ts_plot, city_ts_plot, map_plot)
html_file = 'dashboard.html'
COVID_HTML = '../wckdouglas.github.io/_includes/COVID.html'
output_file(html_file)
save(dashboard)
if os.path.isfile(COVID_HTML):
    markdown_html(html_file,COVID_HTML)
