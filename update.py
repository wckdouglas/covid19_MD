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
<<<<<<< HEAD
from bokeh.io import show, save, output_file
from bokeh.models import (CDSView, ColorBar, ColumnDataSource,
                          GeoJSONDataSource, HoverTool,
                          LinearColorMapper, Slider, BasicTicker)
from bokeh.layouts import column, row, widgetbox
from bokeh.palettes import brewer
from bokeh.palettes import Inferno256
from bokeh.plotting import figure
from src.utils import Data, markdown_html
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Update')

def plot_cases_map(data):
    geosource = GeoJSONDataSource(geojson = data.drop('Date', axis=1).to_json())
    color_mapper = LinearColorMapper(palette=Inferno256, 
                            low=data.per_population.min(), 
                            high=data.per_population.max())

    p = figure(title = 'COVID19 in Maryland\n(Cases per 1M people)', 
            plot_height = 400,
            plot_width = 950, 
            tools = "box_zoom, reset")
    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = None
    p.axis.visible = False
    p.title.text_font_size = '25pt'

    # Add patch renderer to figure.
    states = p.patches('xs','ys', source = geosource,
                    fill_color = {'field':'per_population',
                                    'transform':color_mapper},
                    line_color = 'gray', 
                    line_width = 0.25, 
                    fill_alpha = 1)
    # Create hover tool
    p.add_tools(HoverTool(tooltips = [('City','@City'),
                                    ('Zip code','@Zip'),
                                    ('Population','@Population'),
                                    ('Cases', '@Cases'),
                                    ('Cases/1M population', '@per_population')]))
    #color bar
    color_bar = ColorBar(color_mapper = color_mapper, 
                        label_standoff = 8,
                        width = 500, height = 20,
                        border_line_color = None,
                        location = (0,0), 
                        major_label_text_font_size='20px',
                        orientation='horizontal')
    p.add_layout(color_bar)
    logger.info('Plotted total cases map')
    return p


def plot_new_cases_map(per_day_increase_data, today):
    geosource = GeoJSONDataSource(geojson = per_day_increase_data.to_json())
    color_mapper = LinearColorMapper(palette=Inferno256, 
                            low=per_day_increase_data.increase.min(), 
                            high=per_day_increase_data.increase.max())

    p = figure(title = 'New COVID19 cases in Maryland ({})'.format(today), 
            plot_height = 400,
            plot_width = 950, 
            tools = "box_zoom, reset")
    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = None
    p.axis.visible = False
    p.title.text_font_size = '25pt'

    # Add patch renderer to figure.
    states = p.patches('xs','ys', source = geosource,
                    fill_color = {'field':'increase',
                                    'transform':color_mapper},
                    line_color = 'gray', 
                    line_width = 0.25, 
                    fill_alpha = 1)
    # Create hover tool
    p.add_tools(HoverTool(tooltips = [('Date','@Date'),
                                    ('City','@City'),
                                    ('Zip code','@Zip'),
                                    ('Population','@Population'),
                                    ('New cases', '@increase'),
                                    ('New cases/1M population', '@per_population')]))

    #color bar
    color_bar = ColorBar(color_mapper = color_mapper, 
                        label_standoff = 8,
                        width = 500, height = 20,
                        border_line_color = None,
                        location = (0,0), 
                        major_label_text_font_size='20px',
                        orientation='horizontal')
    p.add_layout(color_bar)
    logger.info('Plotted daily new cases map')
    return p


def plot_line(ts_data):
    p = figure(x_axis_type="datetime", 
                plot_width = 950, 
                plot_height = 400, 
                x_axis_label='Date',
                y_axis_label = 'Total Cases',
                title = 'Daily cases by city',
                tools='box_zoom,reset')
    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = None
    p.title.text_font_size = '25pt'
    p.xaxis.axis_label = 'Date'
    p.yaxis.axis_label = 'Total Cases'
    p.xaxis.axis_label_text_font_size = "25pt"
    p.xaxis.major_label_text_font_size = "25pt"
    p.yaxis.axis_label_text_font_size = "25pt"
    p.yaxis.major_label_text_font_size = "25pt"


    for city, city_df in ts_data.groupby('City'):
        source = ColumnDataSource(city_df)
        color = 'black' if city == 'Rockville' else 'grey'
        lw = 4 if city == 'Rockville' else 2
        alpha = 0.9 if city == 'Rocville' else 0.4
        p.line(x='Date',
                y='Cases',
                color = color,
                line_width=lw,
                line_alpha=0.8,
                source=source)
        #add tool tips
        hover = HoverTool(tooltips =[
                        ('Date','@formatted_date'),
                        ('Cases','@Cases'),
                        ('City', '@City')])
    p.add_tools(hover)
    logger.info('Plotted line plot')
    return p


def main():
    # make dataframes
    maryland = Data(state='MD')
    logger.info('Retrieved data')

    #make map data
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
    logger.info('Plotting date: %s' %today)

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


    # time series data
    ts_data = maryland.zip_covid\
        .merge(maryland.zip_map.filter(['Zip','City']), on = 'Zip') \
        .groupby(['Zip','City'], as_index=False)\
        .apply(lambda d: d.sort_values('Date')  \
        .assign(Cases = lambda d: d.Cases.fillna(method='ffill', axis=0)\
        .fillna(0))) \
        .reset_index(drop=True) \
        .groupby(['City','Date'], as_index=False) \
        .agg({'Cases':'sum'})\
        .assign(formatted_date = lambda d: d.Date.astype(str)) 
    
    today = str(ts_data.Date.max()).split(' ')[0]
    first_day = str(ts_data.Date.min()).split(' ')[0]
    logger.info('Time series date from %s to %s' %(first_day,today))
    
    p1 = plot_cases_map(total_case_data)
    p2 = plot_new_cases_map(per_day_increase_data, today)
    p3 = plot_line(ts_data)

    p = column(p1, p2, p3)
    html_file = 'output.html'
    COVID_HTML = '../wckdouglas.github.io/_includes/COVID.html'
    output_file(html_file)
    save(p)
    markdown_html(html_file,COVID_HTML)

if __name__ == '__main__':
    main()
=======
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
>>>>>>> 665af4954d1e311586e998e2c4f877c624636be2
