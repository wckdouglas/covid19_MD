import datetime
import os
import sys

import geopandas as gpd
import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.layouts import column
from bokeh.models.widgets import Panel, Tabs

from .plotting import PLOT_HEIGHT, PLOT_WIDTH, plot_map, plot_time_series
from .utils import Data, get_data, logger, markdown_html

today = datetime.date.today()


def is_updated(filename):
    """
    check if the file exist
    if yes, check if it's updated today
    """
    if os.path.isfile(filename):
        creation_date = os.path.getmtime(filename)
        creation_date = datetime.datetime.fromtimestamp(creation_date)
        return creation_date.date() == today
    else:
        return False


def ts_plots(ts_data_file):
    # read time series data and plot
    ts_data = (
        pd.read_csv(ts_data_file)
        .assign(Date=lambda d: pd.to_datetime(d.Date))
        .assign(Zip=lambda d: d.Zip.astype(str))
    )
    new_zip_df = ts_data.assign(
        increase=lambda d: d.groupby("Zip").Cases.transform(lambda x: x - np.roll(x, 1))
    ).query("increase>=0")
    zip_ts_plot = plot_time_series(ts_data, new_zip_df, grouping="Zip")

    city_df = ts_data.groupby(["City", "Date", "formatted_date"], as_index=False).agg(
        {"Cases": "sum"}
    )
    new_city_df = new_zip_df.groupby(
        ["City", "Date", "formatted_date"], as_index=False
    ).agg({"Cases": "sum", "increase": "sum"})
    city_ts_plot = plot_time_series(city_df, new_city_df, grouping="City")
    return zip_ts_plot, city_ts_plot


def map_plots(map_data_file):
    # read map data and plot
    map_df = gpd.read_file(map_data_file).rename(
        columns={"per_population": "Total", "increase": "Daily"}
    )
    today = str(map_df.Date.astype(str).unique()[0]).split("T")[0]
    zip_map_plot = plot_map(map_df, with_zip=True, today=today)

    map_df = (
        gpd.read_file("data/MD.geojson")
        .rename(columns={"per_population": "Total", "increase": "Daily"})
        .drop("Zip", axis=1)
        .assign(Population=lambda d: d.Population.astype(float))
        .dissolve(by=["City", "State"], aggfunc="sum")
        .assign(Total=lambda d: d.Cases / d.Population)
        .assign(per_populatin_increase=lambda d: d.Daily / d.Population)
        .reset_index()
    )
    city_map_plot = plot_map(map_df, with_zip=False, today=today)
    return zip_map_plot, city_map_plot


def update_data(args, ts_data_file, map_data_file):
    """
    write new data to file
    """
    if not is_updated(ts_data_file) or not is_updated(map_data_file) or args.refresh:
        logger.info("Updating data: %s" % str(today))
        # daily update!!
        get_data(
            ts_data_file=ts_data_file,
            map_data_file=map_data_file,
            datadir=args.datadir,
        )


def update(args, get_app=False):
    logger.info("Updating dashboard")
    ts_data_file = args.datadir + "/ts.csv"
    map_data_file = args.datadir + "/MD.geojson"
    update_data(args, ts_data_file, map_data_file)
    zip_ts_plot, city_ts_plot = ts_plots(ts_data_file)
    zip_map_plot, city_map_plot = map_plots(map_data_file)

    # combined figure
    Zip_panel = Panel(
        child=column(zip_ts_plot, zip_map_plot, sizing_mode="stretch_both"),
        title="By zip code",
    )
    City_panel = Panel(
        child=column(city_ts_plot, city_map_plot, sizing_mode="stretch_both"),
        title="By City",
    )
    dashboard = Tabs(
        tabs=[Zip_panel, City_panel],
        width=PLOT_WIDTH,
        height_policy="fixed",
        width_policy="fixed",
        height=int(1.1 * (3 * PLOT_HEIGHT)),
    )

    # p = column(ts_plot, city_ts_plot, map_plot)
    if not get_app:
        html_file = args.out_html
        output_file(html_file)
        save(dashboard)
    else:
        return dashboard


def check_update():
    logger.info("Checking database")
    dat = Data()
    dat.read_zip_COVID()
    dat.zip_covid.pipe(lambda d: d[d.Date == d.Date.max()]).query("Cases > 0").assign(
        Cases=lambda d: d.Cases.astype(int).astype(str) + " Cases"
    ).to_csv(sys.stdout, index=False, sep="\t", header=False)
