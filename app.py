import pandas as pd
import numpy as np
import streamlit as st


@st.cache
def get_data():
    keys = ['UID','iso2','iso3','code3','FIPS', 'Admin2',
            'Province_State','Country_Region', 
            'Lat', 'Long_', 'Combined_Key']
    data = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv'
    df = pd.read_csv(data) 
    return df


@st.cache
def transform(df):
    return df.pipe(pd.melt, id_vars = keys, value_name = 'Count', var_name = 'date') \
        .assign(date = lambda d: pd.to_datetime(d.date, format='%m/%d/%y')) \
        .groupby('Combined_Key', as_index=False) \
        .apply(lambda d: d.assign(daily_increase = lambda dd: d.Count - np.roll(d.Count,1))) \
        .assign(daily_increase = lambda d: d.daily_increase.where(d.daily_increase > 0, 0)) \
        .reset_index(drop=True)


def main();
    df = get_data()
    state = streamlit.selectbox("Choose your state: ", df.Province_State) 
    df = transform(df)


if __name__ == "__main__":
    main()