Soil Analysis Toolkit

Overview

The Soil Analysis Toolkit extracts soil composition data for given latitude and longitude coordinates using the USDA's Soil Data Mart SOAP API. The data is processed to provide a detailed analysis of soil properties by depth range, including sand, silt, clay content, available water storage, and more.

Input

A list of coordinates (latitude, longitude).
SOAP API endpoint for fetching soil data based on these coordinates.
Latitude and longitude data are passed to the API for querying soil properties.
Output

A CSV file containing weighted average soil properties for specific depth bins at each location.
Columns include:
depth_bin: Depth range (e.g., "0-10 cm").
sand, silt, clay: Soil texture percentages.
bulk_density: Soil bulk density.
sat_hidric_cond: Saturated hydraulic conductivity.
aws: Available water storage in the specified depth range.
lat, lon: Coordinates for each data point.
How the Code Works

Fetch Soil Data:
Uses the fetch_soil_data function to query the USDA Soil Data Mart SOAP API.
Parses the XML response and converts it into a pandas DataFrame.
Process Soil Data:
Filters and cleans the data, converting relevant columns to numeric types.
Uses get_soil_info to process data for a list of coordinates.
Filters the data to retain only the most representative soil components.
Calculate Weighted Averages:
Divides the soil profile into depth bins (e.g., 0-10 cm, 10-20 cm).
Calculates weighted averages for each property based on the depth range.
Output Final Data:
Compiles results for all coordinates into a single DataFrame.
Prints or saves the final data with weighted soil properties for each depth range.
Dependencies

requests: For making HTTP requests to the SOAP API.
xmltodict: For parsing XML responses.
pandas: For data manipulation and analysis.
numpy: For numerical operations.
