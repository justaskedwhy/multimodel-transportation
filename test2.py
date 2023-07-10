from tkinter import Tk  #changed to accept excel sheets
from tkinter.filedialog import askopenfilename
from openpyxl import load_workbook
import datetime
from pandas import Timestamp
import pandas as pd
import numpy as np
Tk().withdraw() 
inputxl = askopenfilename(title='input')  
outputxl  = askopenfilename(title = 'output')
book = load_workbook(r'{}'.format(outputxl))
data = pd.read_excel(inputxl,sheet_name='Route Information')
order_data = pd.read_excel(inputxl,sheet_name='Order Information')
nodes = pd.unique(data[['Source','Destination']].values.ravel('k')).tolist()
travelmodes = data['Travel Mode'].unique().tolist()   #the excel has some changes to the names of the columns
carriermodes = data['Carrier'].unique().tolist()
t = []
t_consolidate = []
t_consolidate_0 = []
d_route = {}
d_consoildate = {}
d_cost = {}
def calvalue(route_info,volume_ut,weight_ut,total_ut,ratio,order_value):
    #add methods to it with different methods segrigated into different sections
    dict = {}
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
    return pd.DataFrame(dict)
def variablefinder(travelmode,carrier,initial,final):
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
    variable['ConfidenceLevel'] = dataslice['ConfidenceLevel'].item()
    variable['MaxWeightPerEquipment'] = dataslice['MaxWeightPerEquipment'].item()
    variable['VolumetricWeightConversionFactor'] = dataslice['VolumetricWeightConversionFactor'].item()
    return variable
def pc_new(nid,dest):
    p_ = nid.copy()
    for i in dest:
        p_.remove(i)
    return p_
def route(n,nid,date,ini,fin,volume,weight,order_value,finaldat=()):#finaldat is in tuple because of the problems with list(local and globle variable problems)
        if n == 0:
            for travelelement in travelmodes:
                for carrierelement in carriermodes:
                    variable = variablefinder(travelelement,carrierelement,ini,fin)
                    if  variable['transit_time']:
                        destination = fin
                        source = ini
                        container_size = variable['MaxVolumePerEquipment']
                        MaxWeightPerEquipment = variable['MaxWeightPerEquipment']
                        VolumetricWeightConversionFactor = variable['VolumetricWeightConversionFactor']
                        Weight_Utilitation = weight/MaxWeightPerEquipment
                        Volume_Utilization = volume/container_size
                        total_time = variable['custom_clearance_time'] + variable['Port_Airport_RailHandling_Time'] + variable['extra_time'] + variable['transit_time']
                        date_new = date - datetime.timedelta(hours=total_time) #subtracts time by some hours
                        week_new = date_new.strftime('%Y-%V')#in the format YYYY-WW eg. 2023-06
                        finaldat = source,destination,travelelement,carrierelement,container_size,MaxWeightPerEquipment,VolumetricWeightConversionFactor,Weight_Utilitation,Volume_Utilization,order_value,total_time,date_new,week_new,
                        t.append((finaldat,))
            return
        if n == 1:
            pt = list(finaldat)
            for intermediate in nid:
                for travelelement in travelmodes:
                    for carrierelement in carriermodes:
                        variable = variablefinder(travelelement,carrierelement,intermediate,fin)
                        if variable['transit_time']:
                            destination = fin
                            source = intermediate
                            container_size = variable['MaxVolumePerEquipment']
                            MaxWeightPerEquipment = variable['MaxWeightPerEquipment']
                            VolumetricWeightConversionFactor = variable['VolumetricWeightConversionFactor']
                            Weight_Utilitation = weight/MaxWeightPerEquipment
                            Volume_Utilization = volume/container_size
                            total_time = variable['custom_clearance_time'] + variable['Port_Airport_RailHandling_Time'] + variable['extra_time'] + variable['transit_time']
                            date_new = date - datetime.timedelta(hours=total_time)
                            week_new = date_new.strftime('%Y-%V')
                            pt.append((source,destination,travelelement,carrierelement,container_size,MaxWeightPerEquipment,VolumetricWeightConversionFactor,Weight_Utilitation,Volume_Utilization,order_value,total_time,date_new,week_new))
                            for travelelement2 in travelmodes:
                                for carrierelement2 in carriermodes:
                                    variable2 = variablefinder(travelelement2,carrierelement2,ini,intermediate)
                                    if variable2['transit_time']:
                                        destination = intermediate
                                        source = ini
                                        container_size = variable2['MaxVolumePerEquipment']
                                        MaxWeightPerEquipment = variable['MaxWeightPerEquipment']
                                        VolumetricWeightConversionFactor = variable['VolumetricWeightConversionFactor']
                                        Weight_Utilitation = weight/MaxWeightPerEquipment
                                        Volume_Utilization = volume/container_size
                                        total_time = variable2['custom_clearance_time'] + variable2['Port_Airport_RailHandling_Time'] + variable2['extra_time'] + variable2['transit_time']
                                        date_new_2 = date_new - datetime.timedelta(hours=total_time)
                                        week_new_2 = date_new_2.strftime('%Y-%V')
                                        pt.append((source,destination,travelelement2,carrierelement2,container_size,MaxWeightPerEquipment,VolumetricWeightConversionFactor,Weight_Utilitation,Volume_Utilization,order_value,total_time,date_new_2,week_new_2))
                                        t.append(tuple(pt[::-1]))#to change the order from last to first to first to last.
                                        pt.pop()#avoids duplications
                            pt.pop()
        elif n > 1 :
            for intermediate in nid:
                for travelelement in travelmodes:
                    for carrierelement in carriermodes:
                        variable = variablefinder(travelelement,carrierelement,intermediate,fin)
                        if variable['transit_time']:
                            pt = list(finaldat)
                            destination = fin
                            source = intermediate
                            container_size = variable['MaxVolumePerEquipment']
                            MaxWeightPerEquipment = variable['MaxWeightPerEquipment']
                            VolumetricWeightConversionFactor = variable['VolumetricWeightConversionFactor']
                            Weight_Utilitation = weight/MaxWeightPerEquipment
                            Volume_Utilization = volume/container_size
                            total_time = variable['custom_clearance_time'] + variable['Port_Airport_RailHandling_Time'] + variable['extra_time'] + variable['transit_time']
                            date_new = date - datetime.timedelta(hours=total_time)
                            week_new = date_new.strftime('%Y-%V')
                            pt.append((source,destination,travelelement,carrierelement,container_size,MaxWeightPerEquipment,VolumetricWeightConversionFactor,Weight_Utilitation,Volume_Utilization,order_value,total_time,date_new,week_new))
                            route(n-1,pc_new(nid.copy(),(intermediate,)),date_new,ini,intermediate,volume,weight,order_value,tuple(pt))
def consolidation_0(zero_routes):#for only the routes having zero intermidiates, done in DemandPullAhead method
    if len(zero_routes) == 0:
        return#avoids error
    one_stop_df = pd.DataFrame(zero_routes,columns=['Order','Source','Destination','Travel_Mode','Carrier','Container_Size','MaxWeightPerEquipment','VolumetricWeightConversionFactor','Weight_Utilitation','Volume_Utilization','order_value','Total_Time','Date','Week'])
    one_sort = one_stop_df.sort_values('Date',ignore_index=True)
    current_row_index = 0
    pullahead = eval(one_sort.loc[current_row_index,'Order'])[-1]
    added_volumn_ut = one_sort.loc[current_row_index,'Volume_Utilization']
    added_weight_ut = one_sort.loc[current_row_index,'Weight_Utilitation']
    for slice in range(one_sort.shape[0]):
        current_date = one_sort.loc[current_row_index,'Date']
        current_row_volumn_ut = one_sort.loc[current_row_index,'Volume_Utilization']
        current_row_weight_ut = one_sort.loc[current_row_index,'Weight_Utilitation']
        if (one_sort.loc[slice,'Weight_Utilitation'] == 0 and one_sort.loc[slice,'Volume_Utilization']) or current_row_index == slice:#checks if the next routes is more that pullahead days from the present route #and one_sort.loc[slice,'Date'] <start is experimental 
            continue
        if not (one_sort.loc[slice,'Date'] <= current_date + datetime.timedelta(days=pullahead)):
            one_sort.loc[current_row_index,'Volume_Utilization'] = added_volumn_ut
            one_sort.loc[current_row_index,'Weight_Utilitation'] = added_weight_ut
            added_volumn_ut = one_sort.loc[slice,'Volume_Utilization']
            added_weight_ut = one_sort.loc[slice,'Weight_Utilitation']
            current_row_index = slice
            continue
        variable_row_volumn_ut = one_sort.loc[slice,'Volume_Utilization']
        variable_row_weight_ut = one_sort.loc[slice,'Weight_Utilitation']
        one_sort.loc[slice,'Volume_Utilization'] = 0
        one_sort.loc[slice,'Weight_Utilitation'] = 0
        added_volumn_ut += variable_row_volumn_ut 
        added_weight_ut += variable_row_weight_ut 
        condition = (bool(added_volumn_ut >= np.ceil(current_row_volumn_ut)),bool(added_weight_ut >= np.ceil(current_row_weight_ut)))
        match condition:
            case (True,False):
                ratio = np.divide(np.ceil(current_row_volumn_ut)-added_volumn_ut+variable_row_volumn_ut,variable_row_volumn_ut)
                transfer_variable_row_weight_ut = np.multiply(ratio,variable_row_weight_ut)
                one_sort.loc[current_row_index,'Volume_Utilization'] = np.ceil(current_row_volumn_ut)
                one_sort.loc[slice,'Volume_Utilization'] = added_volumn_ut - np.ceil(current_row_volumn_ut)
                one_sort.loc[current_row_index,'Weight_Utilitation'] = added_weight_ut - variable_row_weight_ut + transfer_variable_row_weight_ut
                one_sort.loc[slice,'Weight_Utilitation'] = variable_row_weight_ut - transfer_variable_row_weight_ut
                added_volumn_ut = added_volumn_ut - np.ceil(current_row_volumn_ut)
                added_weight_ut = variable_row_weight_ut - transfer_variable_row_weight_ut
                current_row_index = slice
            case (False,True):
                ratio = np.divide(np.ceil(current_row_weight_ut) - added_weight_ut + variable_row_weight_ut, variable_row_weight_ut)
                transfer_variable_row_volumn_ut = np.multiply(ratio,variable_row_volumn_ut)
                one_sort.loc[current_row_index,'Weight_Utilitation'] = np.ceil(current_row_weight_ut)
                one_sort.loc[slice,'Weight_Utilitation'] = added_weight_ut - np.ceil(current_row_weight_ut) 
                one_sort.loc[current_row_index,'Volume_Utilization'] = added_volumn_ut - variable_row_volumn_ut + transfer_variable_row_volumn_ut
                one_sort.loc[slice,'Volume_Utilization'] = variable_row_volumn_ut - transfer_variable_row_volumn_ut
                added_weight_ut = added_weight_ut - np.ceil(current_row_weight_ut) 
                added_volumn_ut = variable_row_volumn_ut - transfer_variable_row_volumn_ut
                current_row_index =slice
            case (True,True):
                ratio_V = np.divide(np.ceil(current_row_volumn_ut) - added_volumn_ut + variable_row_volumn_ut, variable_row_volumn_ut)
                ratio_W = np.divide(np.ceil(current_row_weight_ut) - added_weight_ut + variable_row_weight_ut, variable_row_weight_ut)
                if ratio_V <= ratio_W:
                    transfer_variable_row_weight_ut = np.multiply(ratio_V,variable_row_weight_ut)
                    one_sort.loc[current_row_index,'Volume_Utilization'] = np.ceil(current_row_volumn_ut)
                    one_sort.loc[slice,'Volume_Utilization'] = added_volumn_ut - np.ceil(current_row_volumn_ut)
                    one_sort.loc[current_row_index,'Weight_Utilitation'] = added_weight_ut - variable_row_weight_ut + transfer_variable_row_weight_ut
                    one_sort.loc[slice,'Weight_Utilitation'] = variable_row_weight_ut - transfer_variable_row_weight_ut
                    added_volumn_ut = added_volumn_ut - np.ceil(current_row_volumn_ut)
                    added_weight_ut = variable_row_weight_ut - transfer_variable_row_weight_ut
                    current_row_index = slice
                else:
                    transfer_variable_row_volumn_ut = np.multiply(ratio_W,variable_row_volumn_ut)
                    one_sort.loc[current_row_index,'Weight_Utilitation'] = np.ceil(current_row_weight_ut)
                    one_sort.loc[slice,'Weight_Utilitation'] = added_weight_ut - np.ceil(current_row_weight_ut) 
                    one_sort.loc[current_row_index,'Volume_Utilization'] = added_volumn_ut - variable_row_volumn_ut + transfer_variable_row_volumn_ut
                    one_sort.loc[slice,'Volume_Utilization'] = variable_row_volumn_ut - transfer_variable_row_volumn_ut
                    added_weight_ut = added_weight_ut - np.ceil(current_row_weight_ut) 
                    added_volumn_ut = variable_row_volumn_ut - transfer_variable_row_volumn_ut
                    current_row_index =slice
        one_sort.to_csv(r"C:\Users\vjr\Desktop\eqn.txt",sep='\t',mode='a')
    else:
        one_sort.loc[slice,'Volume_Utilization'] = added_volumn_ut
        one_sort.loc[slice,'Weight_Utilitation'] = added_weight_ut
    one_sort['DemandPullAhead'] = True
    for slice in range(one_sort.shape[0]):
        d_one_sort = one_sort.loc[slice].to_dict()
        t_consolidate_0.append((tuple(d_one_sort.values())[0],(tuple(d_one_sort.values())[1:],)))
def consoildation(orderno,route,routedictionary,consolidant):
    fol = False
    pt = consolidant.copy()
    to_consolidate_df = pd.DataFrame(route,columns=['Source','Destination','Travel_Mode','Carrier','Container_Size','MWpE','VWcF','Weight_Utilitation','Volume_Utilization','order_value','Total_Time','Date','Week'])#dataframes are easy to work with
    for orderindex in routedictionary:
        if orderindex == orderno:
            continue
        routetuple = routedictionary[orderindex]
        for root in routetuple:
            if fol:#checks whether the order index has already used more than one time
                fol = False
                break
            from_df = pd.DataFrame(root,columns=['Source','Destination','Travel_Mode','Carrier','Container_Size','MWpE','VWcF','Weight_Utilitation','Volume_Utilization','order_value','Total_Time','Date','Week'])
            equaldf = to_consolidate_df.merge(from_df,on=['Source','Destination','Travel_Mode','Carrier','Week'],suffixes=('', '_DROP')).filter(regex='^(?!.*_DROP)')#finds commen rows to both dataframe
            for i in range(len(equaldf)):
                fol = True
                equalrow = equaldf.loc[i]
                index = pt.index[(consolidant['Source'] == equalrow['Source']) & (consolidant['Destination'] == equalrow['Destination']) & (consolidant['Travel_Mode'] == equalrow['Travel_Mode']) & (consolidant['Carrier'] == equalrow['Carrier']) & (consolidant['Week'] == equalrow['Week'])]
                pt.loc[index,'Consolidant'] += str((orderindex,routetuple.index(root))) + ','#adds the route index to the column consolidation 
    consolidant_tuple = tuple(pt.itertuples(index=False,name=None))
    t_consolidate.append(consolidant_tuple)
def consolidate_Routes(routes):
    one_stop = {}
    x = ()
    for orderindex in routes:
        for route in routes[orderindex]:
            if len(route) == 1:
                x = one_stop.keys()
                if not (route[0][:4]) in x:#( source,destination, travel mode, carrier)
                    one_stop[route[0][:4]] = []
                one_stop[(route[0][:4])].append(('{}'.format((orderindex)),) + (route[0]))#('orderindex',....,...,..)
            df = pd.DataFrame(route,columns=['Source','Destination','Travel_Mode','Carrier','Container_Size','MWpE','VWcF','Weight_Utilitation','Volume_Utilization','order_value','Total_Time','Date','Week'])
            df['Consolidant'] = ''
            df['DemandPullAhead'] = False
            #used in checking whether done through DemandPullAhead method
            consoildation(orderindex,route,routes,df)
        d_consoildate[orderindex] = tuple(t_consolidate)
        t_consolidate.clear()
    for one_stop_keys in one_stop:
        consolidation_0(tuple(one_stop[one_stop_keys]))
        for i in t_consolidate_0:
            d_consoildate[eval(i[0])] += (i[1],)
        t_consolidate_0.clear()
def cost(route_dict_con,route_dict):
    #add if api cloumn is true in future and do the pullahead into the excel itself as a column (must)
    for orderindex in route_dict_con:
        cost_tuple = []
        for routes in route_dict_con[orderindex]:
            costslice = ()
            for routeslice in routes:
                if routeslice[-1]:
                    routeslice_pd = pd.DataFrame((routeslice,),columns=['Source','Destination','Travel_Mode','Carrier','Container_Size','MWpE','VWcF','Weight_Utilitation','Volume_Utilization','order_value','Total_Time','Date','Week','DemandPullAhead'])
                else:
                    routeslice_pd = pd.DataFrame((routeslice,),columns=['Source','Destination','Travel_Mode','Carrier','Container_Size','MWpE','VWcF','Weight_Utilitation','Volume_Utilization','order_value','Total_Time','Date','Week','Consolids','DemandPullAhead'])
                try:
                    consolids = eval(routeslice_pd['Consolids'].item())
                except:
                    consolids = ()
                consolids_volumn_ut,consolids_weight_ut = 0,0
                for consolid_i in range(len(consolids)):
                    consolidable = consolids[consolid_i]
                    consolid_pd = pd.DataFrame(route_dict[consolidable[0]][consolidable[1]],columns=['Source','Destination','Travel_Mode','Carrier','Container_Size','MWpE','VWcF','Weight_Utilitation','Volume_Utilization','order_value','Total_Time','Date','Week'])
                    index = consolid_pd.index[(consolid_pd['Source'] == routeslice_pd['Source'].item()) & (consolid_pd['Destination'] == routeslice_pd['Destination'].item()) & (consolid_pd['Travel_Mode'] == routeslice_pd['Travel_Mode'].item()) & (consolid_pd['Carrier'] == routeslice_pd['Carrier'].item()) & (consolid_pd['Week'] == routeslice_pd['Week'].item())]
                    consolidslice = consolid_pd.loc[index]
                    consolids_volumn_ut += consolidslice['Volume_Utilization'].item()
                    consolids_weight_ut += consolidslice['Weight_Utilitation'].item()
                volumn_ut = routeslice_pd['Volume_Utilization'].item() + consolids_volumn_ut
                weight_ut = routeslice_pd['Weight_Utilitation'].item() + consolids_weight_ut
                total_volumn_ut = np.ceil(volumn_ut)
                total_weight_ut = np.ceil(weight_ut)
                total_ut = np.max((total_volumn_ut,total_weight_ut))
                if total_ut == total_weight_ut:
                    ratio = np.divide(routeslice_pd['Weight_Utilitation'].item(),weight_ut)
                    route_index = data.index[((data['Source'] == routeslice_pd['Source'].item()) & (data['Destination'] == routeslice_pd['Destination'].item()) & (data['Travel Mode'] == routeslice_pd['Travel_Mode'].item()) & (data['Carrier'] == routeslice_pd['Carrier'].item()))]
                    route_ = data.loc[route_index].to_dict('records')
                    cost_pd = calvalue(route_[0],routeslice_pd['Volume_Utilization'].item(),routeslice_pd['Weight_Utilitation'].item(),total_ut,ratio,orderindex[1])
                else:
                    ratio = np.divide(routeslice_pd['Volume_Utilization'].item(),volumn_ut)
                    route_index = data.index[((data['Source'] == routeslice_pd['Source'].item()) & (data['Destination'] == routeslice_pd['Destination'].item()) & (data['Travel Mode'] == routeslice_pd['Travel_Mode'].item()) & (data['Carrier'] == routeslice_pd['Carrier'].item()))]
                    route_ = data.loc[route_index].to_dict('records')
                    cost_pd = calvalue(route_[0],routeslice_pd['Volume_Utilization'].item(),routeslice_pd['Weight_Utilitation'].item(),total_ut,ratio,orderindex[1])
                routenew_pd = routeslice_pd.merge(cost_pd,left_index=True,right_index=True)
                costslice += tuple(routenew_pd.itertuples(index=False,name=None))
            cost_tuple.append(costslice)
        d_cost[orderindex] = tuple(cost_tuple)
def display(dictionary,routedict = {}):
    writer = pd.ExcelWriter(outputxl,engine='openpyxl')
    writer.book = book
    datafinal = pd.DataFrame(columns=['Orderno','Source','Destination','Legs','Intermidiates','Travel_Modes','Carriers','Time','Fixed Freight Cost','Port/Airport/Rail Handling Cost','Documentation Cost','Equipment Cost','Extra Cost','VariableFreightCost','Bunker/ Fuel Cost','Warehouse Cost','Transit Duty','Total Cost','OrderDate','DemandPullAhead'])
    datafinal_route = pd.DataFrame(columns=['Orderno','Source','Destination','Legs','Intermidiates','Travel_Mode','Carrier','Container_Size','MaxWeightPerEquipment','VolumetricWeightConversionFactor','Weight_Utilitation','Volume_Utilization','order_value','Total_Time','Date','Week'])
    for orderindex in dictionary:
        for routes in dictionary[orderindex]:
            finaldat = {}
            finaldat['Orderno'] = orderindex[0]
            finaldat['Source'] = routes[0][0]
            finaldat['Destination'] = routes[-1][1]
            finaldat['Intermidiates'] = routes[0][0]
            finaldat['Legs'] = len(routes) - 1
            finaldat['Travel_Modes'] = ''
            finaldat['Carriers'] = ''
            finaldat['Time'] = 0
            finaldat['OrderDate'] = routes[0][11]
            finaldat['DemandPullAhead'] = routes[0][13]
            finaldat['Fixed Freight Cost'] = 0
            finaldat['Port/Airport/Rail Handling Cost'] = 0
            finaldat['Documentation Cost'] = 0
            finaldat['Equipment Cost'] = 0
            finaldat['Extra Cost'] = 0
            finaldat['VariableFreightCost'] = 0
            finaldat['Bunker/ Fuel Cost'] = 0
            finaldat['Warehouse Cost'] = 0
            finaldat['Transit Duty'] = 0
            if type(finaldat['DemandPullAhead']) == str:
                finaldat['DemandPullAhead'] = routes[0][14]  
                for routeslice_i in range(0,len(routes)):
                    finaldat['Intermidiates'] += '--->' + routes[routeslice_i][1]
                    finaldat['Travel_Modes'] += routes[routeslice_i][2] + ','
                    finaldat['Carriers'] +=  routes[routeslice_i][3] + ',' 
                    finaldat['Time'] += routes[routeslice_i][10]
                    finaldat['Fixed Freight Cost'] += routes[routeslice_i][15]
                    finaldat['Port/Airport/Rail Handling Cost'] += routes[routeslice_i][16]
                    finaldat['Documentation Cost'] += routes[routeslice_i][17]
                    finaldat['Equipment Cost'] += routes[routeslice_i][18]
                    finaldat['Extra Cost'] += routes[routeslice_i][19]
                    finaldat['VariableFreightCost'] += routes[routeslice_i][20]
                    finaldat['Bunker/ Fuel Cost'] += routes[routeslice_i][21]
                    finaldat['Warehouse Cost'] += routes[routeslice_i][22]
                    finaldat['Transit Duty'] += routes[routeslice_i][23]
            else:
                for routeslice_i in range(0,len(routes)):
                    finaldat['Intermidiates'] += '--->' + routes[routeslice_i][1]
                    finaldat['Travel_Modes'] +=   routes[routeslice_i][2] + ','
                    finaldat['Carriers'] +=   routes[routeslice_i][3] + ','
                    finaldat['Time'] = finaldat['Time'] + routes[routeslice_i][10]
                    finaldat['Fixed Freight Cost'] += routes[routeslice_i][14]
                    finaldat['Port/Airport/Rail Handling Cost'] += routes[routeslice_i][15]
                    finaldat['Documentation Cost'] += routes[routeslice_i][16]
                    finaldat['Equipment Cost'] += routes[routeslice_i][17]
                    finaldat['Extra Cost'] += routes[routeslice_i][18]
                    finaldat['VariableFreightCost'] += routes[routeslice_i][19]
                    finaldat['Bunker/ Fuel Cost'] += routes[routeslice_i][20]
                    finaldat['Warehouse Cost'] += routes[routeslice_i][21]
                    finaldat['Transit Duty'] += routes[routeslice_i][22]
            finaldat['Carriers'] = finaldat['Carriers'][:-1]
            finaldat['Travel_Modes'] = finaldat['Travel_Modes'][:-1] 
            finaldat['Total Cost'] = finaldat['Fixed Freight Cost'] + finaldat['Port/Airport/Rail Handling Cost'] + finaldat['Documentation Cost'] + finaldat['Equipment Cost'] + finaldat['Extra Cost'] + finaldat['VariableFreightCost'] + finaldat['Bunker/ Fuel Cost'] + finaldat['Warehouse Cost'] + finaldat['Transit Duty']
            datafinal.loc[len(datafinal.index)] = finaldat
    for orderindex_ in routedict:
        for route_ in routedict[orderindex_]:
            finaldat_ = {}
            finaldat_['Order'] = orderindex_[0]
            finaldat_['Source'] = route_[0][0]
            finaldat_['Destination'] = route_[-1][1]
            finaldat_['Intermidiates'] =route_[0][0] + '--->' + route_[0][1]
            finaldat_['Legs'] = len(route_) - 1
            finaldat_['Travel_Mode'] = route_[0][2]
            finaldat_['Carrier'] = route_[0][3]
            finaldat_['Container_Size'] = '{}'.format(route_[0][4])
            finaldat_['MaxWeightPerEquipment'] = '{}'.format(route_[0][5])
            finaldat_['VolumetricWeightConversionFactor'] = '{}'.format(route_[0][6])
            finaldat_['Weight_Utilitation'] = '{}'.format(route_[0][7])
            finaldat_['Volume_Utilization'] = '{}'.format(route_[0][8])
            finaldat_['order_value'] = route_[0][9]
            finaldat_['Total_Time'] = route_[0][10]
            finaldat_['OrderDate'] = route_[0][11]
            for routeslice_I in range(1,len(route_)):
                finaldat_['Intermidiates'] += '--->' + route_[routeslice_I][1]
                finaldat_['Travel_Mode'] += ',' + route_[routeslice_I][2]
                finaldat_['Carrier'] += ',' + route_[routeslice_I][3]
                finaldat_['Container_Size'] += ',' +'{}'.format(route_[routeslice_I][4])
                finaldat_['MaxWeightPerEquipment'] += ',' +'{}'.format(route_[routeslice_I][5])
                finaldat_['VolumetricWeightConversionFactor'] += ',' +'{}'.format(route_[routeslice_I][6])
                finaldat_['Weight_Utilitation'] += ',' +'{}'.format(route_[routeslice_I][7])
                finaldat_['Volume_Utilization'] += ',' +'{}'.format(route_[routeslice_I][8])
            datafinal_route.loc[len(datafinal_route.index)] = finaldat_
    datafinal_route.to_excel(writer,sheet_name='ROUTING')
    datafinal.to_excel(writer,sheet_name='cost')
    writer.close()
#................................................................................
nodeindex = nodes.copy()
#deleted here since it isn't needed (switched to pandas)
for inputslice in order_data.values.tolist():
    for n in range(4):
        route(n,pc_new(nodeindex,(inputslice[1],inputslice[2])),inputslice[7],inputslice[1],inputslice[2],inputslice[5],inputslice[4],inputslice[3],())
        try:
            week = inputslice[7].strftime('%Y-%V')
        except:
            week = None
    d_route[(inputslice[0],inputslice[3],inputslice[4],inputslice[5],inputslice[7],inputslice[8])] = tuple(t)#storing routes belonging to different orders with dictionary
    t.clear()
# for i in d_route:
#     print(i)
#     for j in d_route[i]:
#         for k in j:
#             print(k)
#         print('\n')
consolidate_Routes(d_route)
# for i in d_consoildate:
#     print(i)
#     for j in d_consoildate[i]:
#         for k in j:
#             print(k)
#         print('\n')
#     print('\n')
cost(d_consoildate,d_route)
display(d_cost,d_route)
