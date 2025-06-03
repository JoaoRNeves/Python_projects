# 💸 Expense Splitter with Proportional Custom Split

A Python Tkinter GUI application that helps users split a total expense among multiple people either evenly or by specifying custom proportional percentages. The app dynamically adjusts percentages to always total 100%, preventing errors in manual input.

---

## Features

- Input total expense amount  
- Input number of people sharing the expense  
- Choose between:  
  - Even split (equal shares)  
  - Custom split (specify percentages for each person)  
- Real-time adjustment of percentage inputs to ensure they sum to 100%  
- Validation of user input to prevent invalid entries  
- Displays the amount each person should pay based on the split type  

---

## Preview



---

## Installation

1. **Clone the repository**  
   ```bash
   git clone https://github.com/joaorneves/python_projects.git
   cd "python_projects/Udemy Class_2_Expense Splitter"
    ````

2. **Run the application**

   ```bash
   python Code.py
   ```

---

## Usage

1. Enter the total expense amount (must be a positive number).
2. Enter the number of people sharing the expense.
3. Choose the split type:

   * Even split: Each person pays an equal share.
   * Custom split: Enter custom percentages for each person. The app auto-adjusts to ensure total is 100%.
4. Click **Calculate**.
5. The amounts each person should pay will be displayed.

---

## Screenshots

<img width="200" alt="Screenshot 1" src="https://github.com/user-attachments/assets/c40959ae-389b-4950-bd27-27c906d2a535" />

<img width="200" alt="Screenshot 2" src="https://github.com/user-attachments/assets/48e206a7-d243-488c-b02a-6e242334e9b9" />

<img width="200" alt="Screenshot 3" src="https://github.com/user-attachments/assets/084e1e51-8ea3-42a2-9345-7ec877124946" />

---

## Known Issues / Limitations

* Number of people must be at least 1 for even split and at least 2 for custom split.
* Percentages are rounded to two decimal places, which may cause tiny rounding differences.

---

## Future Improvements

* Save and load split configurations
* Support for currency selection
* Export results to a file (CSV, PDF)
* More robust input error handling

---

## License

This project is open-source and free to use.

---

## Acknowledgements

Created as part of a small projects series to practice Python and GUI development.
Built with the support of AI tools to accelerate coding and learning (mainly the GUI).
Feedback and contributions are welcome!
