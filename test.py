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
    #dataslice is a specific row which contain data specific to (travelmode,initial,final) 
    dataslice = data.loc[data['Travel_Mode'] == travelmode and data['Source']  == initial  and data['Destination'] == final]
    variable = {}
    variable['custom_clearance_time'] = dataslice['CustomClearance_time_hours']
    variable['Port_Airport_RailHandling_Time'] = dataslice['Port_Airport_Rail_Handling_time_hours']
    variable['extra_time'] = dataslice['Extra_Time']
    variable['transit_time'] = dataslice['Transit_time_hours']
    variable['MaxVolumePerEquipment'] = dataslice['Container_Size']
    variable['ConfidenceLevel'] = dataslice['ConfidenceLevel']
    variable['MaxWeightPerEquipment'] = dataslice['MaxWeightPerEquipment']
    variable['VolumetricWeightConversionFactor'] = dataslice['VolumetricWeightConversionFactor']
    return variable
def pc_new(nid,dest):
    p_ = nid.copy()
    for i in dest:
        p_.remove(i)
    return p_
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
#deleted here since it isn't needed (switched to pandas)
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
#deleted this part for new method