''' Performs optional initialization

It can be absent from the code
'''
def init():
    pass        

''' Returns the list of variables needed to compute the composite

The names must correspond to the original titles in the data file
'''
def variables():
    return ["X", "Y"]

''' Returns the name of the new composite variable

The names must correspond to the original titles in the data file
'''    
def name():
    return "Z"

''' Returns the title of the new composite variable

The title is often a human-readable string describing the variable
'''
def title():
    return "Sum of X and Y"

''' Returns a string with the data type for the variable

The valid types are int, long, float, double, and category
'''
def type():
    return "float"

''' Returns composite value given the values of the component variables

The returned value will be automatically converted into a string, so it might be a good 
idea to do the conversion directly inside this method to make sure it is correct.
'''
def calculate(values): 
    x = float(values["X"])
    y = float(values ["Y"])
    return x + y
    
''' Returns a string with the range of the composite

This range should be of the form "min,max" for numerical variables, and an enumeration of
all possible categories with their code:value pairs for category variables, as in:
"0:male;1:female"
'''    
def range(): 
    return "0,100"

''' Returns the table this composite should be put in, within the Composites group

If this method is not modified, the composite will be put inside the default table 
"All Composites"
'''
def table(): 
    return "All Composites"