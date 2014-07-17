'''
Calculates the Obesity composite using the CDC BMI tables

@author: Mahan Nekoui, Andres Colubri
'''

import csv

maleAges = []
maleCutoff85 = []
maleCutoff95 = []
femaleAges = []
femaleCutoff85 = []
femaleCutoff95 = []

def init():
    males = []       
    with open("males.tsv") as tsv:
        for line in csv.reader(tsv, dialect="excel-tab"):
            males.append(line)

    maleCutoff85Index = males[0].index("85th Percentile BMI Value")
    maleCutoff95Index = males[0].index("95th Percentile BMI Value")
    
    for row in males:
        try:
            maleAges.append(float(row[0]))
        except ValueError:
            maleAges.append(row[0])
        
        try:
            maleCutoff85.append(float(row[maleCutoff85Index]))
        except ValueError:
            maleCutoff85.append(row[maleCutoff85Index])

        try:
            maleCutoff95.append(float(row[maleCutoff95Index]))
        except ValueError:
            maleCutoff95.append(row[maleCutoff95Index])
    
    females = []       
    with open("females.tsv") as tsv:
        for line in csv.reader(tsv, dialect="excel-tab"):
            females.append(line)

    femaleCutoff85Index = females[0].index("85th Percentile BMI Value")    
    femaleCutoff95Index = females[0].index("95th Percentile BMI Value")
    
    for row in females:
        try:
            femaleAges.append(float(row[0]))
        except ValueError:
            femaleAges.append(row[0])   
                 
        try:
            femaleCutoff85.append(float(row[femaleCutoff85Index]))
        except ValueError:
            femaleCutoff85.append(row[femaleCutoff85Index])

        try:
            femaleCutoff95.append(float(row[femaleCutoff95Index]))
        except ValueError:
            femaleCutoff95.append(row[femaleCutoff95Index])

def variables():
    return ["RIAGENDR", "RIDAGEMN", "BMXBMI"]

def name():
    return "OBESITY"
    
def title():    
    return "Overweight/Obesity status"
    
def type():    
    return "category"
    
def calculate(values):
    gender = values ["RIAGENDR"]
    age = values["RIDAGEMN"]
    bmi = values["BMXBMI"]    
    
    if '\N' in [age,bmi,gender]:
        obesity = '\N'
    else:
        age = float(age)
        gender = float(gender)
        bmi = float(bmi)
        
        if 240 <= age:
            if 30.0 <= bmi:
                obesity = 3
            elif 25.0 <= bmi:                
                obesity = 2
            else:
                obesity = 1
                
        elif age < 24:
            obesity = '\N'
        
        else:
            if gender == 1:
                ageindex = maleAges.index(age + 0.5)
                cutoff85 = maleCutoff85[ageindex]
                cutoff95 = maleCutoff95[ageindex]
                
                if cutoff95 <= bmi:
                    obesity = 3
                elif cutoff85 <= bmi:
                    obesity = 2                
                else:
                    obesity = 1
            else:
                ageindex = femaleAges.index(age + 0.5)
                cutoff85 = femaleCutoff85[ageindex]
                cutoff95 = femaleCutoff95[ageindex]
                
                if cutoff95 <= bmi:
                    obesity = 3
                elif cutoff85 <= bmi:
                    obesity = 2                
                else:
                    obesity = 1              

    return obesity
        
def range(): 
    return "1:Normal;2:Overweight;3:Obese"
    
def table(): 
    return "Health Indicators"