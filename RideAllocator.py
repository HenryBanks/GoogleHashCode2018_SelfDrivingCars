import numpy as np
import pandas as pd
import scipy, math, sys

### 0. METHODS

def extract_parameters(keys, df):
    parameters = {}
    for i in range(len(keys)):
        parameters[keys[i]] = round(float(df.columns[i]))
    return parameters

def remove_invalid_rides(data):
    data['valid?'] = data.apply(lambda row: row['dt'] <= row['dt_window'], axis = 1)
    len_before = len(data)
    data = data.loc[data['valid?']]
    len_after = len(data)
    print ('%s rides were invalid/impossible and have been removed.' % (len_before - len_after))
    data.drop(columns = 'valid?')
    return data

def build_results():
    results = []
    for i in range(1, parameters['F'] + 1):
        results.append([])
    return results

def build_vehicle_tracker():
    tracker = []
    for i in range(parameters['F']):
        tracker.append([1,0,0]) #Corresponding to t, x, y of next availability
    return tracker

def run_simulation(parameters, data):
    for t in range(1,parameters['T']-1):
        print ('%s of %s' % (t, parameters['T'])) #Show progress in console
        for v in range(1, parameters['F'] + 1):
            if tracker[v-1][0] == t and len(unallocated_rides) > 0: #Test if vehicle is available for a ride
                pd_max = 0 #Keep track of best p/d ratio
                r_select = None #Keep track of ride ID with pd_max
                d_total_select = None #Keep track of transfer and ride completion time
                for r in unallocated_rides: # <<<< Efficiency and journey-end opportunities
                    ds = delta_s(tracker[v-1][1], tracker[v-1][2], data.at[r, 'x1'], data.at[r, 'y1']) #Calculate spatial transfer cost
                    dt = delta_t(tracker[v-1][0], data.at[r, 't1']) #Calculate temporal transfer cost
                    d_trans = max(ds, dt) #Calculate transfer time
                    d_total = d_trans + data.at[r, 'd'] #Calculate total transfer and ride completion time
                    if d_trans == dt: #Check if the vehicle will arrive for the ride in time for the ideal ride start time
                        p = data.at[r, 'd+b'] #Include bonus points in score
                    else:
                        p = data.at[r, 'd'] #Exclude bonus points in score
                    pd = p/d_total #Calculate points per time unit, a measure of the value of the ride
                    if pd > pd_max: #Check to see if ride r is the most valuable yet
                        pd_max = pd #Store value for comparison in future loops through rides
                        r_select = r #Store ride ID
                        d_total_select = d_total #Store ride time to completion to avoid recalculation later
                results[v-1].append(r_select) #Record allocation in results
                #print ('Ride number %s allocated to vehicle %s' % (r_select, v))
                unallocated_rides.remove(r_select) #Remove ride from list of unallocated rides
                tracker[v-1] = [t+d_total_select, data.at[r_select, 'x2'], data.at[r_select, 'y2']] #Record new location of vehicle

def delta_s(x1, y1, x2, y2): #Difference in spatial displacement
    return abs(x2-x1) + abs(y2-y1)

def delta_t(t1, t2):
    return t2-t1

def print_output(results):
    #output = pd.DataFrame(results, dtype = int)
    output_name = files[sys.argv[1]][:-3] + '.out'
    output = open(output_name, 'w+')
    for v in range(1, parameters['F'] + 1):
        results_string = list(map(lambda x: str(x), results[v-1]))
        output.write(str(len(results_string)) + ' ' + ' '.join(results_string) + '\n')
    #output.to_csv(output_name, index = False, header = False, sep = ' ')
    #print ('The results as list of lists: %s' % (results))
    #print ('The results as dataframe: %s' % (output))

    
    #fout=open(sys.argv[1][:-3]+".out",'w+')

		#for veh in self.vehicleList:
			#fout.write(veh.printRides())

### 1. DEFINITIONS

files = {'a': 'a_example.in',
    'b': 'b_should_be_easy.in',
    'c': 'c_no_hurry.in',
    'd': 'd_metropolis.in',
    'e': 'e_high_bonus.in'}

parameter_keys = ['R', 'C', 'F', 'N', 'B', 'T']
''' Where:
    R = number of rows in the grid
    C = number of columns in the grid
    F = number of vehicles in the fleet
    N = number of rides
    B = per-ride bonus for starting the ride on time
    T = number of steps in the simulation '''

data_headers = ['x1', 'y1', 'x2', 'y2', 't1', 't2']
''' Where:
    x1 = row of the starting intersection
    y1 = column of the starting intersection
    x2 = row of the finishing intersection
    y2 = column of the finishing intersection
    t1 = the earliest start for the ride
    t2 = number of steps in the simulation '''

### 2. IMPORTING & PARSING SIMULATION DATA

data = pd.read_csv(files[sys.argv[1]], delim_whitespace = True)
parameters = extract_parameters(parameter_keys, data)
data.columns = data_headers
print ('Datafile: %s' % (files[sys.argv[1]]))
print ('Parameters: %s' % (parameters))

### 3. DATA CLEANING, CHECKS & PREP

data['d_window'] = data.apply(lambda row: row['t2']-row['t1'], axis = 1)
data['d'] = data.apply(lambda row: abs(row['x2']-row['x1']) + abs(row['y2']-row['y1']), axis = 1)
data['d+b'] = data.apply(lambda row: row['d'] + parameters['B'], axis = 1)
#data = remove_invalid_rides(data) - all data sources checked and all rides proved valid

### 4. OTHER SIMULATION PREP

results = build_results()
unallocated_rides = [i for i in data.index]
tracker = build_vehicle_tracker()

### 5. RUN SIMULATION

run_simulation(parameters, data)

### 6. SAVE OUTPUT

print_output(results)