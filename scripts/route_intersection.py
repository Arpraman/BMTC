# -*- coding: utf-8 -*-
"""
Created on Wed Apr  2 10:46:30 2025

@author: Arpita.Pramanick
"""

import pandas as pd

#The excel file contains data in different sheets... the name of the bus number is the sheetname. Only one directional route list is available.

data = pd.ExcelFile(r'C:\Users\Arpita.Pramanick\OneDrive - Unilever\Desktop\BMTC Data\BMTC\data\Bus Routes.xlsx')

route = pd.DataFrame()

#Reading each bus number and its stops into one dataframe
for sheet in data.sheet_names:
    stops = pd.read_excel(data,sheet,header=None)
    stops.columns = ['Stops']
    stops['BusNumber'] = sheet
    stops = stops[['BusNumber','Stops']]
    route = pd.concat([route,stops])
    del stops

routeCp = route.copy()

route = routeCp.copy()

#Transform the bus stop names
def cleanStops(df):
    df['Stops'] = df['Stops'].apply(lambda x: x.split('(')[0])
    df['Stops'] = df['Stops'].apply(lambda x: x.split(',')[0])    
    df.Stops = df.Stops.str.strip()
    df.Stops = df.Stops.str.lower()
    return(df)

route = cleanStops(route)

#Find all the intersecting stops for provided busnumber-busstop combos. This will return multiple intersections
# This will also return route combos like this: KBS1K_500CA and 500CA_KBS1K.

def findIntersect(df):
    busnum = df.BusNumber.unique()
    interDict = {}
    
    for i in range(len(busnum)):
        list1 = df[df.BusNumber == busnum[i]].Stops.unique()
        for j in range(len(busnum)):
            if i != j:  # Ensure we don't compare the same bus number
                list2 = df[df.BusNumber == busnum[j]].Stops.unique()
                intersect = [x for x in list1 if x in list2]
                interDict[f'{busnum[i]}_{busnum[j]}'] = intersect
                interDict[f'{busnum[j]}_{busnum[i]}'] = intersect
    
    # Filter out non-empty values
    non_empty_interDict = {k: v for k, v in interDict.items() if v}
    
    return non_empty_interDict

intersections = findIntersect(route)
        
#Takes in start and stop destinations and returns a recommendation of bus and intersection stops.
#This function can only work for routes having direct buses or just 1 change 

def findBuses(start,stop,df=route,intersect=intersections):
    #Find the buses which have the start location
    start_bus = df[df.Stops.str.contains(start)].BusNumber.unique()
    print("Buses starting from origin:",start_bus)
    #Find the buses which have the stop location
    stop_bus = df[df.Stops.str.contains(stop)].BusNumber.unique()
    print("Buses going to destination:",stop_bus)
    single_bus_rt = [x for x in start_bus if x in stop_bus]
    if single_bus_rt:
        print("There are buses going directly to destination:",single_bus_rt)
        for bus in single_bus_rt:
            print('Start via ' + bus+' at: '+start+ ' and get down at destination '+stop)
    else:   
        #Combine the buses which go in the start or stop routes
        bestIntersection = bestIntersect(intersect,route,start)
        bus_combos = [x +'_'+ y for x in start_bus for y in stop_bus]
        print("Start and last leg bus combos: ",bus_combos)
       # bus_list = {k: intersect.get(k, []) for k in bus_combos}
        bus_list = {k: v for k, v in {k: bestIntersection.get(k, []) for k in bus_combos}.items() if v}
        print("Buses going in the target destination:", bus_list)
        print("Starting location is:",start)
        if user_recommendations(buses = bus_list,start=start,stop=stop):
            return(user_recommendations(buses = bus_list,start=start,stop=stop))
        else:
            return(bestTransfers(bus_combos, route, intersections, start))

#Given list of intersections, the entire route list and the starting path, this returns the best intersect from the starting position.
#Best is defined in terms of the intersection that is closes to the start.
def bestIntersect(intersections,route,start):
    bestIntersection = intersections.copy()
   # print(bestIntersection)
    for k in bestIntersection.keys():  
        print("Value of k is:",k)
        if len(bestIntersection[k])>1:
            start_bus = k.split('_')[0]
            sb_route = list(route[route.BusNumber==start_bus]['Stops'].unique())
            print(sb_route)
            mindist = len(sb_route)
            bestIntersect = start
            if start in sb_route:
                index1 = sb_route.index(start)
                for val in bestIntersection[k]:                 
                    index2 = sb_route.index(val)
                    distance = abs(index1 - index2)
                    if distance < mindist:
                        mindist = distance
                        bestIntersect = val
                bestIntersection[k] = bestIntersect
        # else:
        #     bestIntersection[0]
    return(bestIntersection)
    
#Generates a human readable recommendation of the action to be taken

def user_recommendations(buses,start,stop):
    recommendation = []
    for k in buses.keys():
        start_bus = k.split('_')[0]
        stop_bus = k.split('_')[1]
        if type(buses[k])!=list:
            intersect = buses[k]
        else:
            intersect = buses[k][0]
        value = 'Start via ' + start_bus+' at: '+ start+ '; Change at: '+ str(intersect) + '; Next Bus: '+str(stop_bus)+' to reach destination'
        recommendation.append(value)
        print(recommendation)
    return(recommendation)
    
     


#Best transfers for non-matching combo

def bestTransfers(bus_combos, route, intersections, start):
    for buspair in bus_combos:
        if buspair not in intersections:
            start_bus, last_bus = buspair.split('_')
            print(f"Processing bus pair: {start_bus} -> {last_bus}")
            
            origin_match = {k: v for k, v in intersections.items() if start_bus in k}
           
            
            destination_match = {k: v for k, v in intersections.items() if last_bus in k}

            
            origin_other = [k.split("_")[0] for k in origin_match.keys() if k.split("_")[0] != start_bus]

            
            transfer_match = {k: v for bus in origin_other for k, v in destination_match.items() if bus in k}
            keys_to_remove = [k for k in transfer_match.keys() if k.split("_")[0] == last_bus]
            transfer_match = {k: v for k, v in transfer_match.items() if k not in keys_to_remove}
            transfer_other = [k.split("_")[0] for k in transfer_match.keys()]

            
            
            vals_to_add = [k.split("_")[0] for k in transfer_match.keys() if k.split("_")[0] in origin_other]
            origin_other = [x for x in origin_other if x in vals_to_add]
            
            for bus in origin_other:
                origin_match.update({k: v for k, v in origin_match.items() if k in bus})
            keys_to_remove = [k for k in origin_match.keys() if k.split("_")[0] != start_bus]

            keys_to_remove.extend([k for k in origin_match.keys() if k.split("_")[1] not in transfer_other])

            origin_match = {k: v for k, v in origin_match.items() if k not in keys_to_remove}
            origin_match = bestIntersect(origin_match,route,start)
            # transfer_match = bestIntersect(transfer,route,start)
            print("Origin match:", origin_match)
            print("Transfer match:", transfer_match)
            return (create_nested_dict(origin_match, transfer_match))

def create_nested_dict(origin_match, transfer_match):
    nested_dict = {}
    used_keys = set()

    for o_key, o_value in origin_match.items():
        for t_key, t_value in transfer_match.items():
            common_part = o_key.split('_')[1]
            if common_part in t_key and o_key not in used_keys:
                route_key = f'route{len(nested_dict) + 1}'
                nested_dict[route_key] = [{o_key: o_value}, {t_key: t_value}]
                used_keys.add(o_key)
                used_keys.add(t_key)

    return nested_dict
    
#Direct bus
findBuses('thubarahalli','spice garden')

#1 bus transfers between these two
findBuses('kempegowda bus station','cunningham road')

#No direct buses or 1-bus transfers between these two:
findBuses('jayadeva hospital','cunningham road')     
