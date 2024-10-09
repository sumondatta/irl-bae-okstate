import requests
import xmltodict
import pandas as pd
import numpy as np

# Function to fetch soil data from the API for given latitude and longitude
def fetch_soil_data(lat, lon):
    # Construct the coordinate string in "longitude latitude" format for API query
    lonLat = f"{lon} {lat}"

    # URL for the soil data SOAP API service
    url = "https://SDMDataAccess.nrcs.usda.gov/Tabular/SDMTabularService.asmx"
    headers = {'content-type': 'text/xml'}

    # Construct the SOAP request body to query soil data based on coordinates
    body = f"""<?xml version="1.0" encoding="utf-8"?>
              <soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:sdm="http://SDMDataAccess.nrcs.usda.gov/Tabular/SDMTabularService.asmx">
       <soap:Header/>
       <soap:Body>
          <sdm:RunQuery>
             <sdm:Query>SELECT co.cokey as cokey, ch.chkey as chkey, comppct_r as prcent, slope_r, slope_h as slope, hzname, hzdept_r as deptht, hzdepb_r as depthb, awc_r as awc, 
                        claytotal_r as clay, silttotal_r as silt, sandtotal_r as sand, om_r as om, dbthirdbar_r as bulk_density, wthirdbar_r as th33, ph1to1h2o_r as ph, ksat_r as sat_hidric_cond,
                        ec_r as ec, sar_r as sar, caco3_r as caco3, kffact as k_factor, tfact as t_factor, slope_r as rep_slope, 
                        wthirdbar_r as water_content_0_1bar, wfifteenbar_r as water_content_15bar, weg as wind_erodibility_group, wei as wind_erodibility_index,
                        dbtenthbar_r as bulk_density_10, wtenthbar_r as water_content_10bar 
                        FROM sacatalog sc
                        FULL OUTER JOIN legend lg  ON sc.areasymbol=lg.areasymbol
                        FULL OUTER JOIN mapunit mu ON lg.lkey=mu.lkey
                        FULL OUTER JOIN component co ON mu.mukey=co.mukey
                        FULL OUTER JOIN chorizon ch ON co.cokey=ch.cokey
                        FULL OUTER JOIN chtexturegrp ctg ON ch.chkey=ctg.chkey
                        FULL OUTER JOIN chtexture ct ON ctg.chtgkey=ct.chtgkey
                        FULL OUTER JOIN copmgrp pmg ON co.cokey=pmg.cokey
                        FULL OUTER JOIN corestrictions rt ON co.cokey=rt.cokey
                        WHERE mu.mukey IN (SELECT * from SDA_Get_Mukey_from_intersection_with_WktWgs84('point({lonLat})')) order by co.cokey, ch.chkey, comppct_r, hzdept_r
            </sdm:Query>
          </sdm:RunQuery>
       </soap:Body>
    </soap:Envelope>"""

    # Make a POST request to the API with the SOAP body and headers
    response = requests.post(url, data=body, headers=headers)

    # Parse the XML response into a Python dictionary
    my_dict = xmltodict.parse(response.content)

    # Try to extract the soil data from the response
    try:
        soil_data = my_dict['soap:Envelope']['soap:Body']['RunQueryResponse']['RunQueryResult']['diffgr:diffgram']['NewDataSet']['Table']
    except KeyError as e:
        # Print the raw response and parsed dictionary if extraction fails, for debugging
        print("Raw response content:", response.content)
        print("Parsed response dictionary:", my_dict)
        raise e

    # Convert the extracted data into a pandas DataFrame
    soil_df = pd.DataFrame(soil_data)
    return soil_df

# Function to get soil information for a list of coordinates
def get_soil_info(coords):
    all_data = []

    # Loop through each coordinate pair in the list
    for coord in coords:
        lat, lon = coord

        # Fetch soil data for the given latitude and longitude
        soil_df = fetch_soil_data(lat, lon)

        # List of columns to convert to numeric data types for further processing
        numeric_columns = ['deptht', 'depthb', 'sand', 'silt', 'clay', 'prcent', 'awc', 'om', 'bulk_density', 'th33', 'ph', 'sat_hidric_cond', 'ec', 'sar', 'caco3', 'k_factor', 't_factor', 'rep_slope', 'water_content_0_1bar', 'water_content_15bar', 'wind_erodibility_group', 'wind_erodibility_index', 'bulk_density_10', 'water_content_10bar']

        # Convert specified columns to numeric types, replacing errors with NaN
        for column in numeric_columns:
            soil_df[column] = pd.to_numeric(soil_df[column], errors='coerce')

        # Add latitude and longitude to the DataFrame for reference
        soil_df['lat'] = lat
        soil_df['lon'] = lon

        # Append the DataFrame to the list of all data
        all_data.append(soil_df)

    # Concatenate all data into a single DataFrame
    final_data = pd.concat(all_data, ignore_index=True)

    # Drop duplicate rows based on lat, lon, deptht, depthb, sand, silt, and clay columns
    final_data = final_data.drop_duplicates(subset=['lat', 'lon', 'deptht', 'depthb', 'sand', 'silt', 'clay'])

    return final_data

# List of coordinates to analyze soil data
coords = [
    [36.589068371399115, -98.525390625]
]

# Initialize an empty DataFrame to hold all results
all_priority_df = pd.DataFrame()

# Loop through each coordinate pair to get soil data
for lat, lon in coords:
    # Fetch and process soil data for each coordinate pair
    soil_data = get_soil_info([[lat, lon]])

    # List of columns for filtering the DataFrame
    numeric_columns = ['deptht', 'depthb', 'sand', 'silt', 'clay', 'hzname', 'chkey', 'cokey', 'prcent', 'awc', 'om', 'bulk_density', 'th33', 'ph', 'sat_hidric_cond', 'ec', 'sar', 'caco3', 'k_factor', 't_factor', 'rep_slope', 'water_content_0_1bar', 'water_content_15bar', 'wind_erodibility_group', 'wind_erodibility_index', 'bulk_density_10', 'water_content_10bar']

    # Filter the DataFrame for relevant columns and convert to numeric types
    filtered_soil_data = soil_data[numeric_columns + ['lat', 'lon']]
    for column in numeric_columns:
        filtered_soil_data.loc[:, column] = pd.to_numeric(filtered_soil_data[column], errors='coerce')

    # Drop rows with NaN values in sand, silt, or clay columns
    filtered_soil_data = filtered_soil_data.dropna(subset=['sand', 'silt', 'clay'])

    # Find the component with the highest percentage for prioritization
    highest_prcent = filtered_soil_data['prcent'].max()
    priority_filtered_data = filtered_soil_data[filtered_soil_data['prcent'] == highest_prcent].copy()

    # Define depth bins and calculate the average depth for each bin
    bins = np.arange(0, 210, 10)
    labels = [f'{i}-{i+10}' for i in bins[:-1]]
    priority_filtered_data['depth_bin'] = pd.cut((priority_filtered_data['deptht'] + priority_filtered_data['depthb']) / 2, bins=bins, labels=labels, include_lowest=True)

    # Function to calculate weighted averages for soil properties within a depth range
    def calculate_weighted_averages(df, lower_bound, upper_bound):
        # Select rows where the horizon overlaps with the depth range
        mask = (df['deptht'] < upper_bound) & (df['depthb'] > lower_bound)
        subset = df[mask].copy()

        # Return NaN if no data is available for the specified depth range
        if subset.empty:
            return [np.nan] * (len(numeric_columns) - 2) + [None, None]

        # Calculate the intersection length of each horizon with the depth range
        subset['intersect'] = np.minimum(subset['depthb'], upper_bound) - np.maximum(subset['deptht'], lower_bound)
        total_intersect = subset['intersect'].sum()

        # Return NaN if no valid intersection exists
        if total_intersect == 0:
            return [np.nan] * (len(numeric_columns) - 2) + [None, None]

        # Calculate weighted averages for each property based on intersection length
        weighted_averages = [(subset[column] * subset['intersect']).sum() / total_intersect for column in numeric_columns if column not in ['hzname', 'chkey']]

        # Get representative hzname and chkey
        hzname = subset['hzname'].iloc[0]
        chkey = subset['chkey'].iloc[0]

        return weighted_averages + [hzname, chkey]

    # Calculate the weighted averages for each depth bin and store the results
    priority_results = []
    for label in labels:
        lower_bound, upper_bound = map(float, label.split('-'))
        averages = calculate_weighted_averages(priority_filtered_data, lower_bound, upper_bound)
        priority_results.append((label, *averages, lat, lon))

    # Define the columns for the DataFrame of weighted averages
    priority_columns = ['depth_bin'] + [col for col in numeric_columns if col not in ['hzname', 'chkey']] + ['hzname', 'chkey', 'lat', 'lon']

    # Create a DataFrame from the weighted averages
    priority_df = pd.DataFrame(priority_results, columns=priority_columns)

    # Round numerical columns for clarity and presentation
    priority_df['sand'] = priority_df['sand'].round(1)
    priority_df['silt'] = priority_df['silt'].round(1)
    priority_df['clay'] = priority_df['clay'].round(1)
    priority_df['bulk_density'] = priority_df['bulk_density'].round(2)
    priority_df['sat_hidric_cond'] = priority_df['sat_hidric_cond'].round(4)
    priority_df['k_factor'] = priority_df['k_factor'].round(2)
    priority_df['t_factor'] = priority_df['t_factor'].astype('Int64')
    priority_df['wind_erodibility_group'] = priority_df['wind_erodibility_group'].astype('Int64')
    priority_df['wind_erodibility_index'] = priority_df['wind_erodibility_index'].astype('Int64')

    # Calculate the available water storage (AWS) for each depth range
    priority_df['aws'] = priority_df.apply(lambda row: row['awc'] * (row['depthb'] - row['deptht']) / 100, axis=1)

    # Fill NaN values using forward fill for consistency
    priority_df = priority_df.ffill()

    # Append the processed data to the final DataFrame
    all_priority_df = pd.concat([all_priority_df, priority_df], ignore_index=True)

# Print the final DataFrame containing soil composition by depth for all coordinates
print("Final Priority Soil Composition by Depth Range for All Coordinates:")
print(all_priority_df.to_string(index=False))
