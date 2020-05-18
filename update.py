#!/usr/bin/env python

import os
import datetime
import pandas as pd
import geopandas as gpd
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
    creation_date = os.path.getmtime(filename)
    creation_date = datetime.datetime.fromtimestamp(creation_date)
    return today == creation_date.date()


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
zip_ts_plot = plot_time_series(ts_data, grouping='Zip')
city_df = ts_data\
    .groupby(['City','Date','formatted_date'], as_index=False)\
    .agg({'Cases':'sum'})
city_ts_plot = plot_time_series(city_df, grouping='City')



# read map data and plot
map_df = gpd.read_file('data/MD.geojson') \
    .rename(columns = {'per_population':'Total',
                        'increase':'Daily'})
map_plot = plot_map(map_df)


# combined figure
Zip_panel = Panel(child=column(zip_ts_plot, map_plot), title='By zip code')
City_panel = Panel(child=column(city_ts_plot, map_plot), title='By City')
dashboard = Tabs(tabs=[Zip_panel, City_panel])

#p = column(ts_plot, city_ts_plot, map_plot)
html_file = 'output.html'
COVID_HTML = '../wckdouglas.github.io/_includes/COVID.html'
output_file(html_file)
save(dashboard)
markdown_html(html_file,COVID_HTML)
