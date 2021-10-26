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
    with fs.open(f's3://zmd-bidder-data/adfatigued/zoomd-impressions-{date}.csv') as f:
        return pd.read_csv(f)

# Find result
def trigger():
    # Group the `DSP_BID_ID` by `USER_COUNTRY_ID` & `CAMPAIGN_NAME` then count it
    df_group = pd.DataFrame(df.groupby(by=['DSP_BID_ID','USER_COUNTRY_ID','CAMPAIGN_NAME']).size().to_frame("count"))
    # Reset index
    df_group = df_group.reset_index()
    # Scale the count counted in the first step
    df_scaled = pd.DataFrame()
    scaler = MinMaxScaler()
    for country in st.session_state.countries:
        for campaign in df_group[df_group.USER_COUNTRY_ID == str(country)].CAMPAIGN_NAME.unique():
            df_scaled_ind = df_group.loc[((df_group.USER_COUNTRY_ID  == str(country)) & (
                df_group.CAMPAIGN_NAME == campaign))].copy()
            df_scaled_ind.loc[:, ('scale')] = scaler.fit_transform(
                df_scaled_ind[['count']])
            df_scaled = df_scaled.append(df_scaled_ind)
    # Result based on slider
    result = df_scaled[df_scaled.scale > st.session_state.threshold]
    # Remove duplicate DSP_BID_ID
    result = result.drop_duplicates(subset='DSP_BID_ID')
    # Clean result
    result = result[['DSP_BID_ID','USER_COUNTRY_ID','CAMPAIGN_NAME']]
    result = result.set_index('DSP_BID_ID')

    # Conver result to csv


    @st.cache
    def convert_df(df):
        return df.to_csv().encode('utf-8')


    csv = convert_df(result)

    st.write(
            f'Ad Fatigued User List with Threshold of {st.session_state.threshold} ({result.shape[0]} users)')
    st.write(result)
    st.download_button(
        label="Download as CSV",
        data=csv,
        file_name=f"ad_fatigued_{st.session_state.threshold}.csv",
        mime='text/csv'
    )
        
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
    date_input = st.date_input("Date Range", value=(date.today()-timedelta(days=7), date.today()-timedelta(days=2)), max_value=date.today()-timedelta(days=2))
    submit = st.form_submit_button()
    
# Read files based on date input
if submit:
    daterange = pd.date_range(date_input[0], date_input[1])
    df = pd.DataFrame()
    for i in daterange:
        read_df = read_file(i.date())
        df = df.append(read_df)
    df = df.dropna()
    df = df.reset_index(drop=True)

    # Slider of the threshold
    with st.form(key="slider"):
        st.slider('Threshold', min_value=0.0,
                            max_value=1.0, value=0.8, step=0.1, key="threshold")
        st.selectbox('Country ID', df.USER_COUNTRY_ID.unique(), key="countries")
        st.form_submit_button("Submit", on_click=trigger)
