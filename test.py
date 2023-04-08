import mysql.connector as sqldb
from sqlalchemy import create_engine,text
from datetime import timedelta
import pandas as pd
import numpy as np
db_connection_str = create_engine('mysql+pymysql://root:0123456789@localhost:3306/again')
db_connection = db_connection_str.connect()
data = pd.read_sql(text('select * from model_data_imput;'),db_connection)
order_data = pd.read_sql(text('select * from model_data_order'),db_connection)
columns = list(data.columns)
miscellaneous = columns[3:6] + columns[21:22]
costs = columns[8:17]
times = columns[17:21]
nodes = pd.unique(data[['Source','Destination']].values.ravel('k')).tolist()
travelmodes = data['Travel_Mode'].unique().tolist()
t = []
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
    variable['custom_clearance_time'] = timeMatrix[0,travelmodes.index(travelmode),nodes.index(initial),nodes.index(final)]
    variable['Port_Airport_RailHandling_Time'] = timeMatrix[1,travelmodes.index(travelmode),nodes.index(initial),nodes.index(final)]
    variable['extra_time'] = timeMatrix[2,travelmodes.index(travelmode),nodes.index(initial),nodes.index(final)]
    variable['transit_time'] = timeMatrix[3,travelmodes.index(travelmode),nodes.index(initial),nodes.index(final)]
    variable['FixedFreightCost'] = costMatrix[0,travelmodes.index(travelmode),nodes.index(initial),nodes.index(final)]
    variable['VariableFreightCost'] = costMatrix[1,travelmodes.index(travelmode),nodes.index(initial),nodes.index(final)]
    variable['Port_Airport_RailHandlingCost'] = costMatrix[2,travelmodes.index(travelmode),nodes.index(initial),nodes.index(final)]
    variable['Bunker_FuelCost'] = costMatrix[3,travelmodes.index(travelmode),nodes.index(initial),nodes.index(final)]
    variable['DocumentationCost'] = costMatrix[4,travelmodes.index(travelmode),nodes.index(initial),nodes.index(final)]
    variable['EquipmentCost'] = costMatrix[5,travelmodes.index(travelmode),nodes.index(initial),nodes.index(final)]
    variable['ExtraCost'] = costMatrix[6,travelmodes.index(travelmode),nodes.index(initial),nodes.index(final)]
    variable['WarehouseCost'] = costMatrix[7,travelmodes.index(travelmode),nodes.index(initial),nodes.index(final)]
    variable['TransitDuty'] = costMatrix[8,travelmodes.index(travelmode),nodes.index(initial),nodes.index(final)]
    variable['MaxVolumePerEquipment'] = miscellaneousMatrix[0,travelmodes.index(travelmode),nodes.index(initial),nodes.index(final)]
    variable['ConfidenceLevel'] = miscellaneousMatrix[3,travelmodes.index(travelmode),nodes.index(initial),nodes.index(final)]
    variable['MaxWeightPerEquipment'] = miscellaneousMatrix[1,travelmodes.index(travelmode),nodes.index(initial),nodes.index(final)]
    variable['VolumetricWeightConversionFactor'] = miscellaneousMatrix[2,travelmodes.index(travelmode),nodes.index(initial),nodes.index(final)]
    return variable
def pc_new(nid,dest):
    p_ = nid.copy()
    for i in dest:
        p_.remove(i)
    return p_
print(pc_new(['a','b','c','d','e'],('a',)))
def path_new(n,nid,volume,weight,order_value,ini,fin='',finaldat={}):
        if n == 0:
            for travelelement in travelmodes:
                variable = variablefinder(travelelement,ini,fin)
                cost = calvalue(variable,volume,weight,order_value)
                if  variable['transit_time']:
                    finaldat['Route'] = ini + ' -->' + fin
                    finaldat['Mode'] = travelelement
                    variable.update(cost)
                    variable.pop('MaxVolumePerEquipment')
                    variable.pop('MaxWeightPerEquipment')
                    variable.pop('VolumetricWeightConversionFactor')
                    finaldat.update(variable)
                    t.append(finaldat)
                    return
        if n == 1:
            for intermediate in nid:
                #print(nid)
                for travelelement in travelmodes:
                    variable = variablefinder(travelelement,ini,intermediate)
                    cost = calvalue(variable,volume,weight,order_value)
                    if variable['transit_time']:
                        if intermediate in finaldat['Route']:
                            continue
                        pt = {}
                        pt.update(finaldat)
                        pt['Route'] += '-->' + intermediate    
                        if 'Mode' in finaldat:
                            pt['Mode'] +=  ',' + travelelement
                            pt['ConfidenceLevel'] *= variable['ConfidenceLevel']
                        else:
                            pt['Mode'] = travelelement
                            pt['ConfidenceLevel'] = variable['ConfidenceLevel']
                        variable.update(cost)
                        for travelelement2 in travelmodes:
                            variable2 = variablefinder(travelelement2,intermediate,fin)
                            cost2 = calvalue(variable2,volume,weight,order_value)
                            if variable2['transit_time']:
                                pt['Route'] += '-->' + fin
                                pt['Mode'] += ',' + travelelement2
                                pt['ConfidenceLevel'] *= variable2['ConfidenceLevel']
                                variable2.update(cost2)
                                variable.pop('ConfidenceLevel') 
                                variable.pop('MaxVolumePerEquipment')
                                variable.pop('MaxWeightPerEquipment')
                                variable.pop('VolumetricWeightConversionFactor')
                                variable2.pop('ConfidenceLevel') 
                                variable2.pop('MaxVolumePerEquipment')
                                variable2.pop('MaxWeightPerEquipment')
                                variable2.pop('VolumetricWeightConversionFactor')
                                for i in variable:
                                    if i in finaldat:
                                        pt[i] += variable[i] + variable2[i]
                                    else:
                                        pt[i] = variable[i] + variable2[i]
                                t.append(pt)
        elif n > 1 :
            for intermediate in nid:
                for travelelement in travelmodes:
                    variable = variablefinder(travelelement,ini,intermediate)
                    cost = calvalue(variable,volume,weight,order_value)
                    if variable['transit_time']:
                        if intermediate in finaldat['Route']:
                            continue
                        pt = {}
                        pt.update(finaldat)
                        if 'Mode' in finaldat:
                            pt['Route'] += '-->' + intermediate
                            pt['Mode']  += ',' + travelelement
                            pt['ConfidenceLevel'] *= variable['ConfidenceLevel']
                        else:
                            pt['Route'] += '-->' + intermediate
                            pt['Mode']  = travelelement
                            pt['ConfidenceLevel'] = variable['ConfidenceLevel']
                        variable.update(cost)
                        variable.pop('ConfidenceLevel') 
                        variable.pop('MaxVolumePerEquipment')
                        variable.pop('MaxWeightPerEquipment')
                        variable.pop('VolumetricWeightConversionFactor')
                        for i in variable:
                            if i in finaldat:
                                pt[i] += variable[i]
                            else:
                                pt[i] = variable[i]
                        path_new(n-1,pc_new(nid.copy(),(intermediate,)),volume,weight,order_value,intermediate,fin,pt)
#...    .............................................................................
nodeindex = nodes.copy()
timeMatrix = np.zeros((len(times),len(travelmodes),len(nodes),len(nodes)))
costMatrix = np.zeros((len(costs),len(travelmodes),len(nodes),len(nodes)))
miscellaneousMatrix = np.zeros((len(miscellaneous),len(travelmodes),len(nodes),len(nodes)))
ind = data.values.tolist()
for dataslice in ind:
    #print(dataslice)
    sourceindex,destinationindex,travel_mode,CustomClearanceTime,TransitTime,Port_Airport_RailHandlinTime,ExtraTime= nodes.index(dataslice[1]),nodes.index(dataslice[2]),travelmodes.index(dataslice[7]),dataslice[15],dataslice[16],dataslice[17],dataslice[18]
    FixedFreightCost,VariableFreightCost,Port_Airport_RailHandlingCost,Bunker_Fuel_Cost,DocumentationCost,EquipmentCost,ExtraCost,WarehouseCost,TransitDuty = dataslice[6],dataslice[7],dataslice[8],dataslice[9],dataslice[10],dataslice[11],dataslice[12],dataslice[13],dataslice[14]
    MaxVolumePerEquipment,ConfidenceLevel,MaxWeightPerEquipment,VolumetricWeightConversionFactor = dataslice[2],dataslice[19],dataslice[3],dataslice[4]
    for i in times:
        timeMatrix[times.index(i),travel_mode,sourceindex,destinationindex] = dataslice[columns.index(i)]
    for i in costs:
        costMatrix[costs.index(i),travel_mode,sourceindex,destinationindex] = dataslice[columns.index(i)]
    for i in miscellaneous:
        miscellaneousMatrix[miscellaneous.index(i),travel_mode,sourceindex,destinationindex] = dataslice[columns.index(i)]
#........................................................................................
#print(timm,daym,cc,sep='\n')
x,x_ = 0,0
for inputslice in order_data.values.tolist():
    for n in range(1):
        path_new(n,pc_new(nodeindex,(inputslice[1],inputslice[2])),inputslice[5],inputslice[4],inputslice[3],inputslice[1],inputslice[2],{'Order_no':inputslice[0],'Stops':n,'Ship_From':inputslice[1],'Ship_To':inputslice[2],'Route':inputslice[1],'Order_date':inputslice[6],'Required_Delivery_Date':inputslice[7]})
    x = len(t)
    if x == x_:
        x_ = {'Order_no':inputslice[0],'Stops':n,'Ship_From':inputslice[1],'Ship_To':inputslice[2],'Order_date':inputslice[6],'Required_Delivery_Date':inputslice[7]}
        x_.update(dict.fromkeys(('Route','Mode','FixedFreightCost','VariableFreightCost','Port_Airport_RailHandlingCost','Bunker_FuelCost','DocumentationCost','EquipmentCost','ExtraCost','WarehouseCost','TransitDuty','custom_clearance_time','Port_Airport_RailHandling_Time','extra_time','transit_time','ConfidenceLevel','MaxVolumePerEquipment'),0))#Path not available
        t += [x_]
        x_ = x + 1
        continue
    x_ = x
dat= {}
dat['Order_no'] = []
dat['Stops'] = []
dat['Ship_From'] = []
dat['Ship_To'] = []
dat['Route'] = []
dat['Mode'] = []
dat['FixedFreightCost'] = []
dat['VariableFreightCost'] = []
dat['Port_Airport_RailHandlingCost'] = []
dat['Bunker_FuelCost'] = []
dat['DocumentationCost'] = []
dat['EquipmentCost'] = []
dat['ExtraCost'] = []
dat['WarehouseCost'] =[]
dat['TransitDuty'] = []
dat['custom_clearance_time'] = []
dat['Port_Airport_RailHandling_Time'] = []
dat['extra_time'] = []
dat['transit_time'] = []
dat['ConfidenceLevel'] = []
dat['Order_date'] = []
dat['Required_Delivery_Date'] = []
for i in t:
    for j in i:
        if j == 'MaxVolumePerEquipment':
            continue
        dat[j].append(i[j])
df = pd.DataFrame(dat)
if 'Path not available' not in  dat['custom_clearance_time']:
    df['Total_time'] = df['custom_clearance_time'] + df['Port_Airport_RailHandling_Time'] + df['extra_time'] + df['transit_time'] 
    df['Total_cost'] = df['FixedFreightCost'] + df['VariableFreightCost'] + df['Port_Airport_RailHandlingCost'] + df['Bunker_FuelCost'] + df['DocumentationCost'] + df['EquipmentCost'] + df['ExtraCost'] + df['WarehouseCost'] + df['TransitDuty']
else:
    df['Total_time'] = 0
    df['Total_cost'] = 0
Plan_Ship_Date = []
Actual_Delivery_Date = []
for dates in range(len(df['Order_date'])):
    try:
        if df['Total_time'][dates] == 'Path not available' or np.isnan(df['Order_date'][dates]):
            Actual_Delivery_Date += [np.nan] 
            continue
    except:
        pass
    Actual_Delivery_Date += [df['Order_date'][dates]+  timedelta(df['Total_time'][dates]/24)]
for dates in range(len(df['Required_Delivery_Date'])):
    try:
        if  df['Total_time'][dates] == 'Path not available'  or  np.isnan(df['Required_Delivery_Date'][dates]):
            Plan_Ship_Date += [np.nan] 
            continue
    except:
        pass
    Plan_Ship_Date += [df['Required_Delivery_Date'][dates] -  timedelta(df['Total_time'][dates]/24)]
df['Plan_Ship_Date'] = Plan_Ship_Date
df['Actual_Delivery_Date'] = Actual_Delivery_Date
df.to_sql('model_data',con = db_connection,if_exists='append',index = False)
db_connection.commit()