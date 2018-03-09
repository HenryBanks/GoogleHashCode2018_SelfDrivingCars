import numpy as np
import pandas as pd
from pytictoc import TicToc
import scipy, math, sys

### 1. CLASSES

class SimulationGreedy:

    ## a. Class variables

    ## b. Constructor

    def __init__(self, orderbook):
        self.name = orderbook.name
        self.rides = orderbook.data
        self.parameters = orderbook.parameters
        self.rides_matrix = self.rides.values
        self.rides_unalloc = [i for i in self.rides.index]
        self.vehicles = self.create_vehicles()
        self.status = 'Ready'
        self.score = 0
        self.score_max = (self.rides['d_ride'].sum(), self.rides['b_ride'].sum())
        #self.performance = None
        #self.runTime = None

    ## c. Instance methods

    def create_vehicles(self):
        vehicles = []
        for v in range(self.parameters['Fleet']):
            vehicles.append(Vehicle(v)) #Corresponding to t, x, y of next availability
        return vehicles

    def run_simulation(self):
        print ('Simulation started...')
        timer = TicToc()
        timer.tic()
        for t in range(1, self.parameters['Timeslots']):
            print ('.', end = '')
            for v in range(self.parameters['Fleet']):
                if self.vehicles[v].available == t and len(self.rides_unalloc) > 0:
                    p_ratio_max = 0
                    r_select = None
                    p_select = 0
                    d_trans_ride_select = None
                    for r in self.rides_unalloc:
                        d_trans_s = abs(self.rides_matrix[r][0]-self.vehicles[v].x) + abs(self.rides_matrix[r][1]-self.vehicles[v].y)
                        d_trans_t = self.rides_matrix[r][4] - self.vehicles[v].available
                        d_trans = max(d_trans_s, d_trans_t)
                        d_ride = self.rides_matrix[r][7]
                        d_trans_ride = d_trans + d_ride
                        if t + d_trans_ride > self.rides_matrix[r][5]:
                            continue
                        if d_trans != d_trans_t:
                            p = d_ride
                        else:
                            p = self.rides_matrix[r][8]
                        p_ratio = p/d_trans_ride
                        if p_ratio > p_ratio_max:
                            p_ratio_max = 0
                            r_select = r
                            p_select = p
                            d_trans_ride_select = d_trans_ride
                    if r_select != None:
                        self.vehicles[v].allocate_ride(r_select)
                        self.rides_unalloc.remove(r_select)
                        self.vehicles[v].update_availability(d_trans_ride_select)
                        self.score += p_select
        print ()
        timer.toc('Simulation completed in')
        #self.performance = (round(100 * (self.score / self.score_max[0])) + "%%", round(100 * (self.score / self.score_max[1])) + "%%")
        self.status = 'Complete'
        

    def print_simulation_report(self):
        print ()
        print ('** SIMULATION REPORT **')
        print ()
        print ('Name: %s' % self.name)
        print ('Parameters: %s' % self.parameters)
        print ('Status: %s' % self.status)
        print ()
        #if self.runTime != None:
            #print (self.runTime)
        print ('Unallocated rides: %s' % len(self.rides_unalloc))
        print ('Score: %s' % self.score)
        print ('Max scores (excl./incl. bonus): (%s/%s)' % (self.score_max[0], self.score_max[1]))
        #if self.performance != None:
            #print ('Performance: %s' % self.performance)
        print ()

        self.score = None
        self.score_max = (self.rides['d_ride'].sum(), self.rides['b_ride'].sum())
        self.performance = None

    def output_results(self):
        if self.status == 'Complete':
            output_name = self.name[:-3] + '.out'
            output = open(output_name, 'w+')
            for v in self.vehicles:
                results_string = list(map(lambda x: str(x), v.rides_alloc))
                output.write(str(v.get_ride_count()) + ' ' + ' '.join(results_string) + '\n')
        else:
            print ('Simulation %s has not yet been run!' % self.name)

class Vehicle:

    ## a. Class variables

    ## b. Constructor

    def __init__(self, name):
        self.name = name
        self.x = 0
        self.y = 0
        self.available = 1
        self.rides_alloc = []

    ## c. Instance methods

    def get_ride_count(self):
        return len(self.rides_alloc)

    def allocate_ride(self, ride):
        self.rides_alloc.append(ride)

    def update_availability(self, time):
        self.available += time

class RideOrderBook:

    ## a. Class variables

    files = {'a': 'a_example.in',
            'b': 'b_should_be_easy.in',
            'c': 'c_no_hurry.in',
            'd': 'd_metropolis.in',
            'e': 'e_high_bonus.in'}

    parameterKeys = ['Rows', 'Columns', 'Fleet', 'Rides', 'Bonus', 'Timeslots']
    ''' Where:
        Rows = number of rows in the grid
        Columns = number of columns in the grid
        Fleet = number of vehicles in the fleet
        Rides = number of rides
        Bonus = per-ride bonus for starting the ride on time
        Timeslots = number of steps in the simulation '''
        
    dataHeaders = ['x1', 'y1', 'x2', 'y2', 't1', 't2']
    ''' Where:
        x1 = row of the starting intersection
        y1 = column of the starting intersection
        x2 = row of the finishing intersection
        y2 = column of the finishing intersection
        t1 = the earliest start for the ride
        t2 = the latest end for the ride '''

    ## b. Constructor

    def __init__(self, fileKey):
        self.name = self.files[fileKey]
        self.data = self.load_dataframe(self.files[fileKey])
        self.parameters = self.extract_parameters(self.parameterKeys, self.data)
        self.data.columns = self.dataHeaders
        self.run_preparatory_calculations()

    ## c. Instance methods

    def load_dataframe(self, filename):
        df = pd.read_csv(filename, delim_whitespace = True)
        return df

    def extract_parameters(self, keys, dataframe):
        parameters = {}
        for i in range(len(keys)):
            parameters[keys[i]] = round(float(dataframe.columns[i]))
        return parameters

    def run_preparatory_calculations(self):
        self.data['t_window'] = self.data.apply(lambda row: row['t2']-row['t1'], axis = 1)
        self.data['d_ride'] = self.data.apply(lambda row: abs(row['x2']-row['x1']) + abs(row['y2']-row['y1']), axis = 1)
        self.data['b_ride'] = self.data.apply(lambda row: row['d_ride'] + self.parameters['Bonus'], axis = 1)

    def remove_invalid_rides(self):
        self.data['valid?'] = self.data.apply(lambda row: row['d_ride'] <= row['t_window'], axis = 1)
        self.data = self.data.loc[self.data['valid?']]
        self.data.drop(columns = 'valid?')

###########################################################################################################################
###########################################################################################################################

def main():

    #Load data and simulation
    simulationData = RideOrderBook(sys.argv[1])
    simulation = SimulationGreedy(simulationData)

    #Run simulation or view simulation summary
    if sys.argv[2] == 'run':
        simulation.run_simulation()
        simulation.output_results()
        simulation.print_simulation_report()
    elif sys.argv[2] == 'view':
        simulation.print_simulation_report()
    else:
        print ('System argument error!')

main()

    

    ### 6. SAVE OUTPUT

    #print_output(results)