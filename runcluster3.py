from mpi4py.futures import MPIPoolExecutor
import numpy as np
import pandas as pd

from nurse_functionsE2 import *

Demands = list(range(100))
H_levels = [0.5]
Instances = ['n20I1.xls', 'n30I1.xls', 'n40I1.xls']
investments = list(range(25))  #  will correspond to a maximum level of investment by  instance I'd say  30% of the total trainings?
ex_times = [10]

def exp3_investment(Demand, H, file, ex_time, inv):
    Begs, Ends, Ls, HUi, Wi, OTMaxi, Rmin, _, CDmin, Cnpr, Cot, StayM, StrMax, J, I, S, D, D_0, D_N, P, Dabs, Pabs, Asp, num_units, nurse_num, nurses_area, num_days = read_data3_Param(file)
    QMin, QNPR = read_data3_Demand_100Exp(file, Demand)

    I_j, I_j_initial = cross_policy2(file, 0, 0, 0, num_units, nurse_num, 0)
    q = productivity_parameter(I, J, I_j_initial, 0.5)

    _sol, objective, kpis = midterm_rostering2c_investment(Begs, Ends, Ls, HUi, Wi, OTMaxi, I_j, Rmin, H, CDmin, Cnpr, Cot,
                                                           StayM, StrMax, QMin, QNPR, J, I, S, D, D_0, D_N, P, Dabs, Pabs,
                                                           Asp, q, ex_time, inv, 'None')

    df1 = pd.DataFrame.from_dict(_sol.as_dict(), orient='index')
    df2 = pd.DataFrame.from_dict(kpis, orient='index')

    df1.to_csv(r'ResultsEXP3\\'  + str(file[1:5]) + '_D' + str(int(Demand)) + '_H' + str(int(H * 10)) + '_I' + str(inv) + '_SOL.csv', decimal=",", sep=';')
    df2.to_csv(r'ResultsEXP3\\'  + str(file[1:5]) + '_D' + str(int(Demand)) + '_H' + str(int(H * 10)) + '_I' + str(inv) + '_KPIS.csv', decimal=",", sep=';')
    
    #with pd.ExcelWriter(r'ResultsEXP3\\'  + str(file[1:5]) + '_D' + str(int(Demand)) + '_H' + str(int(H * 10)) + '_I' + str(inv) + '.xlsx') as writer:
    #    df1.to_excel(writer, sheet_name='solution')
    #    df2.to_excel(writer, sheet_name='kpis')

if __name__ == '__main__':
    with MPIPoolExecutor() as executor:
        executor.starmap(exp3_investment, [(Demand, H, file, ex_time, inv) for Demand in Demands 
                                                                           for H in H_levels 
                                                                           for file in Instances 
                                                                           for ex_time in ex_times 
                                                                           for inv in investments])







