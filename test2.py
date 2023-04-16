from tkinter import Tk  #changed to accept excel sheets
from tkinter.filedialog import askopenfilename
import datetime
import pandas as pd
import numpy as np
Tk().withdraw() 
inputxl = askopenfilename(title='input')  
data = pd.read_excel(inputxl,sheet_name='Route Information')
order_data = pd.read_excel(inputxl,sheet_name='Order Information')
nodes = pd.unique(data[['Source','Destination']].values.ravel('k')).tolist()
travelmodes = data['Travel Mode'].unique().tolist()   #the excel has some changes to the names of the columns
t = []
t_consolidate = []
d_route = {}
d_consoildate = {}
def calvalue(cost,volume,weight,order_value):
    dict = {}
    dict['FixedFreightCost'] = cost['FixedFreightCost']*np.max((np.ceil(volume/cost['MaxVolumePerEquipment']),np.ceil(weight/cost['MaxWeightPerEquipment'])))
    dict['VariableFreightCost'] = cost['VariableFreightCost']*np.max((np.ceil(volume*cost['VolumetricWeightConversionFactor']),np.ceil(weight)))
    dict['Port/Airport/RailHandlingCost'] = cost['Port/Airport/RailHandlingCost']*np.max((np.ceil(volume/cost['MaxVolumePerEquipment']),np.ceil(weight/cost['MaxWeightPerEquipment'])))
    dict['Bunker/FuelCost'] = cost['Bunker/FuelCost']
    dict['DocumentationCost'] = cost['DocumentationCost']*np.max((np.ceil(volume/cost['MaxVolumePerEquipment']),np.ceil(weight/cost['MaxWeightPerEquipment'])))
    dict['EquipmentCost'] = cost['EquipmentCost']*np.max((np.ceil(volume/cost['MaxVolumePerEquipment']),np.ceil(weight/cost['MaxWeightPerEquipment'])))
    dict['ExtraCost'] = cost['ExtraCost']*np.max((np.ceil(volume/cost['MaxVolumePerEquipment']),np.ceil(weight/cost['MaxWeightPerEquipment'])))
    dict['WarehouseCost'] = cost['WarehouseCost']*volume
    dict['TransitDuty'] = cost['TransitDuty']*order_value
    return dict
def variablefinder(travelmode,initial,final):
    variable = {}
    if not ((data['Travel Mode'] == travelmode) & (data['Source']  == initial)  & (data['Destination'] == final)).any():#checks wether a row exist in the dataframe
        variable['transit_time'] = 0
        return variable
    #dataslice is a specific row which contain data specific to (travelmode,initial,final) 
    dataslice = data.loc[(data['Travel Mode'] == travelmode) & (data['Source']  == initial)  & (data['Destination'] == final)]
    variable['custom_clearance_time'] =dataslice['CustomClearance time (hours)'].item()
    variable['Port_Airport_RailHandling_Time'] = dataslice['Port/Airport/Rail Handling time (hours)'].item()
    variable['extra_time'] = dataslice['Extra Time'].item()
    variable['transit_time'] = dataslice['Transit time (hours)'].item()
    variable['MaxVolumePerEquipment'] = dataslice['Container Size'].item()
    variable['ConfidenceLevel'] = dataslice['ConfidenceLevel'].item()
    variable['MaxWeightPerEquipment'] = dataslice['MaxWeightPerEquipment'].item()
    variable['VolumetricWeightConversionFactor'] = dataslice['VolumetricWeightConversionFactor'].item()
    variable['Carrier'] = dataslice['Carrier'].item()
    return variable
def pc_new(nid,dest):
    p_ = nid.copy()
    for i in dest:
        p_.remove(i)
    return p_
def route(n,nid,date,ini,fin,finaldat=()):#finaldat is in tuple because of the problems with list(local and globle variable problems)
        if n == 0:
            for travelelement in travelmodes:
                variable = variablefinder(travelelement,ini,fin)
                if  variable['transit_time']:
                    destination = fin
                    source = ini
                    carrier = variable['Carrier']
                    container_size = variable['MaxVolumePerEquipment']
                    MWpE = variable['MaxWeightPerEquipment']
                    VWcF = variable['VolumetricWeightConversionFactor']
                    total_time = variable['custom_clearance_time'] + variable['Port_Airport_RailHandling_Time'] + variable['extra_time'] + variable['transit_time']
                    date_new = date - datetime.timedelta(hours=total_time) #subtracts time by some hours
                    week_new = date_new.strftime('%Y-%V')#in the format YYYY-WW eg. 2023-06
                    finaldat = source,destination,carrier,container_size,MWpE,VWcF,total_time,date_new,week_new,
                    t.append((finaldat,))
            return
        if n == 1:
            pt = list(finaldat)
            for intermediate in nid:
                for travelelement in travelmodes:
                    variable = variablefinder(travelelement,intermediate,fin)
                    if variable['transit_time']:
                        destination = fin
                        source = intermediate
                        carrier = variable['Carrier']
                        container_size = variable['MaxVolumePerEquipment']
                        MWpE = variable['MaxWeightPerEquipment']
                        VWcF = variable['VolumetricWeightConversionFactor']
                        total_time = variable['custom_clearance_time'] + variable['Port_Airport_RailHandling_Time'] + variable['extra_time'] + variable['transit_time']
                        date_new = date - datetime.timedelta(hours=total_time)
                        week_new = date_new.strftime('%Y-%V')
                        pt.append((source,destination,carrier,container_size,MWpE,VWcF,total_time,date_new,week_new))
                        for travelelement2 in travelmodes:
                            variable2 = variablefinder(travelelement2,ini,intermediate)
                            if variable2['transit_time']:
                                destination = intermediate
                                source = ini
                                carrier = variable2['Carrier']
                                container_size = variable2['MaxVolumePerEquipment']
                                MWpE = variable2['MaxWeightPerEquipment']
                                VWcF = variable2['VolumetricWeightConversionFactor']
                                total_time = variable2['custom_clearance_time'] + variable2['Port_Airport_RailHandling_Time'] + variable2['extra_time'] + variable2['transit_time']
                                date_new_2 = date_new - datetime.timedelta(hours=total_time)
                                week_new_2 = date_new_2.strftime('%Y-%V')
                                pt.append((source,destination,carrier,container_size,MWpE,VWcF,total_time,date_new_2,week_new_2))
                                t.append(tuple(pt[::-1]))#to change the order from last to first to first to last.
                                pt.pop()
                        pt.pop()
        elif n > 1 :
            for intermediate in nid:
                for travelelement in travelmodes:
                    variable = variablefinder(travelelement,intermediate,fin)
                    if variable['transit_time']:
                        pt = list(finaldat)
                        destination = fin
                        source = intermediate
                        carrier = variable['Carrier']
                        container_size = variable['MaxVolumePerEquipment']
                        MWpE = variable['MaxWeightPerEquipment']
                        VWcF = variable['VolumetricWeightConversionFactor']
                        total_time = variable['custom_clearance_time'] + variable['Port_Airport_RailHandling_Time'] + variable['extra_time'] + variable['transit_time']
                        date_new = date - datetime.timedelta(hours=total_time)
                        week_new = date_new.strftime('%Y-%V')
                        pt.append((source,destination,carrier,container_size,MWpE,VWcF,total_time,date_new,week_new))
                        route(n-1,pc_new(nid.copy(),(intermediate,)),date_new,ini,intermediate,tuple(pt))
def consoildation(orderno,route,routedictionary,consolidant):
    fol = True#to ensure no duplicate consolidation
    if len(route) == 0:#END
        consolidant_tuple = tuple(consolidant.itertuples(index=False,name=None))
        t_consolidate.append(consolidant_tuple)
        return 
    routeslice = route[0]
    #if statements for routes which have already consoliate and eleminate orderindex one by one after used
    to_consolidate_df = pd.DataFrame(route,columns=['Source','Destination','Carrier','Container_Size','MWpE','VWcF','Total_Time','Date','Week'])#dataframes are easy to work with
    for orderindex in routedictionary:
        if orderindex[0] == orderno:
            continue
        routetuple = routedictionary[orderindex]
        routedictionary_new = routedictionary.copy()
        routedictionary_new.pop(orderindex)#to remove already used order
        for root in routetuple:
            from_df = pd.DataFrame(root,columns=['Source','Destination','Carrier','Container_Size','MWpE','VWcF','Total_Time','Date','Week'])
            equaldf = to_consolidate_df.merge(from_df,on=['Source','Destination','Carrier','Week'],suffixes=('', '_DROP')).filter(regex='^(?!.*_DROP)')#finds commen rows to both dataframe
            route_new_df_1 = pd.concat([to_consolidate_df,equaldf],ignore_index=True).drop_duplicates(subset=['Source','Destination','Carrier','Week'],keep= False)#https://pandas.pydata.org/docs/reference/api/pandas.concat.html, https://www.digitalocean.com/community/tutorials/pandas-drop-duplicate-rows-drop_duplicates-function
            route_new_df_2 = route_new_df_1.drop(route_new_df_1.index[(route_new_df_1['Source'] == routeslice[0]) & (route_new_df_1['Destination'] == routeslice[1]) & (route_new_df_1['Week'] == routeslice[8])])#drops row which is in use
            route_new_ = tuple(route_new_df_2.itertuples(index=False,name=None))
            pt = consolidant.copy()
            for i in range(len(equaldf)):
                fol = False
                equalrow = equaldf.loc[i]
                index = pt.index[(consolidant['Source'] == equalrow['Source']) & (consolidant['Destination'] == equalrow['Destination']) & (consolidant['Carrier'] == equalrow['Carrier']) & (consolidant['Week'] == equalrow['Week'])]
                pt.loc[index,'Consolidant'] = str((orderindex,routetuple.index(root)))#adds the route index to the column consolidation 
                consoildation(orderno,route_new_,routedictionary_new,pt.copy())
    if fol:
        consoildation(orderno,route[1:],routedictionary,consolidant)
def consolidate_Routes(routes):
    for orderindex in routes:
        for route in routes[orderindex]:
            df = pd.DataFrame(route,columns=['Source','Destination','Carrier','Container_Size','MWpE','VWcF','Total_Time','Date','Week'])
            df['Consolidant'] = ''
            consoildation(orderindex[0],route,routes,df)
        d_consoildate[orderindex] = tuple(t_consolidate)
        t_consolidate.clear()
#...    .............................................................................
nodeindex = nodes.copy()
#deleted here since it isn't needed (switched to pandas)
for inputslice in order_data.values.tolist():
    for n in range(3):
        route(n,pc_new(nodeindex,(inputslice[1],inputslice[2])),inputslice[7],inputslice[1],inputslice[2],())
    d_route[(inputslice[0],inputslice[3],inputslice[4],inputslice[5],inputslice[6])] = tuple(t)#storing routes belonging to different orders with dictionary
    t.clear()
for i in d_route:
    print(i)
    for j in d_route[i]:
        for k in j:
            print(k)
        print('\n')
consolidate_Routes(d_route)
for i in d_consoildate:
    print(i)
    for j in d_consoildate[i]:
        print(j)
    print('\n')
#deleted this part for new method