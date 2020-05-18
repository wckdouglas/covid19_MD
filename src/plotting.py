from bokeh.models import (ColorBar, ColumnDataSource, CustomJS,
                          GeoJSONDataSource, HoverTool, Select,
                          LinearColorMapper, Slider, BasicTicker)
from bokeh.layouts import column, row, widgetbox
from bokeh.palettes import brewer
from bokeh.palettes import Viridis256
from bokeh.plotting import figure
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Interactive plots')

def plot_map(map_df):
    today = str(map_df.Date.astype(str).unique()[0]).split('T')[0]
    logger.info('Plotting map for: %s' %today)
    logger.info('Plotting %i zip codes' %map_df.shape[0])
    geosource = GeoJSONDataSource(geojson = map_df.drop('Date', axis=1).to_json())
    col = 'Daily'
    title = 'New COVID19 cases in MD (%s)' %today
    color_mapper = LinearColorMapper(palette=Viridis256, 
                            low=map_df[col].min(), 
                            high=map_df[col].max())

    p = figure(title = title, 
            plot_height = 400,
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
    hover = HoverTool(tooltips = [('City','@City'),
                                    ('Zip code','@Zip'),
                                    ('Population','@Population'),
                                    ('Cases', '@Cases'),
                                    ('Cases/1M population', '@Total'),
                                    ('Daily increase','@Daily')])
                                    #('Incases/1M population', '@per_population_increase')]))
    p.add_tools(hover)

    code = """
        var selected = cb_obj.value
        console.log('Selected: ' + selected);
        var low = Math.min.apply(Math,source.data[selected]);
        var high = Math.max.apply(Math,source.data[selected]);
        console.log('Low: ' + low+ '; high: ' + high);
        color_mapper.low = low;
        color_mapper.high = high;
        map_plot.glyph.fill_color = {'field': selected,
                                    'transform': color_mapper};
        if (selected == 'Total'){
            var title = 'COVID19 cases in MD (per 1M population)';
        }else{
            var title = 'New COVID19 cases in MD (' + today + ')'; 
        }
        console.log('Plotting: ' + title)
        p.title.text = title;
    """

        
    callback = CustomJS(args=dict(map_plot=state_map, 
                                source = geosource, 
                                today = today,
                                color_mapper = color_mapper,
                                p = p), code = code)
        

    select = Select(title = 'Dataset', 
                    value = 'Daily',
                    options = ['Total','Daily'])
    select.js_on_change('value', callback)
    #color bar
    color_bar = ColorBar(color_mapper = color_mapper, 
                        label_standoff = 8,
                        width = 400, height = 20,
                        major_label_text_font_size='16px',
                        major_tick_line_width=3,
                        border_line_color = None,
                        location = (0,0), 
                        orientation='horizontal')
    p.add_layout(color_bar)
    return column(select,p)

def plot_time_series(ts_data, grouping='Zip'):
    tooltips = [('Date','@formatted_date'),
                ('Cases','@Cases'),
                ('City', '@City')]
    if grouping == 'Zip':
        title = 'Zip code' 
        default = '20850'
        tooltips.append(('Zip code', '@Zip'))
    else:
        title = 'City'
        default = 'Rockville'
    logger.info('Plotting time series for: %s level' %title)
    options = ts_data[grouping].unique().tolist()
    p = figure(x_axis_type="datetime", 
                x_axis_label='Date',
                y_axis_label = 'Total Cases',
                title = 'Daily cases by {}'.format(title),
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
    for group, group_df in ts_data.groupby(grouping):
        source = ColumnDataSource(group_df)

        if group in ['Rockville','20850']:
            color = 'red'
            alpha = 0.7
            lw = 5
            level = 'overlay'
        else:
            color = 'lightgray'
            alpha = 0.3
            lw = 2
            level = 'underlay'

        line = p.line(x='Date',
                y='Cases',
                color = color,
                line_alpha=alpha,
                line_width = lw,
                legend_label=str(group),
                name = str(group),
                source=source)
        line.level = level
        #add tool tips
        hover = HoverTool(tooltips = tooltips)
        lines.append(line)
    p.add_tools(hover)
    p.legend.visible = False

    code = """
        var highlight = cb_obj.value.toString()
        console.log('Selected: ' + highlight);
        var i;
        for (i = 0; i < lines.length; i++){
            var line = lines[i];
            if (line.name == highlight){
                console.log('Found: ' + line.name);
                line.glyph.line_alpha = 0.7;
                line.glyph.line_color = 'red';
                line.glyph.line_width = 5;
                line.level = 'overlay';
            }else{
                line.glyph.line_alpha = 0.3;
                line.glyph.line_color = 'lightgray';
                line.glyph.line_width = 1;
                line.level = 'underlay';
            }
            line.change.emit();
        } 
    """

        
    callback = CustomJS(args=dict(lines=lines), code = code)
    select = Select(title=title, 
        options=options, 
        value=default)
    select.js_on_change('value', callback)
    logger.info('Plotting %i %s' %(len(options), title))
    return column(select, p)
