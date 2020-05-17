from bokeh.models import (ColorBar, ColumnDataSource, CustomJS,
                          GeoJSONDataSource, HoverTool, Select,
                          LinearColorMapper, Slider, BasicTicker)
from bokeh.layouts import column, row, widgetbox
from bokeh.palettes import brewer
from bokeh.palettes import Inferno256
from bokeh.plotting import figure
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Interactive plots')

def plot_map(map_df):
    today = str(map_df.Date.astype(str).unique()[0]).split('T')[0]
    logger.info('Plotting %s' %today)
    geosource = GeoJSONDataSource(geojson = map_df.drop('Date', axis=1).to_json())
    col = 'Daily'
    title = 'New COVID19 cases in MD (%s)' %today
    color_mapper = LinearColorMapper(palette=Inferno256, 
                            low=map_df[col].min(), 
                            high=map_df[col].max())

    p = figure(title = title, 
            plot_height = 600,
            plot_width = 800, 
            toolbar_location = 'below',
            tools = "box_zoom, reset")
    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = None
    p.axis.visible = False
    p.title.text_font_size = '25pt'

    # Add patch renderer to figure.
    state_map = p.patches('xs','ys', source = geosource,
                    fill_color = {'field':col,
                                    'transform':color_mapper},
                    line_color = 'gray', 
                    line_width = 0.25, 
                    fill_alpha = 1)
    # Create hover tool
    p.add_tools(HoverTool(tooltips = [('City','@City'),
                                    ('Zip code','@Zip'),
                                    ('Population','@Population'),
                                    ('Cases', '@Cases'),
                                    ('Cases/1M population', '@per_population'),
                                    ('Daily increase','@increase'),
                                    ('Incases/1M population', '@per_population_increase')]))

    callback = CustomJS(args=dict(map_plot=state_map, 
                                source = geosource, 
                                color_map = color_mapper,
                                today = today,
                                p = p), 
                        code ="""
        var low = Math.min.apply(Math,source.data[cb_obj.value]);
        var high = Math.max.apply(Math,source.data[cb_obj.value]);
        color_mapper.low = low;
        color_mapper.high = high;
        map_plot.glyph.fill_color.value = cb_obj.value;
        map_plot.trigger('change');
        if (cb_obj.value == 'Total'){
            var title = 'COVID19 cases in MD (per 1M population)';
        }else{
            var title = 'New COVID19 cases in MD (' + today + ')' 
        }
        p.title = title;
        map_plot.change.emit();
        source.change.emit();
        color_map.change.emit()
    """)

    select = Select(title = 'Dataset', options = ['Daily','Total'], value = 'Daily')
    select.js_on_change('value', callback)
    #color bar
    color_bar = ColorBar(color_mapper = color_mapper, 
                        label_standoff = 8,
                        width = 500, height = 20,
                        border_line_color = None,
                        location = (0,0), 
                        orientation='horizontal')
    p.add_layout(color_bar)
    return column(select,p)

def plot_zip_time_series(ts_data):
    p = figure(x_axis_type="datetime", 
                x_axis_label='Date',
                y_axis_label = 'Total Cases',
                title = 'Daily cases by Zip code',
                tools='box_zoom,reset',
                plot_width=800, plot_height=400,
                y_range=(0, ts_data.Cases.max()),
                x_range= (ts_data.Date.min(), ts_data.Date.max()))
    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = None
    p.title.text_font_size = '25pt'
    p.xaxis.axis_label = 'Date'
    p.yaxis.axis_label = 'Total Cases'
    p.xaxis.axis_label_text_font_size = "25pt"
    p.xaxis.major_label_text_font_size = "25pt"
    p.yaxis.axis_label_text_font_size = "25pt"
    p.yaxis.major_label_text_font_size = "25pt"

    lines = []
    for zip_code, zip_df in ts_data.groupby('Zip'):
        source = ColumnDataSource(zip_df)
        color = 'red' if zip_code == '20850' else 'black'
        alpha = 0.9 if zip_code == '20850' else 0.1
        lw = 10 if zip_code == '20850' else 1
        line = p.line(x='Date',
                y='Cases',
                color = color,
                line_alpha=alpha,
                line_width = lw,
                legend_label=str(zip_code),
                name = str(zip_code),
                source=source)
        #add tool tips
        hover = HoverTool(tooltips =[
                        ('Date','@formatted_date'),
                        ('Cases','@Cases'),
                        ('City', '@City'),
                        ('Zip code', '@Zip')])
        lines.append(line)
        
    def update_plot(attr, old, new):
        highlight_zip = select.value

        for line in lines:
            if line.name != highlight_zip:
                line.glyph.line_alpha = 0.1
                line.glyph.line_color = 'lightgray'
                line.glyph.line_width = 1
            else:
                line.glyph.line_alpha = 0.9
                line.glyph.line_color = 'red'
                line.glyph.line_width = 10
        

    select = Select(title='Zip code', 
        options=ts_data.Zip.unique().tolist(), 
        value='20850')
    select.on_change('value', update_plot)
    p.add_tools(hover)
    p.legend.visible = False
    return column(select, p)
