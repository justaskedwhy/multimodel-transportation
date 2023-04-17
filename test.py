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
def route(n,nid,date,ini,fin,volume,weight,order_value,finaldat=()):#finaldat is in tuple because of the problems with list(local and globle variable problems)
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
                    Weight_Utilitation = weight/MWpE
                    Volume_Utilization = volume/container_size
                    total_time = variable['custom_clearance_time'] + variable['Port_Airport_RailHandling_Time'] + variable['extra_time'] + variable['transit_time']
                    date_new = date - datetime.timedelta(hours=total_time) #subtracts time by some hours
                    week_new = date_new.strftime('%Y-%V')#in the format YYYY-WW eg. 2023-06
                    finaldat = source,destination,carrier,container_size,MWpE,VWcF,Weight_Utilitation,Volume_Utilization,order_value,total_time,date_new,week_new,
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
                        Weight_Utilitation = weight/MWpE
                        Volume_Utilization = volume/container_size
                        total_time = variable['custom_clearance_time'] + variable['Port_Airport_RailHandling_Time'] + variable['extra_time'] + variable['transit_time']
                        date_new = date - datetime.timedelta(hours=total_time)
                        week_new = date_new.strftime('%Y-%V')
                        pt.append((source,destination,carrier,container_size,MWpE,VWcF,Weight_Utilitation,Volume_Utilization,order_value,total_time,date_new,week_new))
                        for travelelement2 in travelmodes:
                            variable2 = variablefinder(travelelement2,ini,intermediate)
                            if variable2['transit_time']:
                                destination = intermediate
                                source = ini
                                carrier = variable2['Carrier']
                                container_size = variable2['MaxVolumePerEquipment']
                                MWpE = variable2['MaxWeightPerEquipment']
                                VWcF = variable2['VolumetricWeightConversionFactor']
                                Weight_Utilitation = weight/MWpE
                                Volume_Utilization = volume/container_size
                                total_time = variable2['custom_clearance_time'] + variable2['Port_Airport_RailHandling_Time'] + variable2['extra_time'] + variable2['transit_time']
                                date_new_2 = date_new - datetime.timedelta(hours=total_time)
                                week_new_2 = date_new_2.strftime('%Y-%V')
                                pt.append((source,destination,carrier,container_size,MWpE,VWcF,Weight_Utilitation,Volume_Utilization,order_value,total_time,date_new_2,week_new_2))
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
                        Weight_Utilitation = weight/MWpE
                        Volume_Utilization = volume/container_size
                        total_time = variable['custom_clearance_time'] + variable['Port_Airport_RailHandling_Time'] + variable['extra_time'] + variable['transit_time']
                        date_new = date - datetime.timedelta(hours=total_time)
                        week_new = date_new.strftime('%Y-%V')
                        pt.append((source,destination,carrier,container_size,MWpE,VWcF,Weight_Utilitation,Volume_Utilization,order_value,total_time,date_new,week_new))
                        route(n-1,pc_new(nid.copy(),(intermediate,)),date_new,ini,intermediate,volume,weight,order_value,tuple(pt))
def consoildation(orderno,route,routedictionary,consolidant):
    fol = False
    pt = consolidant.copy()
    to_consolidate_df = pd.DataFrame(route,columns=['Source','Destination','Carrier','Container_Size','MWpE','VWcF','Weight_Utilitation','Volume_Utilization','order_value','Total_Time','Date','Week'])#dataframes are easy to work with
    for orderindex in routedictionary:
        if orderindex[0] == orderno:
            continue
        routetuple = routedictionary[orderindex]
        for root in routetuple:
            if fol:
                fol = False
                break
            from_df = pd.DataFrame(root,columns=['Source','Destination','Carrier','Container_Size','MWpE','VWcF','Weight_Utilitation','Volume_Utilization','order_value','Total_Time','Date','Week'])
            equaldf = to_consolidate_df.merge(from_df,on=['Source','Destination','Carrier','Week'],suffixes=('', '_DROP')).filter(regex='^(?!.*_DROP)')#finds commen rows to both dataframe
            for i in range(len(equaldf)):
                fol = True
                equalrow = equaldf.loc[i]
                index = pt.index[(consolidant['Source'] == equalrow['Source']) & (consolidant['Destination'] == equalrow['Destination']) & (consolidant['Carrier'] == equalrow['Carrier']) & (consolidant['Week'] == equalrow['Week'])]
                pt.loc[index,'Consolidant'] += str((orderindex,routetuple.index(root))) + ','#adds the route index to the column consolidation 
    consolidant_tuple = tuple(pt.itertuples(index=False,name=None))
    t_consolidate.append(consolidant_tuple)
def consolidate_Routes(routes):
    for orderindex in routes:
        for route in routes[orderindex]:
            df = pd.DataFrame(route,columns=['Source','Destination','Carrier','Container_Size','MWpE','VWcF','Weight_Utilitation','Volume_Utilization','order_value','Total_Time','Date','Week'])
            df['Consolidant'] = ''
            consoildation(orderindex[0],route,routes,df)
        d_consoildate[orderindex] = tuple(t_consolidate)
        t_consolidate.clear()
#................................................................................
nodeindex = nodes.copy()
#deleted here since it isn't needed (switched to pandas)
for inputslice in order_data.values.tolist():
    for n in range(4):
        route(n,pc_new(nodeindex,(inputslice[1],inputslice[2])),inputslice[7],inputslice[1],inputslice[2],inputslice[5],inputslice[4],inputslice[3],())
        try:
            week = inputslice[6].strftime('%Y-%V')
        except:
            week = None
    d_route[(inputslice[0],inputslice[3],inputslice[4],inputslice[5],week)] = tuple(t)#storing routes belonging to different orders with dictionary
    t.clear()
# for i in d_route:
#     print(i)
#     for j in d_route[i]:
#         for k in j:
#             print(k)
#         print('\n')
consolidate_Routes(d_route)
for i in d_consoildate:
    print(i)
    for j in d_consoildate[i]:
        for k in j:
            print(k)
        print('\n')
    print('\n')
#deleted this part for new method