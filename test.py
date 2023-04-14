from sqlalchemy import create_engine,text
import datetime
import pandas as pd
import numpy as np
db_connection_str = create_engine('mysql+pymysql://root:0123456789@localhost:3306/again')
db_connection = db_connection_str.connect()
data = pd.read_sql(text('select * from model_data_imput;'),db_connection)
order_data = pd.read_sql(text('select * from model_data_order'),db_connection)
nodes = pd.unique(data[['Source','Destination']].values.ravel('k')).tolist()
travelmodes = data['Travel_Mode'].unique().tolist()
t = []
d = {}
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
    if not ((data['Travel_Mode'] == travelmode) & (data['Source']  == initial)  & (data['Destination'] == final)).any():#checks wether a row exist in the dataframe
        variable['transit_time'] = 0
        return variable
    #dataslice is a specific row which contain data specific to (travelmode,initial,final) 
    dataslice = data.loc[(data['Travel_Mode'] == travelmode) & (data['Source']  == initial)  & (data['Destination'] == final)]
    variable['custom_clearance_time'] =dataslice['CustomClearance_time_hours'].item()
    variable['Port_Airport_RailHandling_Time'] = dataslice['Port_Airport_Rail_Handling_time_hours'].item()
    variable['extra_time'] = dataslice['Extra_Time'].item()
    variable['transit_time'] = dataslice['Transit_time_hours'].item()
    variable['MaxVolumePerEquipment'] = dataslice['Container_Size'].item()
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
                    t.append(finaldat)
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
        elif n > 1 :
            for intermediate in nid:
                for travelelement in travelmodes:
                    variable = variablefinder(travelelement,intermediate,fin)
                    if variable['transit_time']:
                        pt = []
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
#................................................................................
nodeindex = nodes.copy()
#deleted here since it isn't needed (switched to pandas)
for inputslice in order_data.values.tolist():
    for n in range(1,3):
        route(n,pc_new(nodeindex,(inputslice[1],inputslice[2])),inputslice[7],inputslice[1],inputslice[2],())
    d[(inputslice[0],inputslice[3],inputslice[4],inputslice[5])] = tuple(t)#storing routes belonging to different orders with dictionary
    t.clear()
#deleted this part for new method