#!/usr/bin/env python

import pandas as pd
import geopandas as gpd
from bokeh.layouts import column
from bokeh.io import output_file, save
from src.plotting import plot_map, plot_zip_time_series
from src.utils import Data, markdown_html, get_data

#get_data()
ts_data = pd.read_csv('data/ts.csv') \
    .assign(Date = lambda d: pd.to_datetime(d.Date)) \
    .assign(Zip = lambda d: d.Zip.astype(str))
ts_plot = plot_zip_time_series(ts_data)

map_df = gpd.read_file('data/MD.geojson') \
    .rename(columns = {'per_population':'Total',
                        'increase':'Daily'})
map_plot = plot_map(map_df)
p = column(ts_plot, map_plot)
html_file = 'output.html'
COVID_HTML = '../wckdouglas.github.io/_includes/COVID.html'
output_file(html_file)
save(p)
markdown_html(html_file,COVID_HTML)