#Load packages
import numpy as np
import pandas as pd
import random
from docplex.mp.model import Model

def efficiency(sol, q, num_nurses, num_shifts, num_units, num_days, Ls, file):
    import statistics
    table_nu = np.zeros((num_nurses, num_units))
    table_nu2 = np.zeros((num_nurses, num_units))
    c_time = np.zeros(num_units)
    c_time_hu =  np.zeros(num_units)

    for m in sol:
        #print(m)
        if m[0] == 'y':
            split_name = m.split('_')
            i = int(split_name[1])
            s = int(split_name[2])
            j = int(split_name[3])
            d = int(split_name[4])

            # print('y' + '_' + str(i) + '_' + str(s) + '_' + str(j) + '_' + str(d) + ' = 1')
            table_nu[i - 1, j - 1] = table_nu[i - 1, j - 1] + q[i - 1, j - 1] * Ls[s - 1]
            table_nu2[i - 1, j - 1] = table_nu2[i - 1, j - 1] + Ls[s - 1]
            c_time[j - 1] = c_time[j - 1] + Ls[s - 1]



    nurses_area = np.array(pd.read_excel(file, sheet_name='Area', header=None, index_col=0))

    ini_ = 0
    for i in range(num_units):
        fin_ = int(nurses_area[i, 0] + ini_)
        c_time_hu[i] = np.sum(table_nu[ini_:fin_, i])
        ini_ = fin_

    time_perunit = np.sum(table_nu, axis=0)
    eff = time_perunit / c_time
    #eff = statistics.mean(eff)
    eff_byunits = c_time_hu / c_time

    #c_time - Tiempo total por unidad
    #table_nu - Matriz de tiempo trabajdo ponderados
    #time_perunit - Suma de tiempos trabajados ponderados por unidad
    #eff = effiencia por unidad considerando qij
    #table_nu2 = tiempos totales trabajados por enfermera i y unidad j
    #c_time_hu  tiempo trabajado en home unit por unidad j

    return c_time, table_nu, time_perunit, eff, table_nu2, eff_byunits

def extract_Ij(sol, num_nurses, num_units, I_j_initial):
    I_j = {}
    for i in range(1, num_units+1):
        I_j[i] = []
    for i in range(1, num_nurses+1):
        for j in range(1, num_units+1):
            if sol.get_value('w' + '_' + str(i) + '_' + str(j)) == 1:
                I_j[j] = I_j[j] + [i]

    required_pu = np.zeros((1, num_units))

    for i in range(num_units):
        required_pu[0, i] = int(len(I_j[i+1]) - len(I_j_initial[i+1]))

    return I_j, required_pu

def read_data3_Param(file):
    # Create the parameter HUi from table with number of nurses per area
    # Cross_conf 1 - Chaining, 2 - Reciprocal pairs, 3- n to all(n), 4 - all to all, Default not cross-training
    nurses_area = np.array(pd.read_excel(file, sheet_name='Area', header=None, index_col=0))
    Param_values = pd.read_excel(file, sheet_name='Param_values', index_col=0, header=None)

    num_units = int(Param_values.iloc[7, 0])
    nurse_num = int(Param_values.iloc[10, 0])
    num_days = int(Param_values.iloc[8, 0])
    num_periods = int(Param_values.iloc[9, 0])
    num_shifts = int(Param_values.iloc[11, 0])

    # Sets
    J = np.array(list(range(1, num_units + 1)))  # Units
    I = np.array(list(range(1, nurse_num + 1)))  # Nurses
    S = np.array(list(range(1, num_shifts + 1)))  # Shifts
    D = np.array(list(range(1, num_days + 1))) # Days
    P = np.array(list(range(1, num_periods + 1)))  # Periods
    d_dummie = D.copy()
    D_0 = np.union1d(0, D)
    D_N = D_0[0:len(D_0) - 1]
    Dabs = len(D)
    Pabs = len(P)

    # GENERATED DATA
    # Prelocate
    HUi = np.array([0]*nurse_num)
    Wi = np.array([0] * nurse_num)


    OTi = np.ones((1, nurse_num))*int(Param_values.iloc[12, 0])
    OTi = OTi[0]

    ini_ = 0
    for i in range(num_units):
        fin_ = int(nurses_area[i, 0] + ini_)
        Wi[ini_:fin_] = nurses_area[i, 1] # NewLine
        HUi[ini_:fin_] = i + 1
        ini_ = fin_

    """
    req = pd.read_excel(file, sheet_name= 'D' + str(demand_conf))
    # Prelocate
    QMin = np.zeros((num_units, num_days, num_periods))  # [TABLE [UNIT, DAY, PERIOD]] minimum demand for nurses in unit j on day d in period p
    QNPR = np.zeros((num_units, num_days, num_periods))  # yisj0 # This parameter I think goes with the constraints.

    for i in range(0, num_units):
        for j in range(0, num_days):
            for k in range(0, num_periods):
                filt = (req['Unit'] == i + 1) & (req['day'] == j + 1) & (req['period'] == k + 1)
                # print(str(i+1) + str(j+1) + str(k+1))
                QMin[i, j, k] = req.loc[filt, 'min_req']
                QNPR[i, j, k] = req.loc[filt, 'max_req']
    """

    # Shift related parameters
    s_info = pd.read_excel(file, sheet_name='ShiftsIn')
    Begs = np.array(s_info.iloc[:, 1])  # LIST [List of first working periods] 1 first working period in shift s
    Ends = np.array(s_info.iloc[:, 2])  # LIST [List of end working periods]
    Ls = np.array(s_info.iloc[:, 3])  # LIST length of shift s (in periods)

    # Single value parameters
    Rmin = int(Param_values.iloc[0, 0])  # NUMBER Minimun  rest time between shifts
    H = Param_values.iloc[1, 0]  # minimum proportion of regular working time spent in the home unit
    CDmin = int(Param_values.iloc[2, 0])  # costs of each nurse missing to cover minimum demand
    Cnpr = Param_values.iloc[3, 0]  # costs of each nurse missing to satisfy target demand
    Cot = Param_values.iloc[4, 0]  # costs for each overtime hour
    StayM = int(Param_values.iloc[5, 0])  # minimum number of consecutive days a nurse is assigned to one particular unit
    StrMax = int(Param_values.iloc[6, 0])  # maximum stretch of consecutive on duty working days

    # Tables
    asp_info = pd.read_excel(file, sheet_name='Asp', index_col=[0])
    Asp = np.array(asp_info.iloc[:, :])  # TABLE [Shifts, vrs periods]  1, if shift s covers period p

    return Begs, Ends, Ls, HUi, Wi, OTi, Rmin, H, CDmin, Cnpr, Cot, StayM, StrMax, J, I, S, D, D_0, D_N, P, Dabs, Pabs, Asp, num_units, nurse_num, nurses_area, num_days

def cross_policy2(file, cross_conf, Intensityp, breadth, num_units, nurse_num, chaining_mode): # MODIFIED FROM PREVIOUS ON 21/04/21
    # More nurses example - Create the Ij flexible configuration
    #Breadth = 1  # Number of units a nurse is applicable to
    #Intensity = 2  # Percentaje or number of cross trained nurses in a unit
    #Depth = 1

    nurses_area = np.array(pd.read_excel(file, sheet_name='Area', header=None, index_col=0))
    if Intensityp < 1: # careful no full flex
        Intensity = np.ceil(np.transpose(nurses_area)[0]*Intensityp)

        #Intensity = int(int(np.min(nurses_area))*Intensityp) #I have to correct this. it has to be 50% of the unit, for example
    else:
        Intensity = int(Intensityp) # np.array(int(Intensityp))

    ini_ = 0
    I_j = {}
    # I_j inicial
    for i in range(num_units):
        fin_ = int(nurses_area[i, 0] + ini_)
        #HUi[ini_:fin_] = i + 1
        I_j[i + 1] = np.array(list(range(ini_ + 1, fin_ + 1)))
        ini_ = fin_

    I_j_initial = I_j.copy()

    # Type of configuration
    # 1 - Chaining, 2 - Reciprocal pairs, 3- n to all(n), 4 - all to all, 5 one for each
    if cross_conf == 1:
        # Chaining
        if Intensityp >= 1:
            # 1 - Chaining
            if Intensity == 1 and breadth == 1:
                for i in range(1, num_units + 1):
                    if i < num_units:
                        I_j[i + 1] = np.append(I_j[i + 1], I_j[i][:Intensity])
                    else:
                        I_j[1] = np.append(I_j[1], I_j[num_units][:Intensity])
                #print(I_j)

            elif breadth == 1 and chaining_mode == 1:
                for i in range(1, num_units + 1):
                    if i < num_units:
                        I_j[i + 1] = np.append(I_j[i + 1], I_j[i][:Intensity])
                    else:
                        I_j[1] = np.append(I_j[1], I_j[num_units][:Intensity])

            elif Intensity == 2 and breadth == 1 and chaining_mode == 2:
                Intensity = 2
                breadth = 1

                unit_list = []
                unit_list2 = []
                unit_list3 = []

                add2 = list(range(1, num_units + 1))
                add3 = []

                for i in range(Intensity):
                    add3 = add3 + [i] * breadth

                cont1 = 0
                for i in range(1, num_units + 1):
                    unit_list = unit_list + ([i] * (Intensity * breadth))

                for i in range(Intensity * breadth + 2):
                    unit_list2 = unit_list2 + add2

                for i in range(1, num_units + 1):
                    unit_list3 = unit_list3 + add3

                unit_list = np.array(unit_list)
                unit_list2 = np.array(unit_list2)
                unit_list3 = np.array(unit_list3)
                av_units = np.ones(num_units) * (Intensity * breadth)
                unit_list2al = np.zeros((num_units * Intensity * breadth))

                cont2 = 0
                cont3 = 0
                cont4 = 0
                passed = 0
                itera = 0

                for i in unit_list:

                    if cont4 == Intensity * breadth:
                        cont4 = 0
                        cont3 = cont3 - 1

                    for j in unit_list2[cont3 + 1:]:  # +1
                        # print(unit_list2[cont3+1:])

                        if i == j:
                            cont3 = cont3 + 1
                            passed = passed + 1
                            pass
                        else:
                            # print(str(i) +' - '+ str(j))
                            if av_units[j - 1] != 0:
                                if cont4 == 0 and itera != 1:
                                    unit_list2al[itera - passed] = j

                                else:
                                    unit_list2al[itera - passed] = j
                                    # cont3 = cont3 + 1
                                av_units[j - 1] = av_units[j - 1] - 1
                                cont3 = cont3 + 1
                            else:  # look for the following available
                                for k in range(num_units):
                                    if av_units[k] > 0:
                                        unit_list2al[itera - passed] = k + 1
                                        av_units[k] = av_units[k] - 1
                                        cont3 = cont3 + 1
                                        break
                            break
                    cont4 = cont4 + 1
                    itera = itera + 1
                for j in range(num_units * Intensity):
                    I_j[unit_list2al[j]] = np.append(I_j[unit_list2al[j]], I_j[unit_list[j]][unit_list3[j]])

                print(I_j)

            elif Intensity == 1 and breadth == 2 and chaining_mode == 2:

                unit_list = []
                unit_list2 = []
                unit_list3 = [0] * (num_units * breadth * Intensity)

                add2 = list(range(1, num_units + 1))

                cont1 = 0
                for i in range(1, num_units + 1):
                    unit_list = unit_list + ([i] * (Intensity * breadth))

                for i in range(Intensity * breadth + 2):
                    unit_list2 = unit_list2 + add2

                unit_list = np.array(unit_list)
                unit_list2 = np.array(unit_list2)
                unit_list3 = np.array(unit_list3)
                av_units = np.ones(num_units) * (Intensity * breadth)
                unit_list2al = np.zeros((num_units * Intensity * breadth))

                cont2 = 0
                cont3 = 0
                cont4 = 0
                passed = 0
                itera = 0

                for i in unit_list:

                    if cont4 == Intensity * breadth:
                        cont4 = 0
                        cont3 = cont3 - 1

                    for j in unit_list2[cont3 + 1:]:  # +1
                        if i == j:
                            cont3 = cont3 + 1
                            passed = passed + 1
                            pass
                        else:
                            # print(str(i) + ' - ' + str(j))
                            if av_units[j - 1] != 0:
                                if cont4 == 0 and itera != 1:
                                    unit_list2al[itera - passed] = j

                                else:
                                    unit_list2al[itera - passed] = j
                                    # cont3 = cont3 + 1
                                av_units[j - 1] = av_units[j - 1] - 1
                                cont3 = cont3 + 1
                            else:  # look for the following available
                                for k in range(num_units):
                                    if av_units[k] > 0:
                                        unit_list2al[itera - passed] = k + 1
                                        av_units[k] = av_units[k] - 1
                                        cont3 = cont3 + 1
                                        break
                            break
                    cont4 = cont4 + 1
                    itera = itera + 1
                for j in range(num_units * Intensity * breadth):
                    I_j[unit_list2al[j]] = np.append(I_j[unit_list2al[j]], I_j[unit_list[j]][unit_list3[j]])

            else:
                ## CORREGIR PARA EL CASO DE INTENSITY < 0  This is gonna be messy
                # Intensity >= 2 and breadth >= 2:
                unit_list = []
                unit_list2 = []
                unit_list3 = []

                add2 = list(range(1, num_units + 1))
                add3 = []
                for i in range(Intensity):
                    add3 = add3 + [i] * breadth

                cont1 = 0
                for i in range(1, num_units + 1):
                    unit_list = unit_list + ([i] * (Intensity * breadth))

                for i in range(Intensity * breadth + num_units + 6):  # CHECK NOT SURE #Added 3 on 28/04/2021  # The six was a 3 I changed
                    unit_list2 = unit_list2 + add2

                for i in range(1, num_units + 1):
                    unit_list3 = unit_list3 + add3

                unit_list = np.array(unit_list)
                unit_list2 = np.array(unit_list2)
                unit_list3 = np.array(unit_list3)
                av_units = np.ones(num_units) * (Intensity * breadth)
                unit_list2al = np.zeros((num_units * Intensity * breadth))

                cont00 = 0
                cont2 = 0
                cont3 = 0
                passed = 0
                for i in unit_list:
                    #if cont00 == 92:
                       #oko = 2

                    cont00 += 1
                    if cont00 == 92:
                        print('---------------' + str(cont00))

                    for j in unit_list2[cont3 + 1:]:  # +1
                        #print(unit_list2[cont3 + 1:])
                        if i == j:
                            cont3 = cont3 + 1
                            passed = passed + 1
                            pass
                        else:
                            # print(str(i) +' - '+ str(j))
                            if av_units[j - 1] != 0:
                                unit_list2al[cont3 - passed] = j
                                av_units[j - 1] = av_units[j - 1] - 1
                                cont3 = cont3 + 1
                            else:  # look for the following available
                                for k in range(num_units):
                                    if av_units[k] > 0:
                                        unit_list2al[cont3 - passed] = k + 1
                                        av_units[k] = av_units[k] - 1
                                        cont3 = cont3 + 1
                                        break
                            break
                #print(unit_list2al)

                for j in range(num_units * Intensity * breadth):
                    I_j[unit_list2al[j]] = np.append(I_j[unit_list2al[j]], I_j[unit_list[j]][unit_list3[j]])

        else:
            #This part was modified
            # I think it is ok Would have to check and validate
            av_units = {}
            for j in range(1, num_units + 1):
                av_units[j] = list(range(1, num_units + 1))
                av_units[j].remove(j)

            count1 = 1
            count2 = 0

            for j in range(1, num_units + 1):
                for i in I_j[j][0: int(Intensity[j - 1])]:
                    # print('nurse#:' + str(i))
                    # print( 'nurses NUmber: ' +  str(int(Intensity[j-1]))
                    # if i == 34:
                    #   print('*********')
                    if count1 > num_units:
                        count1 = 1

                    for k in range(1, num_units + 1):
                        # print(str(j) + ' ' + str(count1))
                        if count1 > num_units:
                            count1 = 1

                        if j != k and (i not in I_j[count1]):
                            I_j[count1] = I_j[count1] + [i]
                            # print(I_j)
                            count2 += 1
                            count1 += 1
                            if count1 > num_units:
                                count1 = 1

                            if count2 == breadth:
                                count2 = 0
                                if count1 == num_units:
                                    count1 = 1
                                break
                        else:
                            count1 += 1


                # print(I_j)
    elif cross_conf == 2:
        # 2 - Reciprocal

        # if Intensity > np.min(nurses_area):
        #    Intensity = np.min(nurses_area)
        if Intensityp != 0:
            if Intensityp >= 1:
                if (num_units % 2) == 0:
                    for i in list(range(1, num_units + 1, 2)):
                        I_j[i] = np.append(I_j[i], I_j[i + 1][:Intensity])
                        I_j[i + 1] = np.append(I_j[i + 1], I_j[i][:Intensity])
                else:
                    for i in list(range(1, num_units, 2)):
                        I_j[i] = np.append(I_j[i], I_j[i + 1][:Intensity])
                        I_j[i + 1] = np.append(I_j[i + 1], I_j[i][:Intensity])
            else:
                if (num_units % 2) == 0:
                    for i in list(range(1, num_units + 1, 2)):
                        I_j[i] = np.append(I_j[i], I_j[i + 1][:int(Intensity[i+1-1])])
                        I_j[i + 1] = np.append(I_j[i + 1], I_j[i][:int(Intensity[i-1])])
                else:
                    for i in list(range(1, num_units, 2)):
                        I_j[i] = np.append(I_j[i], I_j[i + 1][:int(Intensity[i+1-1])])
                        I_j[i + 1] = np.append(I_j[i+1], I_j[i][:int(Intensity[i-1])])
        else:
            pass
    elif cross_conf == 3:
        # 3 - n to all
        if Intensityp != 0:
            for i in range(1, num_units + 1):
                for j in range(1, num_units + 1):
                    if i != j:
                        if Intensityp >= 1:
                            I_j[i] = np.append(I_j[i], I_j[j][:Intensity])
                        else:
                            I_j[i] = np.append(I_j[i], I_j[j][:int(Intensity[j-1])])
        else:
            pass
    elif cross_conf == 6:
        # 4 all to all
        for i in range(1, num_units + 1):
            I_j[i] = np.array(list(range(1, nurse_num + 1)))
    elif cross_conf == 5:
        # one for each
        for i in range(1, num_units + 1): #salidas
            cont = 0
            for j in range(1, num_units + 1):
                if i != j:
                    I_j[j] = np.append(I_j[j], I_j[i][cont])
                    cont = cont + 1
    else:
        pass
    return I_j, I_j_initial

def productivity_parameter(I, J, I_j, prod):
    q = np.zeros((len(I), len(J)))

    for i in I:
        for j in J:
            if (i in I_j[j]) == 1:
                q[i-1, j-1] = 1
            else:
                q[i - 1, j - 1] = prod
    '''
    for j in J:
        not_in = np.setdiff1d(I, I_j[j])
        for k in range(len(not_in)):
            q[not_in[k]-1, j-1] = 0
    '''

    return q