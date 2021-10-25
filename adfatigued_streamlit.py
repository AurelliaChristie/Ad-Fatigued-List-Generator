# Import packages
# Streamlit
import streamlit as st

# To connect with AWS S3
import s3fs
import os

# To tidy up the data
import pandas as pd
from datetime import date, timedelta

# To scale the data
from sklearn.preprocessing import MinMaxScaler

# Create connection object
fs = s3fs.S3FileSystem(anon=False)

# Retrieve file contents
@st.cache
def read_file(date):
    with fs.open(f's3://zmd-bidder-data/zoomd-impressiosns-{date}.csv') as f:
        return pd.read_csv(f)

# Find result
def trigger():
    st.write(df.head())

# Streamlit
# Title
col1, mid, col2 = st.columns([3, 1, 18])
with col1:
    st.image('zoomd-logo.png')
with col2:
    st.title("Ad-Fatigued List Generator")
st.write("Using zoomd-impressions-####-##-##.csv, locate DSP_BID_ID based on Country ID & Campaign Name.")

# Date input
with st.form(key="datetime"):
    date_input = st.date_input("Date Range", value=(date.today()-timedelta(days=7), date.today()-timedelta(days=1)), max_value=date.today()-timedelta(days=1))
    submit = st.form_submit_button()
    
# Read files based on date input
if submit:
    daterange = pd.date_range(date_input[0], date_input[1])
    df = pd.DataFrame()
    for i in daterange:
        read_df = read_file(i.date())
        read_df = read_df[['DSP_BID_ID','USER_COUNTRY_ID','CAMPAIGN_NAME']]
        df = df.append(read_df)
    df = df.dropna()
    df = df.reset_index(drop=True)

    # Slider of the threshold
    with st.form(key="slider"):
        st.slider('Threshold', min_value=0.0,
                            max_value=1.0, value=0.8, step=0.1, key="threshold")
        st.selectbox('Country ID', df.USER_COUNTRY_ID.unique(), key="countries")
        st.form_submit_button("Submit", on_click=trigger)
