Expense Splitter with Proportional Custom Split

**Overview**

This is a Python Tkinter GUI application that helps users split a total expense among multiple people either evenly or by specifying custom proportional percentages. The app dynamically adjusts percentages to always total 100%, preventing errors in manual input.

**Features**

Input total expense amount.
Input number of people sharing the expense.
Choose between:
Even split (equal shares).
Custom split (specify percentages for each person).
Real-time adjustment of percentage inputs to ensure they sum to 100%.
Validation of user input to prevent invalid entries.
Displays the amount each person should pay based on the split type.

              
**Installation**

Make sure you have Python 3.x installed.
Clone this repository or download the Code.py file.
Run the application using:
python Code.py

              
**Usage**

Enter the total expense amount (must be a positive number).
Enter the number of people sharing the expense.
Choose the split type:
Even split: Each person pays an equal share.
Custom split: Enter custom percentages for each person. The app auto-adjusts to ensure total is 100%.
Click Calculate.
The amounts each person should pay will be displayed.
              
**Screenshots**
![Expense Splitter App](https://joaorneves.com/python_projects/Udemy%20Class_2_Expense%20Splitter/images/screenshot1.png)

![Expense Splitter App](images/screenshot2.png)
![Expense Splitter App](images/screenshot3.png)

**Known Issues / Limitations**

Number of people must be at least 1 for even split and at least 2 for custom split.
Percentages are rounded to two decimal places, which may cause tiny rounding differences.

 
**Future Improvements**

Save and load split configurations.
Support for currency selection.
Export results to a file (CSV, PDF).
More robust input error handling.

 
License

This project is open-source and free to use 
