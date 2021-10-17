# Import packages
# Streamlit
import streamlit as st

# To connect with AWS S3
import s3fs
import os

# To tidy up the data
import pandas as pd

# To scale the data
from sklearn.preprocessing import MinMaxScaler

# Create connection object
fs = s3fs.S3FileSystem(anon=False)

# Retrieve file contents
@st.cache
def read_file(date):
    with fs.open(f's3://zmd-bidder-data/adfatigued/zoomd-events-{date}') as f:
        return pd.read_csv(f)

df = pd.DataFrame()
for i in range(11,14):
    read_df = read_file(f'2021-10-{i}.csv')
    df = df.append(read_df)
df = df.reset_index(drop=True)

# Clean data
# Remove unused variable
df = df.drop('/v1/ev?tp', axis=1)

# Combine gaid & idfa as device id
df['device_id'] = df['gaid'].combine_first(df['idfa'])

# Get the result
# Copy the df for merging in the result
df1 = df.copy()

# Subset data to select used variable only and drop the null values
df = df1[['eventtime', 'country_code', 'partner_id', 'device_id']]
df = df.dropna()

# Group the `device_id` per `country_code` & `partner_id` then count it
df_group = pd.DataFrame(df.groupby(
    by=['country_code', 'partner_id', 'device_id']).count())

# Reset index
df_group = df_group.reset_index()

# Rename count column
df_group = df_group.rename(columns={"eventtime": "count"})

# Find unique values of `country_code` and `partner_id` combination and exclude the combination with only 1 member
unique = df_group.groupby(by=["country_code", "partner_id"]).count()
unique = unique[(unique['count'] > 1)]
unique = unique.reset_index()

# Scale the count counted in the first step
df_scaled = pd.DataFrame()
scaler = MinMaxScaler()
for country in unique.country_code.unique():
    for partner in unique[unique.country_code == country].partner_id.unique():
        df_scaled_ind = df_group.loc[((df_group.country_code == country) & (
            df_group.partner_id == partner))].copy()
        df_scaled_ind.loc[:, ('scale')] = scaler.fit_transform(
            df_scaled_ind[['count']])
        df_scaled = df_scaled.append(df_scaled_ind)

# Streamlit
# Title
st.title("Ad-Fatigued List Generator")
st.write("Using zoomd-events-2021-10-11 - zoomd-events-2021-10-13 based on Country Code & Partner ID")
st.write("NB : Threshold represents the minimum of how many times a given user received the ad compared to the range of ads received by users in his group to be classified as an ad-fatigued user. The higher the threshold means the more frequently the users in the list received the ads compared to their own group.")

# Slider of the threshold
with st.form(key="slider"):
    threshold = st.slider('Threshold', min_value=0.0,
                          max_value=1.0, value=0.8, step=0.1)
    submit = st.form_submit_button()

# Result based on slider
result = df_scaled[df_scaled.scale > threshold]

# Remove duplicate device_id
result = result.drop_duplicates(subset='device_id')

# Clean result
result = result.merge(df1, on=["device_id", "country_code", "partner_id"], how="left")[
    ["device_id", "os", "country_code", "partner_id"]]
result = result.drop_duplicates(
    subset=["device_id", "country_code", "partner_id"])
result = result.set_index("device_id")

# Conver result to csv


@st.cache
def convert_df(df):
    return df.to_csv().encode('utf-8')


csv = convert_df(result)

if submit:
    st.write(
        f'Ad Fatigued User List with Threshold of {threshold} ({result.shape[0]} users)')
    st.write(result)
    st.download_button(
        label="Download as CSV",
        data=csv,
        file_name=f"ad_fatigued_{threshold}.csv",
        mime='text/csv'
    )
