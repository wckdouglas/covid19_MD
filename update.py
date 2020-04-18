#!/usr/bin/env python

import pandas as pd
import glob
from src.utils import Data, markdown_html
import matplotlib.pyplot as plt
from bokeh.io import show, save, output_file
from bokeh.models import (CDSView, ColorBar, ColumnDataSource,
                          GeoJSONDataSource, HoverTool,
                          LinearColorMapper, Slider, BasicTicker)
from bokeh.layouts import column, row, widgetbox
from bokeh.palettes import brewer
from bokeh.palettes import Inferno256
from bokeh.plotting import figure
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Update')

def plot_map(data):
    geosource = GeoJSONDataSource(geojson = data.drop('Date', axis=1).to_json())
    color_mapper = LinearColorMapper(palette=Inferno256, 
                            low=data.per_population.min(), 
                            high=data.per_population.max())

    p = figure(title = 'COVID19 in Maryland\n(Cases per 1,000 people)', 
            plot_height = 600,
            plot_width = 950, 
            toolbar_location = 'right',
            tools = "pan, wheel_zoom, box_zoom, reset")
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
                                    ('Cases/1k population', '@per_population')]))
    #color bar
    color_bar = ColorBar(color_mapper = color_mapper, 
                        label_standoff = 8,
                        width = 500, height = 20,
                        border_line_color = None,
                        location = (0,0), 
                        major_label_text_font_size='20px',
                        orientation='horizontal')
    p.add_layout(color_bar)
    logger.info('Plotted map')
    return p


def plot_line(ts_data):
    p = figure(x_axis_type="datetime", 
                plot_width = 950, 
                x_axis_label='Date',
                y_axis_label = 'Total Cases',
                title = 'Daily cases by city',
                tools='save,pan,box_zoom,reset,wheel_zoom')
    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = None
    p.title.text_font_size = '25pt'
    p.xaxis.axis_label = 'Date'
    p.yaxis.axis_label = 'Total Cases'
    p.xaxis.axis_label_text_font_size = "25pt"
    p.xaxis.major_label_text_font_size = "25pt"
    p.yaxis.axis_label_text_font_size = "25pt"
    p.yaxis.major_label_text_font_size = "25pt"


    for zip, zip_df in ts_data.groupby('City'):
        source = ColumnDataSource(zip_df)
        p.line(x='Date',
                y='Cases',
                color = 'grey',
                line_width=4,
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
            .pipe(lambda d: d[d.Date==d.Date.max()]) \
            .filter(['Zip','City','State','Cases','Date','geometry', 'Population']) \
            .assign(Cases = lambda d: d.Cases.fillna(0)) \
            .pipe(lambda d: d[~pd.isnull(d.geometry)]) \
            .assign(per_population = lambda d: d.Cases / d.Population.astype(int) * 1000)
    today = str(data.Date.astype(str).unique()[0])
    logger.info('Plotting date: %s' %today)

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
    
    p1 = plot_map(data)
    p2 = plot_line(ts_data)

    p = column(p1, p2)
    html_file = 'output.html'
    COVID_HTML = '../wckdouglas.github.io/_includes/COVID.html'
    output_file(html_file)
    save(p)
    markdown_html(html_file,COVID_HTML)

if __name__ == '__main__':
    main()
