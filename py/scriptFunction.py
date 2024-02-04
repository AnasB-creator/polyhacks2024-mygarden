
def scriptAnalysis(city, areaGarden, coeffValue, coeffCal, coeffCO2, coeffTime):
    """Function that takes into input the user desired values and outputs a gardening plan, The function will be used
    inside R shiny that is why it is so compact"""
    import numpy as np
    import pandas as pd
    import pulp as plp
    import psycopg2
    # from sqlalchemy import create_engine
    from sklearn.preprocessing import MinMaxScaler



    # Connection to the DataBase
    connStr = f'postgresql://{"roppa070"}:{"xqchfg1d2YIb"}@{"ep-soft-unit-a5tg3j5a.us-east-2.aws.neon.tech"}/{"dev"}?sslmode=require'

    conn = psycopg2.connect(connStr)

    # Cities hardiness and latitude, longitude downloaded
    citiesDf = pd.read_sql('SELECT * FROM cities', con=conn)

    # Plants dataset loading into a dataframe
    plantsDf = pd.read_sql('SELECT * FROM plants', con=conn)

    # Make sure to close the connection once done
    conn.close()

    # engine = create_engine(connStr)
    #
    # # Cities hardiness and latitude, longitude downloaded
    # citiesDf = pd.read_sql_table('cities', con=engine)
    #
    # # Plants dataset loading into a dataframe
    # plantsDf = pd.read_sql_table('plants', con=engine)

    # Initialize the MinMaxScaler
    scaler = MinMaxScaler()

    # Normalization of the values that will be used for the objective function of the daily optimization in our heuristic search
    plantsDf['avgpriceperkilocadnormalized'] = scaler.fit_transform(plantsDf[['avgpriceperkilocad']])
    plantsDf['avgco2consumptionperkilonormalized'] = scaler.fit_transform(plantsDf[['avgco2consumptionperkilo']])
    plantsDf['avgcaloriesbykilonormalized'] = scaler.fit_transform(plantsDf[['avgcaloriesbykilo']])
    plantsDf['growthdurationaveragenormalized'] = scaler.fit_transform(plantsDf[['growthdurationaverage']])

    # Set a random seed for reproducibility
    np.random.seed(42)

    # Generate random integer values for Min_Area_Per_Kg between 1 and 5 for each plant, it will represent the minimum area needed per kg per plant
    plantsDf['minAreaPerKg'] = np.random.randint(1, 5, size=len(plantsDf))

    def optimalPlantationForSpace(plantsDf, earningsCoeff, co2Coeff, caloriesCoeff, growthCoeff,
                                  maxAreaRatioPerPlant, totalArea, remainingArea, minCropsPlanted,
                                  currentDifferentCropsPlanted, scalableAreaPerPlant):
        """Function that returns the ideal plants to allocate the space to given a specific area, and other parameters"""
        # Define the problem
        prob = plp.LpProblem("Optimized_Farming", plp.LpMaximize)

        # Decision variables for areas
        areaVars = plp.LpVariable.dicts("Area", plantsDf['commonname'], lowBound=0, cat=plp.LpInteger)

        # Binary decision variables for whether a crop is planted
        isPlantedVars = plp.LpVariable.dicts("Is_Planted", plantsDf['commonname'], cat='Binary')

        # Objective function
        prob += plp.lpSum([(earningsCoeff * areaVars[crop] *
                        plantsDf.loc[plantsDf['commonname'] == crop, 'avgpriceperkilocadnormalized'].values[0] *
                        plantsDf.loc[plantsDf['commonname'] == crop, 'avgproductionpersqmeter'].values[0])
                       + (co2Coeff * areaVars[crop] *
                          plantsDf.loc[plantsDf['commonname'] == crop, 'avgco2consumptionperkilonormalized'].values[0] *
                          plantsDf.loc[plantsDf['commonname'] == crop, 'avgproductionpersqmeter'].values[0]) +
                       (caloriesCoeff * areaVars[crop] *
                        plantsDf.loc[plantsDf['commonname'] == crop, 'avgcaloriesbykilonormalized'].values[0] *
                        plantsDf.loc[plantsDf['commonname'] == crop, 'avgproductionpersqmeter'].values[0])
                       - (growthCoeff *
                          plantsDf.loc[plantsDf['commonname'] == crop, 'growthdurationaveragenormalized'].values[0])
                       for crop in plantsDf['commonname']]), "Objective"

        # Constraints
        # Total area constraint
        prob += plp.lpSum([areaVars[crop] for crop in plantsDf['commonname']]) <= remainingArea, "Total_Area_Constraint"

        # At least a certain number of plants is planted if there is enough space for a second one , and if current different plant is inferior to 2 there is the need to diversify
        if remainingArea >= scalableAreaPerPlant and currentDifferentCropsPlanted < 2:
            prob += plp.lpSum \
                ([isPlantedVars[crop] for crop in plantsDf['commonname']]) >= minCropsPlanted, "Min_Crops_Planted"

        # Minimum Area Required for each plant per kg
        for crop in plantsDf['commonname']:
            minAreaPerKg = plantsDf.loc[plantsDf['commonname'] == crop, 'minAreaPerKg'].values[0]
            prob += areaVars[crop] >= isPlantedVars[crop] * minAreaPerKg, f"Min_Area_{crop}"

        # Max ratio occupied by each plant
        for crop in plantsDf['commonname']:
            prob += areaVars[crop] <= remainingArea * maxAreaRatioPerPlant, f"Max_Area_{crop}"

        # Linking areaVars to isPlantedVars to ensure a crop is considered planted if it has area allocated
        for crop in plantsDf['commonname']:
            prob += areaVars[crop] >= isPlantedVars[crop] * 0.01, f"Link_{crop}"  # 0.01 as a minimum area to consider a crop planted

        # Problem Solving, where the magic happens
        prob.solve()

        # Creation of the return dataframe of the best plants with their corresponding area
        filteredData = {"commonname": [], "AllocatedArea": []}
        for value in prob.variables():
            if ("Area" in value.name) and (value.varValue > 0):
                cropName = " ".join(value.name.split("_")[1:])
                filteredData["commonname"].append(cropName)
                filteredData["AllocatedArea"].append(value.varValue)

        # Create a DataFrame with the result of the optimization
        allocatedAreaDf = pd.DataFrame(filteredData)

        return allocatedAreaDf

    # Application of the optimizing function

    # Definition of the optimization parameters

    # Coefficients defined by the user in view of his prioritization
    earningsCoeff = coeffValue  # Prioritize earnings
    co2Coeff = coeffCO2  # represent the CO2 reduction
    caloriesCoeff = coeffCal  # Prioritize calorie content
    growthCoeff = coeffTime
    maxAreaRatioPerPlant = 0.60
    # Total area of the garden and total area available variable that will be dynamically changed
    totalArea = areaGarden
    remainingArea = totalArea
    totalPlanDays = 365

    # At least two types of crops are planted
    minCropsPlanted = 2
    # Variety of the current planted plants
    currentDifferentCropsPlanted = 0
    # Area after which we start to consider adding a second plant
    scalableAreaPerPlant = 2
    # Maximum number of time that we replant the same plant in the same gardening plan
    numberOfPlantingMax = 3
    # City of residence of the user and extraction of its hardiness
    cityName = city
    cityHardiness = citiesDf.loc[citiesDf["city_name"] == cityName]["hardiness"].iloc[0]

    # Creation of the DataFrame that will be populated with the gardening plan
    columns = ['commonname', 'startDay', 'endDay', "areaTaken", "kgCultivated", "value", "co2Comsumption", "calories"]
    plantationsDf = pd.DataFrame(columns=columns)

    # Initialization of the counter of the number of times a plant has been planted
    plantsDf["numberOfPlanting"] = 0

    # Optimization that simulates day by the day gardening calendar of the year and optimizes linearly its objective function

    for dayNumber in range(1, totalPlanDays + 1):
        print(remainingArea)
        availablePlantsDf = plantsDf.loc[((plantsDf["growthwindowstart"] - 1) * 30 < dayNumber) &
                    ((plantsDf["growthwindowend"] * 30) >= dayNumber) & (
                                                     plantsDf["numberOfPlanting"] < numberOfPlantingMax) & (
                                                     plantsDf["minhardinesszone"] <= cityHardiness) & (
                                         (plantsDf["maxhardinesszone"] >= cityHardiness))]

        if not plantationsDf.empty:
            plantationsDfUptodate = plantationsDf.loc[plantationsDf["endDay"] >= dayNumber]
            plantationsDfRejected = plantationsDf.loc[plantationsDf["endDay"] == dayNumber + 1]
            currentDifferentCropsPlanted = plantationsDfUptodate["commonname"].nunique()

            if not plantationsDfRejected.empty:
                for index, row in plantationsDfRejected.iterrows():
                    remainingArea += row["areaTaken"]

        if remainingArea != 0:

            allocatedCropsDf = optimalPlantationForSpace(availablePlantsDf, earningsCoeff, co2Coeff, caloriesCoeff,
                                                         growthCoeff, maxAreaRatioPerPlant, totalArea, remainingArea,
                                                         minCropsPlanted, currentDifferentCropsPlanted,
                                                         scalableAreaPerPlant)

            if not allocatedCropsDf.empty:

                for index, row in allocatedCropsDf.iterrows():
                    cropFullData = plantsDf.loc[plantsDf["commonname"] == row["commonname"]]
                    plantsDf.loc[plantsDf['commonname'] == row["commonname"], 'numberOfPlanting'] += 1
                    plantation = {
                        'commonname': row["commonname"],
                        'startDay': dayNumber + 0.0,
                        'endDay': dayNumber + cropFullData["growthdurationaverage"].iloc[0],
                        "areaTaken": row["AllocatedArea"],
                        "kgCultivated": cropFullData["avgproductionpersqmeter"].iloc[0] * row["AllocatedArea"],
                        "value": cropFullData["avgpriceperkilocad"].iloc[0] *
                                 cropFullData["avgproductionpersqmeter"].iloc[0] * row["AllocatedArea"],
                        "co2Comsumption": cropFullData["avgco2consumptionperkilo"].iloc[0] *
                                          cropFullData["avgproductionpersqmeter"].iloc[0] * row["AllocatedArea"],
                        "calories": cropFullData["avgcaloriesbykilo"].iloc[0] *
                                    cropFullData["avgproductionpersqmeter"].iloc[0] * row["AllocatedArea"]
                    }

                    newRowsDf = pd.DataFrame([plantation])
                    plantationsDf = pd.concat([plantationsDf, newRowsDf], ignore_index=True)

                    remainingArea -= row["AllocatedArea"]

    return plantationsDf


if __name__ == '__main__':
    print(scriptAnalysis("Vancouver", 50, 0.5,0.5,0.2,0.6))
