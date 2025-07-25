from tkinter import Tk  #changed to accept excel sheets
from tkinter.filedialog import askopenfilename
from openpyxl import load_workbook
import datetime
from pandas import Timedelta, Timestamp
import pandas as pd
import numpy as np
import time
import json
Tk().withdraw() 
from tkinter import simpledialog 
root = Tk()
root.withdraw()
instance_name = simpledialog.askstring("Instance Name","enter name:\t\t\t")
inputxl = askopenfilename(title='input')  
outputxl  = askopenfilename(title = 'output')
book = load_workbook(r'{}'.format(outputxl))
data = pd.read_excel(inputxl,sheet_name='Route Information')
order_data = pd.read_excel(inputxl,sheet_name='Order Information')
order_unique = order_data.drop_duplicates(subset=['Ship From','Ship To'],keep='first')
order_unique_Idates = order_data.drop_duplicates(subset=['Ship From','Ship To','Required Delivery Date'],keep='first')
nodes = list(set(data['Source'].unique()).intersection(set(data['Destination'].unique())))
t = []
t_consolidate = []
t_consolidate_0 = []
d_route_unique = {}
d_route = {}
d_consoildate = pd.DataFrame()
d_cost = {}
sdtc = {}
data_unique = data.drop_duplicates(subset=['Source','Destination'],ignore_index=True)
for dataslice in data_unique.to_dict(orient='records'):
    dataspec = data.loc[(data['Source'] == dataslice['Source']) & (data['Destination'] == dataslice['Destination']) ]
    sdtc[dataslice['Source'],dataslice['Destination']] = tuple(dataspec.get(['Travel Mode','Carrier']).itertuples(index = False,name = None))
def connections(dframe : pd.DataFrame,val : str) -> set:
        data_node = dframe.loc[dframe['Source'] == val]
        return set(tuple(i[0] for i in data_node.get(['Destination']).itertuples(index = False,name = None)))
def routeunique():   
    nodeindex = nodes.copy()
    for uniqueslice in order_unique.to_dict(orient='records'):
        for n in range(len(nodes) + 1):
            route(n,pc_new(nodeindex,(uniqueslice['Ship From'],uniqueslice['Ship To'])),uniqueslice['Ship From'],uniqueslice['Ship To'],finaldat = pd.DataFrame(data = None,columns=['Source','Destination','Travel_Mode','Carrier','Container_Size','MaxWeightPerEquipment','VolumetricWeightConversionFactor']))
        temp_list = []
        for data_frame in t:
            temp_list.extend(expand_route(data_frame,sdtc,[data_frame]))
        d_route_unique[(uniqueslice['Ship From'],uniqueslice['Ship To'])] = tuple(temp_list) 
        t.clear()
def calvalue(route_info ,volume_ut : float ,weight_ut : float ,total_ut : float,ratio : float,order_value : float) -> pd.DataFrame:
    #add methods to it with different methods segrigated into different sections
    dict = {}
    if np.isnan(ratio):
        ratio = 0
    #method 1
    dict['FixedFreightCost'] = [(route_info['Fixed Freight Cost']*total_ut)*ratio]
    dict['Port/Airport/RailHandlingCost'] = [(route_info['Port/Airport/Rail Handling Cost']*total_ut)*ratio]
    dict['DocumentationCost'] = [(route_info['Documentation Cost']*total_ut)*ratio]
    dict['EquipmentCost'] = [(route_info['Equipment Cost']*total_ut)*ratio]
    dict['ExtraCost'] = [(route_info['Extra Cost']*total_ut)*ratio]
    #method 2
    dict['VariableFreightCost'] = [route_info['VariableFreightCost']*np.max((np.ceil((volume_ut*route_info['Container Size'])*route_info['VolumetricWeightConversionFactor']),np.ceil(weight_ut*route_info['MaxWeightPerEquipment'])))]
    #method 3
    dict['Bunker/FuelCost'] = [(route_info['Bunker/ Fuel Cost']*total_ut)*ratio]
    dict['WarehouseCost'] = [route_info['Warehouse Cost']*(volume_ut*route_info['Container Size'])*ratio]
    dict['TransitDuty'] = [route_info['Transit Duty']*order_value*ratio]
    dict['Totalcost'] = [(dict['Bunker/FuelCost'][0] + dict['DocumentationCost'][0] + dict['EquipmentCost'][0] + dict['ExtraCost'][0] + dict['FixedFreightCost'][0] + dict['Port/Airport/RailHandlingCost'][0] + dict['TransitDuty'][0] + dict['VariableFreightCost'][0] + dict['WarehouseCost'][0])]
    if dict['Totalcost'][0] < route_info['Minimum Cost']:
        dict['FixedFreightCost'] = [0]
        dict['Port/Airport/RailHandlingCost'] = [0]
        dict['DocumentationCost'] = [0]
        dict['EquipmentCost'] = [0]
        dict['ExtraCost'] = [0]
        dict['VariableFreightCost'] = [0]
        dict['Bunker/FuelCost'] = [0]
        dict['WarehouseCost'] = [0]
        dict['TransitDuty'] = [0]
        dict['Totalcost'] = [route_info['Minimum Cost']*ratio]
    return pd.DataFrame(dict)
def variablefinder(travelmode : str,carrier : str,initial : str,final : str) -> dict:
    variable = {}
    if not ((data['Travel Mode'] == travelmode) & (data['Carrier'] == carrier) & (data['Source']  == initial)  & (data['Destination'] == final)).any():#checks whether a row exist in the dataframe
        variable['transit_time'] = 0
        return variable
    #dataslice is a specific row which contain data specific to (travelmode,initial,final) 
    dataslice = data.loc[(data['Travel Mode'] == travelmode) & (data['Source']  == initial)  & (data['Destination'] == final) & (data['Carrier'] == carrier)]
    variable['custom_clearance_time'] =dataslice['CustomClearance time (hours)'].item()
    variable['Port_Airport_RailHandling_Time'] = dataslice['Port/Airport/Rail Handling time (hours)'].item()
    variable['extra_time'] = dataslice['Extra Time'].item()
    variable['transit_time'] = dataslice['Transit time (hours)'].item()
    variable['MaxVolumePerEquipment'] = dataslice['Container Size'].item()
    variable['Confidence Level'] = dataslice['ConfidenceLevel'].item()
    variable['MaxWeightPerEquipment'] = dataslice['MaxWeightPerEquipment'].item()
    variable['VolumetricWeightConversionFactor'] = dataslice['VolumetricWeightConversionFactor'].item()
    return variable
def variablefinder_for_ETA(initial : str,final : str,travelmode : str,carrier : str) -> dict:
    variables = {}
    dataslice = data.loc[(data['Travel Mode'] == travelmode) & (data['Source']  == initial)  & (data['Destination'] == final) & (data['Carrier'] == carrier)]
    
    Weekday_availability = [dataslice[i].item() for i in ('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday')]
    import numpy as np
    variables['Weekday_Availability'] = Weekday_availability
    if np.isnan(sum(Weekday_availability)):
        variables['Weekday_Availability'] = None
    variables['Custom_Clearance_Time'] =dataslice['CustomClearance time (hours)'].item()
    variables['Port_Airport_RailHandling_Time'] = dataslice['Port/Airport/Rail Handling time (hours)'].item()
    variables['Extra_Time'] = dataslice['Extra Time'].item()
    variables['Transit_Time'] = dataslice['Transit time (hours)'].item()
    variables['Transit_Time_Type'] = dataslice['Transit_Time_Type'].item()
    variables['Holiday_Table'] = dataslice['Holiday_Table'].item()
    if np.isnan(variables['Holiday_Table']):
        variables['Holiday_Table'] = []
    return variables
def pc_new(nid : list,dest : tuple) -> list:
    p_ = nid.copy()
    for i in dest:
        if i not in p_:
            continue
        p_.remove(i)
    return p_
def expand_route(initial_frame : pd.DataFrame , travel_carrier_dict : dict ,frame_list : list) -> list:
    for index in range(len(initial_frame.index)):
        Source = initial_frame.loc[index,'Source']
        Destination = initial_frame.loc[index,'Destination']
        size = len(frame_list)
        for frames_index in range(len(frame_list)):
            for travel_mode,carrier in travel_carrier_dict[(Source,Destination)]:
                variables = variablefinder(travel_mode,carrier,Source,Destination)
                to_append_df = frame_list[frames_index].copy()
                to_append_df.loc[index,'Travel_Mode'] = travel_mode
                to_append_df.loc[index,'Carrier'] = carrier
                to_append_df.loc[index,'Container_Size'] = variables['MaxVolumePerEquipment'] 
                to_append_df.loc[index,'MaxWeightPerEquipment'] = variables['MaxWeightPerEquipment']
                to_append_df.loc[index,'VolumetricWeightConversionFactor'] = variables['VolumetricWeightConversionFactor']
                to_append_df.loc[index,'Confidence_Level'] = variables['Confidence Level']
                frame_list.append(to_append_df.copy())
        del frame_list[:size]
    return frame_list
def route(n : int,nid : list,ini : str ,fin :str ,finaldat=pd.DataFrame(data = None,columns=['Source','Destination','Travel_Mode','Carrier','Container_Size','MaxWeightPerEquipment','VolumetricWeightConversionFactor'])):
        paths = [ [ini,i] for i in connections(data,ini) ]
        new_paths = []
        for i in range(n):
            new_paths.clear()
            for path in paths:
                if not len(connections(data,path[-1]) - set(path)):
                    continue
                if (i == n - 1 and fin not in connections(data,path[-1])):
                    continue
                for node in connections(data,path[-1]) - set(path):
                    if (i == n - 1) and (node != fin):
                        continue
                    if (i == n - 1):
                        path.append(fin)
                    else:
                        path.append(node)
                    new_paths.append(path.copy())
                    path.pop()
            paths = new_paths.copy()
        if n == 0:
            paths = [[ini,fin]] if [ini,fin] in paths else []
        for path in paths:
            for index in range(len(path) - 1):
                finaldat = pd.concat([finaldat,pd.DataFrame(data = {finaldat.columns[i] : (path[index],[path[index + 1]])[i] if i < 2 else None for i in range(len(finaldat.columns))},columns = finaldat.columns,index=[0])],ignore_index = True)
            t.append(finaldat)
            finaldat = pd.DataFrame(columns= finaldat.columns)
def ETA(Routes_Dict : dict):
    from datetime import datetime, timedelta
    class ShippingDatesCalculator:
        def __init__(self,dataframe):
            vars = variablefinder_for_ETA(dataframe['Source'],dataframe['Destination'],dataframe['Travel_Mode'],dataframe['Carrier'])
            self.origin_location = dataframe['Source']
            self.destination_location = dataframe['Destination']
            self.delivery_date = dataframe['Date']
            self.customs_time = vars['Custom_Clearance_Time']
            self.extra_time = vars['Extra_Time']
            self.port_time = vars['Port_Airport_RailHandling_Time']
            self.transit_time = vars['Transit_Time']
            self.transit_time_type = vars['Transit_Time_Type']
            self.weekday_availability = vars['Weekday_Availability']
            self.holiday_table = vars['Holiday_Table']
        def is_holiday(self, date, location):
            if location in self.holiday_table:
                return date.strftime('%Y-%m-%d') in self.holiday_table[location]
            return False
    
        def find_previous_non_holiday(self, date, location):
            while self.is_holiday(date, location):
                date -= timedelta(days=1)
            return date
    
        def calculate_eta(self):
            if self.is_holiday(self.delivery_date, self.destination_location):
                eta = self.find_previous_non_holiday(self.delivery_date, self.destination_location)
            else:
                eta = self.delivery_date
            return eta
    
        def calculate_initial_ship_date(self, eta):
            if self.transit_time_type == 'B':
                day_increment = timedelta(days=1)
                while self.transit_time > 0:
                    if eta.weekday() < 5:  # Monday to Friday
                        self.transit_time -= 1
                    eta -= day_increment
                if not self.is_holiday(eta, self.origin_location):
                    initial_ship_date = eta
                else:
                    initial_ship_date = self.find_previous_non_holiday(eta, self.origin_location)
            elif self.transit_time_type == 'C':
                initial_ship_date = eta - timedelta(days=self.transit_time)
                initial_ship_date = self.find_previous_non_holiday(initial_ship_date, self.origin_location)
            elif self.transit_time_type == 'S':
                day_increment = timedelta(days=1)
                while self.transit_time > 0:
                    if eta.weekday() != 6:  # Not Sunday
                        self.transit_time -= 1
                    eta -= day_increment
                initial_ship_date = self.find_previous_non_holiday(eta, self.origin_location)
            else:
                raise ValueError("Invalid transit time type.")
            return initial_ship_date
    
        def calculate_plan_ship_date(self, initial_ship_date):
            if self.weekday_availability is None:
                # Consider pickupdate availability based on transit time type
                current_date = initial_ship_date
                while self.is_holiday(current_date, self.origin_location):
                    current_date -= timedelta(days=1)
                plan_ship_date = current_date
            else:
                current_date = initial_ship_date
                while not self.weekday_availability[current_date.weekday()] or self.is_holiday(current_date, self.origin_location):
                    current_date -= timedelta(days=1)
                plan_ship_date = current_date
            return plan_ship_date
    
        def calculate_ready_date(self, plan_ship_date):
            current_date = plan_ship_date - timedelta(days=1)
            remaining_time = self.customs_time + self.extra_time + self.port_time
            while remaining_time > 0:
                if current_date.weekday() < 5 and not self.is_holiday(current_date, self.origin_location):
                    remaining_time -= 1
                current_date -= timedelta(days=1)
            ready_date = current_date + timedelta(days=1)
            return ready_date
    
        def calculate_shipping_dates(self):
            eta = self.calculate_eta()
            initial_ship_date = self.calculate_initial_ship_date(eta)
            plan_ship_date = self.calculate_plan_ship_date(initial_ship_date)
            ready_date = self.calculate_ready_date(plan_ship_date)
            return eta, initial_ship_date, plan_ship_date, ready_date
    for Order_Index in Routes_Dict:
        Routes : pd.DataFrame
        for Routes in Routes_Dict[Order_Index]:
            col_list = [None for i in range(len(Routes.index))]
            Routes.insert(11,column = 'ETA',value = col_list)
            Routes.insert(11,column = 'Plan_Ship_Date',value = col_list)
            Routes.insert(11,column = 'Ready_Date',value = col_list)
            for index in range(len(Routes.index) - 1,-1,-1):
                var_dates = ShippingDatesCalculator(Routes.loc[index]) 
                eta, initial_ship_date, plan_ship_date, ready_date = var_dates.calculate_shipping_dates()
                Routes.loc[index,'ETA'] = eta
                Routes.loc[index,'Plan_Ship_Date'] = plan_ship_date
                Routes.loc[index,'Ready_Date'] = ready_date
                Routes.loc[index,'Total_Time'] = Routes.loc[index,'Date'] - ready_date
                #there is a kind of a error i think like the ready date is 2018 and the Date is 2023 check on this
                Routes.loc[index,'Week'] = ready_date.strftime('%Y-%V')
                if index == 0:
                    continue
                Routes.loc[index - 1,'Date'] = ready_date
            t.append(Routes)
        Routes_Dict[Order_Index] = tuple(t)
        t.clear()
def converter(data : dict) -> pd.DataFrame:
    dat = pd.DataFrame()
    for keys in data:
        for frames_index in range(len(data[keys])):
            frames = data[keys][frames_index]
            mute_frame = frames.copy()
            mute_frame['Size'] = frames.shape[0]
            mute_frame['Route_Number'] = frames_index
            mute_frame['Order_index'] = str(keys)
            dat = pd.concat([dat,mute_frame])
    dat.reset_index(inplace = True)
    return dat
def deconverter(data : pd.DataFrame) -> dict[tuple,list[pd.DataFrame]]:
    return_dict = {}
    data.set_index('index',inplace = True)
    order_unique = data.drop_duplicates(subset=['Order_index','Route_Number','DemandPullAhead'],keep='first')[['Order_index','Route_Number','DemandPullAhead']]
    for order_index in list(order_unique['Order_index']):
        return_dict[eval(order_index)] = []
    for legindex,unique_ord in order_unique.iterrows():
        inter1 : pd.DataFrame
        inter1 = data.loc[(data['Order_index'] == unique_ord['Order_index'])&(data['Route_Number'] == unique_ord['Route_Number'])&(data['DemandPullAhead'] == unique_ord['DemandPullAhead'])]
        inter1 = inter1.drop(['Order_index','Route_Number','Size'],axis = 1)
        return_dict[eval(unique_ord['Order_index'])] += [inter1]
    return return_dict
def consolidation_0(zero_routes : pd.DataFrame):#for only the routes having zero intermidiates, done in DemandPullAhead method
    one_sort = zero_routes.sort_values('Date',ignore_index=True)
    one_sort['Consolid_Id'] = None
    one_sort['total_Volumn_Ut'] = None
    one_sort['total_Weight_Ut'] = None
    one_sort['DemandPullAhead'] = None
    current_row_index = 0
    pullahead = eval(one_sort.loc[current_row_index,'Order_index'])[-1]
    for slice in range(one_sort.shape[0]):
        current_date = one_sort.loc[current_row_index,'Date']
        current_row_volumn_ut = one_sort.loc[current_row_index,'Volume_Utilization']
        current_row_weight_ut = one_sort.loc[current_row_index,'Weight_Utilitation']
        added_volumn_ut = current_row_volumn_ut
        added_weight_ut = current_row_weight_ut
        if (one_sort.loc[slice,'Weight_Utilitation'] == 0 and one_sort.loc[slice,'Volume_Utilization'] == 0) or current_row_index == slice:#checks if the next routes is more that pullahead days from the present route #and one_sort.loc[slice,'Date'] <start is experimental 
            continue
        if not (one_sort.loc[slice,'Date'] <= current_date + datetime.timedelta(days=pullahead)):
            current_row_index = slice
            continue
        variable_row_volumn_ut = one_sort.loc[slice,'Volume_Utilization']
        variable_row_weight_ut = one_sort.loc[slice,'Weight_Utilitation'] 
        # one_sort.loc[slice,'Volume_Utilization'] = 0
        # one_sort.loc[slice,'Weight_Utilitation'] = 0
        added_volumn_ut += variable_row_volumn_ut 
        added_weight_ut += variable_row_weight_ut 
        condition = (bool(added_volumn_ut >= np.ceil(current_row_volumn_ut)) and ( np.ceil(current_row_volumn_ut) != 0),bool(added_weight_ut >= np.ceil(current_row_weight_ut)) and (np.ceil(current_row_weight_ut) != 0))
        if condition == (False,False):
            one_sort.loc[current_row_index,'Volume_Utilization'] = added_volumn_ut
            one_sort.loc[current_row_index,'Weight_Utilitation'] = added_weight_ut
            one_sort.loc[slice,'Volume_Utilization'] = 0
            one_sort.loc[slice,'Weight_Utilitation'] = 0
        elif condition == (True,False):
            ratio = np.divide(np.ceil(current_row_volumn_ut)-current_row_volumn_ut,variable_row_volumn_ut)
            transfer_variable_row_weight_ut = np.multiply(ratio,variable_row_weight_ut)
            one_sort.loc[current_row_index,'Volume_Utilization'] = np.ceil(current_row_volumn_ut)
            one_sort.loc[slice,'Volume_Utilization'] = added_volumn_ut - np.ceil(current_row_volumn_ut)
            one_sort.loc[current_row_index,'Weight_Utilitation'] = added_weight_ut - variable_row_weight_ut + transfer_variable_row_weight_ut
            one_sort.loc[slice,'Weight_Utilitation'] = variable_row_weight_ut - transfer_variable_row_weight_ut
            current_row_index = slice
        elif condition == (False,True):
            ratio = np.divide(np.ceil(current_row_weight_ut) - current_row_weight_ut, variable_row_weight_ut)
            transfer_variable_row_volumn_ut = np.multiply(ratio,variable_row_volumn_ut)
            one_sort.loc[current_row_index,'Weight_Utilitation'] = np.ceil(current_row_weight_ut)
            one_sort.loc[slice,'Weight_Utilitation'] = added_weight_ut - np.ceil(current_row_weight_ut) 
            one_sort.loc[current_row_index,'Volume_Utilization'] = added_volumn_ut - variable_row_volumn_ut + transfer_variable_row_volumn_ut
            one_sort.loc[slice,'Volume_Utilization'] = variable_row_volumn_ut - transfer_variable_row_volumn_ut
            current_row_index =slice
        elif condition == (True,True):
            ratio_V = np.divide(np.ceil(current_row_volumn_ut) - current_row_volumn_ut, variable_row_volumn_ut)
            ratio_W = np.divide(np.ceil(current_row_weight_ut) - current_row_weight_ut, variable_row_weight_ut)
            if ratio_V <= ratio_W:
                max_current_row_ut = np.ceil(current_row_volumn_ut)
                transfer_variable_row_weight_ut = np.multiply(ratio_V,variable_row_weight_ut)
                one_sort.loc[current_row_index,'Volume_Utilization'] = max_current_row_ut
                one_sort.loc[slice,'Volume_Utilization'] = added_volumn_ut - max_current_row_ut
                one_sort.loc[current_row_index,'Weight_Utilitation'] = added_weight_ut - variable_row_weight_ut + transfer_variable_row_weight_ut
                one_sort.loc[slice,'Weight_Utilitation'] = variable_row_weight_ut - transfer_variable_row_weight_ut
                current_row_index = slice
            else:
                max_current_row_ut = np.ceil(current_row_weight_ut)
                transfer_variable_row_volumn_ut = np.multiply(ratio_W,variable_row_volumn_ut)
                one_sort.loc[current_row_index,'Weight_Utilitation'] = max_current_row_ut
                one_sort.loc[slice,'Weight_Utilitation'] = added_weight_ut - max_current_row_ut
                one_sort.loc[current_row_index,'Volume_Utilization'] = added_volumn_ut - variable_row_volumn_ut + transfer_variable_row_volumn_ut
                one_sort.loc[slice,'Volume_Utilization'] = variable_row_volumn_ut - transfer_variable_row_volumn_ut
                current_row_index =slice
    one_sort = one_sort[(one_sort.Weight_Utilitation != 0) & (one_sort.Volume_Utilization != 0)]
    one_sort.loc[:,'Consolid_Id'] = [hex(hash(x)) for x in tuple(one_sort.itertuples(name = None))]
    one_sort.loc[:,'total_Volumn_Ut'] = one_sort['Volume_Utilization']
    one_sort.loc[:,'total_Weight_Ut'] = one_sort['Weight_Utilitation']
    one_sort.loc[:,'DemandPullAhead'] = [True]*one_sort.shape[0]
    return one_sort
def consoildation(go_through : pd.DataFrame,route_info : pd.DataFrame) -> pd.DataFrame:
    #think of a new way since the constrains have beed lifted so we don't need to send the index of each leg to the next function just total untilization is enough
    lookup = route_info.copy()
    lookup['Consolid_Id'] = None
    lookup['total_Volumn_Ut'] = None
    lookup['total_Weight_Ut'] = None
    for legs in go_through.to_dict(orient='records'):
        inter_df = lookup.loc[(lookup['Source'] == legs['Source']) & (lookup['Destination'] == legs['Destination']) & (lookup['Travel_Mode'] == legs['Travel Mode']) & (lookup['Carrier'] == legs['Carrier'])]
        weeks = list(inter_df['Week'].unique())
        for week_no in weeks:
            inter_df2 = inter_df.loc[(inter_df['Week'] == week_no)]
            inter_df2.loc[:,'Consolid_Id'] = [hex(hash(legs['Source'] + legs['Destination'] + legs['Travel Mode'] + legs['Carrier'] + week_no ))]*(len(inter_df2))
            inter_df2.loc[:,'total_Volumn_Ut'] = [inter_df2['Volume_Utilization'].sum()]*(len(inter_df2))
            inter_df2.loc[:,'total_Weight_Ut'] = [inter_df2['Weight_Utilitation'].sum()]*(len(inter_df2))
            lookup.update(inter_df2)
    lookup['DemandPullAhead'] = False
    return lookup
def consolidate_Routes(routes : dict,leg_info : dict):
    global d_consoildate
    one_stops : pd.DataFrame
    all_stops = converter(routes)
    consolid1 = consoildation(leg_info,all_stops)
    one_stops = all_stops.loc[(all_stops['Size'] == 1)]
    routes_unique = set(one_stops.get(['Source','Destination','Travel_Mode','Carrier']).itertuples(index = False,name = None))
    consoild2 = pd.DataFrame()
    for route_index in routes_unique:
        one_stops_route_unique = one_stops.loc[(one_stops['Source'] == route_index[0]) & (one_stops['Destination'] == route_index[1]) & (one_stops['Travel_Mode'] == route_index[2]) & (one_stops['Carrier'] == route_index[3])]
        one_stops_route_unique = one_stops_route_unique.reset_index(drop = True)
        consoild2 = pd.concat([consoild2,consolidation_0(one_stops_route_unique)],ignore_index=True)
    consoild2.set_index(pd.Series([0 for i in range(consoild2.shape[0])]))
    consolid3 = pd.concat([consolid1,consoild2])
    # with pd.ExcelWriter(outputxl, engine='openpyxl', mode='a') as writer:            
    #     consolid3.to_excel(writer,sheet_name='CONSOLIDS')
    d_consoildate = consolid3
def cost(route_dict_con : pd.DataFrame):
    global d_cost
    #add if api cloumn is true in future and do the pullahead into the excel itself as a column (must)
    orderindex : tuple
    cost = pd.DataFrame()
    for index,legdict in route_dict_con.iterrows():
        leg_pd = pd.DataFrame(legdict.to_dict(),index = [index])
        volumn_ut = legdict['total_Volumn_Ut']
        weight_ut = legdict['total_Weight_Ut']
        total_volumn_ut = np.ceil(volumn_ut)
        total_weight_ut = np.ceil(weight_ut)
        total_ut = np.max((total_volumn_ut,total_weight_ut))
        orderindex = eval(legdict['Order_index'])
        if total_ut == total_weight_ut:
            ratio = np.divide(legdict['Weight_Utilitation'],weight_ut)
            route_index = data.index[((data['Source'] == legdict['Source']) & (data['Destination'] == legdict['Destination']) & (data['Travel Mode'] == legdict['Travel_Mode']) & (data['Carrier'] == legdict['Carrier']))]
            route_ = data.loc[route_index].to_dict('records')
            cost_pd = calvalue(route_[0],legdict['Volume_Utilization'],legdict['Weight_Utilitation'],total_ut,ratio,orderindex[1])
        else:
            ratio = np.divide(legdict['Volume_Utilization'],volumn_ut)
            route_index = data.index[((data['Source'] == legdict['Source']) & (data['Destination'] == legdict['Destination']) & (data['Travel Mode'] == legdict['Travel_Mode']) & (data['Carrier'] == legdict['Carrier']))]
            route_ = data.loc[route_index].to_dict('records')
            cost_pd = calvalue(route_[0],legdict['Volume_Utilization'],legdict['Weight_Utilitation'],total_ut,ratio,orderindex[1])
        legdict = leg_pd.to_dict(orient = 'records')[0]
        legdict.update(cost_pd.to_dict(orient= 'records')[0])
        routenew_pd = pd.DataFrame(legdict,index = [index])
        cost = pd.concat([cost,routenew_pd])
    # with pd.ExcelWriter(outputxl,engine='openpyxl',mode = 'a') as writer:
    #     cost.to_excel(writer,sheet_name="leg wise cost")
    d_cost = deconverter(cost)
def display(dictionary : dict[tuple,list[pd.DataFrame]],routedict : dict[tuple,list[pd.DataFrame]]):
    datafinal = pd.DataFrame(columns=['Instance Name','Orderno','Source','Destination','Volume','Weight','Legs','Intermidiates','Travel_Modes','Carriers','Time','Fixed Freight Cost','Port/Airport/Rail Handling Cost','Documentation Cost','Equipment Cost','Extra Cost','VariableFreightCost','Bunker/ Fuel Cost','Warehouse Cost','Transit Duty','Total Cost','OrderDate','ETA','Delivary_Date','Confidence Level','Confidence Level Rank','DemandPullAhead'])
    datafinal_route = pd.DataFrame(columns=['Instance Name','Orderno','Source','Destination','Volume','Weight','Legs','Intermidiates','Travel_Mode','Carrier','Container_Size','MaxWeightPerEquipment','VolumetricWeightConversionFactor','Weight_Utilitation','Volume_Utilization','order_value','Total_Time','Ready_Date','Plan_Ship_Date','ETA','Date','Week'])
    for orderindex in dictionary:
        for routes_df in dictionary[orderindex]:
            col_to_index = dict(zip(routes_df.columns,range(len(routes_df.columns))))
            routes = tuple(routes_df.itertuples(index=False,name=None))
            finaldat = {}
            finaldat['Instance Name'] = instance_name
            finaldat['Orderno'] = orderindex[0]
            finaldat['Source'] = routes[0][col_to_index['Source']]
            finaldat['Destination'] = routes[-1][col_to_index['Destination']]
            finaldat['Volume'] = routes[0][col_to_index['Container_Size']]*routes[0][col_to_index['Volume_Utilization']]
            finaldat['Weight'] = routes[0][col_to_index['MaxWeightPerEquipment']]*routes[0][col_to_index['Weight_Utilitation']]
            finaldat['Intermidiates'] = ''
            finaldat['Legs'] = len(routes) - 1
            finaldat['Travel_Modes'] = ''
            finaldat['Carriers'] = ''
            finaldat['Time'] = datetime.timedelta()
            finaldat['OrderDate'] = routes[0][col_to_index['Ready_Date']]
            finaldat['ETA'] = routes[-1][col_to_index['ETA']]
            finaldat['Delivary_Date'] = orderindex[-2]
            finaldat['DemandPullAhead'] = routes[0][col_to_index['DemandPullAhead']]
            finaldat['Fixed Freight Cost'] = 0
            finaldat['Port/Airport/Rail Handling Cost'] = 0
            finaldat['Documentation Cost'] = 0
            finaldat['Equipment Cost'] = 0
            finaldat['Extra Cost'] = 0
            finaldat['VariableFreightCost'] = 0
            finaldat['Bunker/ Fuel Cost'] = 0
            finaldat['Warehouse Cost'] = 0
            finaldat['Transit Duty'] = 0
            finaldat['Total Cost'] = 0
            finaldat['Confidence Level'] = 1
            for routeslice_i in range(0,len(routes)):
                finaldat['Intermidiates'] += ' ---> ' + routes[routeslice_i][col_to_index['Destination']]
                finaldat['Travel_Modes'] += routes[routeslice_i][col_to_index['Travel_Mode']] + ','
                finaldat['Carriers'] +=  routes[routeslice_i][col_to_index['Carrier']] + ',' 
                finaldat['Time'] += routes[routeslice_i][col_to_index['Total_Time']]
                finaldat['Fixed Freight Cost'] += routes[routeslice_i][col_to_index['FixedFreightCost']]
                finaldat['Port/Airport/Rail Handling Cost'] += routes[routeslice_i][col_to_index['Port/Airport/RailHandlingCost']]
                finaldat['Documentation Cost'] += routes[routeslice_i][col_to_index['DocumentationCost']]
                finaldat['Equipment Cost'] += routes[routeslice_i][col_to_index['EquipmentCost']]
                finaldat['Extra Cost'] += routes[routeslice_i][col_to_index['ExtraCost']]
                finaldat['VariableFreightCost'] += routes[routeslice_i][col_to_index['VariableFreightCost']]
                finaldat['Bunker/ Fuel Cost'] += routes[routeslice_i][col_to_index['Bunker/FuelCost']]
                finaldat['Warehouse Cost'] += routes[routeslice_i][col_to_index['WarehouseCost']]
                finaldat['Transit Duty'] += routes[routeslice_i][col_to_index['TransitDuty']]
                finaldat['Total Cost'] += routes[routeslice_i][col_to_index['Totalcost']]
                finaldat['Confidence Level'] *= routes[routeslice_i][col_to_index['Confidence_Level']]
            finaldat['Intermidiates'] = finaldat['Intermidiates'].rstrip(finaldat['Destination']).rstrip("---> ").lstrip(' --->')
            finaldat['Carriers'] = finaldat['Carriers'][:-1]
            finaldat['Travel_Modes'] = finaldat['Travel_Modes'][:-1] 
            datafinal.loc[len(datafinal.index)] = finaldat
    for Source_destination in order_unique_Idates.to_dict(orient='records'):
        hold_df1 : pd.DataFrame
        hold_df2 : pd.DataFrame
        hold_df : pd.DataFrame
        hold_df = datafinal.loc[(datafinal['Source'] == Source_destination['Ship From']) & (datafinal['Destination'] == Source_destination['Ship To']) & (datafinal['Delivary_Date'] == Source_destination['Required Delivery Date'])]
        hold_df1 = hold_df.loc[(hold_df['DemandPullAhead'])]
        hold_df2 = hold_df.loc[(hold_df['DemandPullAhead'] == False)]
        hold_df1 = hold_df1.sort_values('Confidence Level')
        hold_df2 = hold_df2.sort_values('Confidence Level')
        hold_df1['Confidence Level Rank'] = hold_df1.loc[:,'Confidence Level']
        hold_df2['Confidence Level Rank'] = hold_df2.loc[:,'Confidence Level']
        Confidence_Level_Unique = hold_df1.loc[:,'Confidence Level Rank'].unique()
        Confidence_Level_Unique.sort()
        Confidence_Level_rankDict = {Confidence_Level_Unique[i] : Confidence_Level_Unique.size - i for i in range(Confidence_Level_Unique.size)}
        hold_df1 = hold_df1.replace({"Confidence Level Rank" : Confidence_Level_rankDict})
        Confidence_Level_Unique = hold_df2.loc[:,'Confidence Level Rank'].unique()
        Confidence_Level_Unique.sort()
        Confidence_Level_rankDict = {Confidence_Level_Unique[i] : Confidence_Level_Unique.size - i for i in range(Confidence_Level_Unique.size)}
        hold_df2 = hold_df2.replace({"Confidence Level Rank" : Confidence_Level_rankDict})
        datafinal.update(hold_df1)
        datafinal.update(hold_df2)
    with pd.ExcelWriter(outputxl, engine='openpyxl', mode='a') as writer:            
        datafinal.to_excel(writer,sheet_name='cost')
#................................................................................
print(time.localtime())
nodeindex = nodes.copy()
routeunique()
print(time.localtime())
# for i in d_route_unique:
#     print(i)
#     for j in d_route_unique[i]:
#         print(j)
#         print()
#     print('\n\n\n')
for inputslice in order_data.to_dict(orient='records'):
    worktuple = d_route_unique[(inputslice['Ship From'],inputslice['Ship To'])] 
    datframe : pd.DataFrame
    for datframe in worktuple:
        rows = len(datframe.index)#'Weight_Utilitation','Volume_Utilization','order_value','Total_Time','Date','Week'
        datframe['Weight_Utilitation'] = inputslice['Weight (KG)']/datframe['MaxWeightPerEquipment']
        datframe['Volume_Utilization'] = inputslice['Volume']/datframe['Container_Size']
        datframe['order_value'] = [inputslice['Order Value'] for i in range(rows)]
        datframe['Total_Time'] = [Timedelta(0) for i in range(rows)]
        datframe['Date'] = [inputslice['Required Delivery Date'] for i in range(rows)]
        datframe['Week'] = [datframe['Date'].to_list()[i].strftime('%Y-%V') for i in range(rows)]
        t.append(datframe.copy())
    d_route[(inputslice['Order Number'],inputslice['Order Value'],inputslice['Weight (KG)'],inputslice['Volume'],inputslice['Required Delivery Date'],inputslice['PullAheadDays'])] = tuple(t)
    t.clear()
print(time.localtime())
ETA(d_route)
print(time.localtime())
# for i in d_route:
#     print(i)
#     for j in d_route[i]:
#         for k in j:
#             print(k)
#         print('\n')
consolidate_Routes(d_route,data)
print(time.localtime())
# for i in d_consoildate:
#     print(i)
#     for j in d_consoildate[i]:
#         print(j.to_dict())
#         print('\n')
#     print('\n')
cost(d_consoildate)
# for i in d_cost:
#     print(i)
#     for j in d_cost[i]:
#         print(j)
#         print('\n')
#     print('\n')
print(time.localtime())
display(d_cost,d_route)
print(time.localtime())
