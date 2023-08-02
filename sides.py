import pandas as pd
# a = []
# for i in range(10):
#     dat = pd.DataFrame({'a':(j + i for j in range(2)),'b':(j + i + 1 for j in range(2)),'c':(j + i + 2 for j in range(2)),'d':(j + i + 3 for j in range(2))})
#     a.append(dat)
# f = pd.DataFrame({'hell':(1,),'hel':(2,),'he':(3,)})
# f.loc[1] = {'hell':1,'he':2}
# print(f)

import requests
from tkinter import Tk  #changed to accept excel sheets
from tkinter.filedialog import askopenfilename
Tk().withdraw() 
inputxl = askopenfilename(title='input')
data = pd.read_excel(inputxl,sheet_name='Route Information')
order_data = pd.read_excel(inputxl,sheet_name='Order Information')
df = order_data.drop_duplicates(subset=['Ship From','Ship To'],keep='first')

# class RatePortalAPI:
#     def __init__(self, api_url, api_key):
#         self.api_url = api_url
#         self.api_key = api_key

#     def create_rateportal_payload(self, row):
#         rate_payload = {
#             "Carriers": [
#                 {
#                     "CarrierId": row['CarrierId'],
#                     "EDIServiceLevelCodes": [row['EDIServiceLevelCodes']],
#                 }
#             ],
#             "IncludeLiveRates": True,
#             "UseDefaultPackagingForLiveRates": False,
#             "UsesPerPoundCostForLiveRates": False,
#             "SourceTypeId": 2,
#             "OriginLocation": {
#                 "Address": None,
#                 "AddressLine2": None,
#                 "LocationId": None,
#                 "CityId": row['OriginCityId'],
#                 "City": None,
#                 "StateId": row['OriginStateId'],
#                 "StateCode": None,
#                 "State": None,
#                 "CountryId": row['OriginCountryId'],
#                 "CountryCode": None,
#                 "Country": None,
#                 "Zip": row['OriginZip'],
#                 "TimeZoneID": row['OriginTimeZoneID']
#             },
#             "DestinationLocation": {
#                 "Address": None,
#                 "AddressLine2": None,
#                 "LocationId": None,
#                 "CityId": row['DestCityId'],
#                 "City": None,
#                 "StateId": row['DestStateId'],
#                 "StateCode": None,
#                 "State": None,
#                 "CountryId": row['DestCountryId'],
#                 "CountryCode": None,
#                 "Country": None,
#                 "Zip": row['DestZip'],
#                 "TimeZoneID": row['DestTimeZoneID']
#             },
#             "PlanDeliveryDate": row['PlanDeliveryDate'],
#             "ShipmentNumber": None,
#             "PackagingInformation": [
#                 {
#                     "ShipUnitsCount": None,
#                     "ShipUnitType": None,
#                     "WeightPerUnit": None,
#                     "WeightUOM": row['WeightUOM'],
#                     "LengthPerUnit": None,
#                     "WidthPerUnit": None,
#                     "HeightPerUnit": None,
#                     "DimensionsUOM": row['DimensionsUOM'],
#                     "ShipUnitLevelId": 2
#                 }
#             ],
#             "StopCount": 1.0,
#             "HazmatFlag": row['HazmatFlag'],
#             "PickupDate": row['PickupDate'],
#             "TeslaChargeableWeight": 0.0
#         }

#         return rate_payload

#     pass

#     def post_rateportal_payload(self, payload):
#         headers = {
#             "Authorization": f"Bearer {self.api_key}",
#             "Content-Type": "application/json"
#         }

#         response = requests.post(self.api_url, json=payload, headers=headers)
#         if response.status_code == 200:
#             return response.json()
#         else:
#             print(f"Failed to post payload. Status code: {response.status_code}")
#             return None

#     def get_shipment_cost_from_response(self, response):
#         if response and 'data' in response:
#             shipment_cost = response['data'][0]['shipmentCost']
#             return shipment_cost
#         else:
#             print("Error: Invalid API response.")
#             return None

# selected_columns = ['CarrierId', 'EDIServiceLevelCodes', 'OriginCityId', 'OriginStateId', 'OriginCountryId', 'OriginZip', 'OriginTimeZoneID', 'DestCityId', 'DestStateId', 'DestCountryId', 'DestZip', 'DestTimeZoneID', 'PlanDeliveryDate', 'ShipUnitsCount', 'WeightPerUnit', 'WeightUOM', 'LengthPerUnit', 'WidthPerUnit', 'HeightPerUnit', 'DimensionsUOM', 'HazmatFlag', 'PickupDate']
# row_values = df[selected_columns].iloc[0]

# api_url = 'api_url'  # Replace 'api_url' with the actual RatePortal API endpoint
# api_key = 'api_key'  # Replace 'api_key' with your actual RatePortal API key
# rate_portal_api = RatePortalAPI(api_url, api_key)
# payload = rate_portal_api.create_rateportal_payload(row_values)
# response = rate_portal_api.post_rateportal_payload(payload)

# if response is not None:
#     shipment_cost = rate_portal_api.get_shipment_cost_from_response(response)
#     if shipment_cost is not None:
#         print("Shipment Cost:", shipment_cost)
#     else:
#         print("Failed to get shipment cost.")
# else:
#     print("Failed to get API response.")

# df = pd.DataFrame()
# df2 = df.copy()
# df2['d'] = 'shgdu',
# df['s'] = 10,
# #print(df)
# #print(df2)
# df = pd.concat([df,df2],ignore_index=True)
# #print(df)
# #print({df.columns[i] : (1,2)[i] for i in range(len(df.columns)) })
# df3 = pd.DataFrame(data = {df.columns[i] : (1,2)[i] for i in range(len(df.columns)) },columns=df.columns,index = [10])
# df3.loc[1] = (1,2)
# #print(df3)
# df.loc[2] = (1,2)
# df = pd.concat([df,df3],ignore_index=True)
# df4 = pd.DataFrame(data=None,columns=['s','d'])
# df4['s'] = (1,2,3)
# print(df4)
# print(df3)
# df4['d'] = tuple([i if i != 2 else None for i in range(3)])
# df4['c'] = 1/df3['d']
# print(df4)
sdtc = {}
from IPython.display import display
data_unique = data.drop_duplicates(subset=['Source','Destination'],ignore_index=True)
data.iterrows()
for dataslice in data_unique.to_dict(orient='records'):
    dataspec = data.loc[(data['Source'] == dataslice['Source']) & (data['Destination'] == dataslice['Destination']) ]
    sdtc[dataslice['Source'],dataslice['Destination']] = tuple(dataspec.get(['Travel Mode','Carrier']).itertuples(index = False,name = None))

def recurse1()