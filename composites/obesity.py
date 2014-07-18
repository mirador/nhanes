'''
Calculates the Obesity composite using the CDC BMI tables

@author: Mahan Nekoui, Andres Colubri
'''

import csv

maleCutoff85 = [0] * 20
maleCutoff95 = [0] * 20
femaleCutoff85 = [0] * 20
femaleCutoff95 = [0] * 20

def init():
    males = []       
    with open("males.tsv") as tsv:
        for line in csv.reader(tsv, dialect="excel-tab"):
            males.append(line)

    maleCutoff85Index = males[0].index("85th Percentile BMI Value")
    maleCutoff95Index = males[0].index("95th Percentile BMI Value")
    
    maleCutoff85sum = {}
    maleCutoff95sum = {}
    for row in males[1: len(males)]:
        yr = int(float(row[0]) / 12)
        cutoff85 = float(row[maleCutoff85Index])
        if yr in maleCutoff85sum:
            maleCutoff85sum[yr].append(cutoff85)
        else:
            maleCutoff85sum[yr] = [cutoff85]
            
        cutoff95 = float(row[maleCutoff95Index])
        if yr in maleCutoff95sum:
            maleCutoff95sum[yr].append(cutoff95)
        else:
            maleCutoff95sum[yr] = [cutoff95]
     
    for yr in range(2, 20):         
        sum = 0
        for bmi in maleCutoff85sum[yr]:
            sum = sum + bmi
        sum = sum / len(maleCutoff85sum[yr])
        maleCutoff85[yr] = sum

        sum = 0
        for bmi in maleCutoff95sum[yr]:
            sum = sum + bmi
        sum = sum / len(maleCutoff95sum[yr])
        maleCutoff95[yr] = sum
        
#     print maleCutoff85       
#     print maleCutoff95
    
    females = []       
    with open("females.tsv") as tsv:
        for line in csv.reader(tsv, dialect="excel-tab"):
            females.append(line)            
    
    femaleCutoff85Index = females[0].index("85th Percentile BMI Value")
    femaleCutoff95Index = females[0].index("95th Percentile BMI Value")
    
    femaleCutoff85sum = {}
    femaleCutoff95sum = {}
    for row in females[1: len(females)]:
        yr = int(float(row[0]) / 12)
        cutoff85 = float(row[femaleCutoff85Index])
        if yr in femaleCutoff85sum:
            femaleCutoff85sum[yr].append(cutoff85)
        else:
            femaleCutoff85sum[yr] = [cutoff85]
            
        cutoff95 = float(row[femaleCutoff95Index])
        if yr in femaleCutoff95sum:
            femaleCutoff95sum[yr].append(cutoff95)
        else:
            femaleCutoff95sum[yr] = [cutoff95]
     
    for yr in range(2, 20):         
        sum = 0
        for bmi in femaleCutoff85sum[yr]:
            sum = sum + bmi
        sum = sum / len(femaleCutoff85sum[yr])
        femaleCutoff85[yr] = sum

        sum = 0
        for bmi in femaleCutoff95sum[yr]:
            sum = sum + bmi
        sum = sum / len(femaleCutoff95sum[yr])
        femaleCutoff95[yr] = sum
        
#     print femaleCutoff85       
#     print femaleCutoff95

def variables():
    return ["RIAGENDR", "RIDAGEYR", "BMXBMI"]

def get_name():
    return "OBESITY"
    
def get_title():    
    return "Overweight/Obesity status"
    
def get_type():    
    return "category"
    
def calculate(values):
    gender = values ["RIAGENDR"]
    age = values["RIDAGEYR"]
    bmi = values["BMXBMI"]
    
    if '\N' in [gender, age, bmi]:
        obesity = '\N'
    else:
        age = int(age)
        
        gender = int(gender)
        bmi = float(bmi)
        
        if 20 <= age:
            if 30.0 <= bmi:
                obesity = 3
            elif 25.0 <= bmi:                
                obesity = 2
            else:
                obesity = 1
                
        elif age < 2:
            obesity = '\N'
        
        else:
            # Age is between 2 and 19
            if gender == 1:
                cutoff85 = maleCutoff85[age]
                cutoff95 = maleCutoff95[age]
                
                if cutoff95 <= bmi:
                    obesity = 3
                elif cutoff85 <= bmi:
                    obesity = 2                
                else:
                    obesity = 1
            else:
                cutoff85 = femaleCutoff85[age]
                cutoff95 = femaleCutoff95[age]
                
                if cutoff95 <= bmi:
                    obesity = 3
                elif cutoff85 <= bmi:
                    obesity = 2                
                else:
                    obesity = 1              

#     print gender, age, bmi, obesity 
    return obesity
        
def get_range(): 
    return "1:Normal;2:Overweight;3:Obese"
    
def get_table(): 
    return "Health Indicators"