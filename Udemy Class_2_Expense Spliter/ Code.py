import tkinter as tk
from tkinter import ttk, messagebox

class ExpenseSplitterApp(tk.Tk):
    # Main application class inheriting from Tkinter's Tk
    
    def __init__(self):
        super().__init__()
        self.title("Expense Splitter with Proportional Custom Split")
        self.geometry("500x600")  # Set fixed window size
        self.resizable(False, False)  # Disable resizing

        # Variables to store user inputs and app state
        self.total_amount_var = tk.StringVar()
        self.num_people_var = tk.StringVar()
        self.split_type_var = tk.StringVar(value="even")  # Default to even split

        self.custom_percentage_vars = []  # List of StringVars for custom split percentages
        self.updating = False  # Flag to avoid recursive updates when tracing variable changes

        self.create_widgets()  # Build the GUI elements

    def create_widgets(self):
        # Create all widgets: labels, entries, radio buttons, buttons, and result display

        # Label and entry for total amount input
        ttk.Label(self, text="Total amount:").pack(pady=(20, 5))
        ttk.Entry(self, textvariable=self.total_amount_var).pack()

        # Label and entry for number of people input
        ttk.Label(self, text="Number of people:").pack(pady=(15, 5))
        ttk.Entry(self, textvariable=self.num_people_var).pack()

        # Label for split type radio buttons
        ttk.Label(self, text="Split type:").pack(pady=(15, 5))

        # Frame to hold split type radio buttons
        split_frame = ttk.Frame(self)
        split_frame.pack()

        # Radio button for even split option
        ttk.Radiobutton(
            split_frame, text="Even split", variable=self.split_type_var, value="even",
            command=self.update_custom_inputs  # Update UI when changed
        ).grid(row=0, column=0, padx=10)

        # Radio button for custom split option
        ttk.Radiobutton(
            split_frame, text="Custom split", variable=self.split_type_var, value="custom",
            command=self.update_custom_inputs
        ).grid(row=0, column=1, padx=10)

        # Frame where custom split percentage entries will be created dynamically
        self.custom_inputs_frame = ttk.Frame(self)
        self.custom_inputs_frame.pack(pady=(10, 10))

        # Button to trigger calculation of shares
        ttk.Button(self, text="Calculate", command=self.calculate).pack(pady=10)

        # Text widget to display calculation results (disabled for editing)
        self.result_text = tk.Text(self, height=12, state="disabled")
        self.result_text.pack(padx=10, pady=10, fill="x")

    def update_custom_inputs(self):
        # Called when split type or number of people changes

        # Clear previous custom percentage inputs and variables
        for widget in self.custom_inputs_frame.winfo_children():
            widget.destroy()
        self.custom_percentage_vars.clear()

        if self.split_type_var.get() == "custom":
            # If custom split is selected, validate number of people
            try:
                num = int(self.num_people_var.get())
                if num < 2:
                    # Custom split requires at least 2 people
                    messagebox.showerror("Input Error", "Number of people must be at least 2 for custom split.")
                    return
            except ValueError:
                # If number input invalid, skip creating inputs
                return

            # Label to instruct user to enter percentages
            ttk.Label(self.custom_inputs_frame, text="Enter percentage for each person:").pack()

            # Create entry fields for each person's percentage
            for i in range(num):
                var = tk.StringVar()
                self.custom_percentage_vars.append(var)

                frame = ttk.Frame(self.custom_inputs_frame)
                frame.pack(fill="x", pady=2)

                # Label showing which person the percentage is for
                ttk.Label(frame, text=f"Person {i+1} (%):", width=15).pack(side="left")

                # Entry widget for input
                entry = ttk.Entry(frame, textvariable=var, width=10)
                entry.pack(side="left")

                # Add trace callback to update last person's percentage automatically
                if i < num - 1:
                    var.trace_add('write', self.make_handler(i))  # For all but last person
                else:
                    var.trace_add('write', self.last_person_handler)  # For last person

            # Initialize all percentages evenly distributed
            equal_percent = 100 / num
            for var in self.custom_percentage_vars:
                var.set(f"{equal_percent:.2f}")

            # Ensure last person's percentage is updated correctly after initialization
            self.update_last_percentage()

    def make_handler(self, index):
        # Factory function to generate a trace handler for each person except last
        def handler(*args):
            if self.updating:
                return  # Prevent recursive updates
            self.updating = True
            try:
                total = 0.0
                # Sum all but last person's percentages
                for i, var in enumerate(self.custom_percentage_vars[:-1]):
                    try:
                        val = float(var.get())
                        if val < 0:
                            raise ValueError
                        total += val
                    except ValueError:
                        # Ignore invalid inputs during typing
                        self.updating = False
                        return

                # Calculate remaining percentage for last person
                last_val = 100 - total
                if last_val < 0:
                    last_val = 0  # Clamp to zero if total exceeds 100

                # Update last person's percentage
                self.custom_percentage_vars[-1].set(f"{last_val:.2f}")
            finally:
                self.updating = False
        return handler

    def last_person_handler(self, *args):
        # Handler to proportionally adjust other percentages when last person's changes
        if self.updating:
            return
        self.updating = True
        try:
            try:
                last_val = float(self.custom_percentage_vars[-1].get())
                if last_val < 0 or last_val > 100:
                    self.updating = False
                    return  # Invalid percentage input
            except ValueError:
                self.updating = False
                return

            others = self.custom_percentage_vars[:-1]
            others_vals = []
            for var in others:
                try:
                    val = float(var.get())
                    if val < 0:
                        raise ValueError
                    others_vals.append(val)
                except ValueError:
                    self.updating = False
                    return

            total_others = sum(others_vals)
            current_total = total_others + last_val

            diff = 100 - current_total  # Difference to fix sum to 100%

            if abs(diff) < 0.01:
                # Already close to 100%, no change needed
                self.updating = False
                return

            if total_others == 0:
                # If all others are zero, distribute difference evenly
                per_person_adjust = diff / len(others)
                new_vals = [max(0, val + per_person_adjust) for val in others_vals]
            else:
                # Otherwise adjust others proportionally based on their current values
                new_vals = []
                for val in others_vals:
                    proportion = val / total_others if total_others != 0 else 0
                    new_val = val + diff * proportion
                    new_val = max(0, new_val)  # Prevent negative values
                    new_vals.append(new_val)

            # Normalize new values so total with last person equals 100
            new_sum = sum(new_vals)
            scale = (100 - last_val) / new_sum if new_sum != 0 else 0
            new_vals = [v * scale for v in new_vals]

            # Update others without triggering traces
            for var, new_val in zip(others, new_vals):
                var.set(f"{new_val:.2f}")
        finally:
            self.updating = False

    def update_last_percentage(self):
        # Helper to update last person's percentage so total is exactly 100%
        try:
            total = 0.0
            for var in self.custom_percentage_vars[:-1]:
                total += float(var.get())
            last_val = 100 - total
            if last_val < 0:
                last_val = 0
            self.custom_percentage_vars[-1].set(f"{last_val:.2f}")
        except Exception:
            # Ignore any errors during initial setup
            pass

    def calculate(self):
        # Calculate and display the split amounts based on inputs

        # Enable and clear the result text widget
        self.result_text.config(state="normal")
        self.result_text.delete("1.0", tk.END)

        # Validate total amount input
        try:
            total = float(self.total_amount_var.get())
            if total <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Input Error", "Total amount must be a positive number.")
            return

        # Validate number of people input
        try:
            num_people = int(self.num_people_var.get())
            if num_people < 1:
                raise ValueError
        except ValueError:
            messagebox.showerror("Input Error", "Number of people must be at least 1.")
            return

        if self.split_type_var.get() == "even":
            # Even split calculation
            share = total / num_people
            self.result_text.insert(tk.END, f"Total expense: €{total:,.2f}\n")
            self.result_text.insert(tk.END, f"Number of people: {num_people}\n")
            self.result_text.insert(tk.END, f"Each person pays: €{share:.2f}\n")

        else:
            # Custom split calculation
            percentages = []
            for i, var in enumerate(self.custom_percentage_vars):
                try:
                    p = float(var.get())
                    if not (0 <= p <= 100):
                        raise ValueError
                    percentages.append(p)
                except ValueError:
                    messagebox.showerror("Input Error", f"Percentage for Person {i+1} must be between 0 and 100.")
                    return

            total_percent = sum(percentages)
            if abs(total_percent - 100) > 0.01:
                # Percentages must sum to 100%
                messagebox.showerror("Input Error", f"Percentages add up to {total_percent:.2f}%. They must total 100%.")
                return

            self.result_text.insert(tk.END, f"Total expense: €{total:,.2f}\n")
            self.result_text.insert(tk.END, f"Number of people: {num_people}\n")
            # Show each person's amount based on percentage
            for i, p in enumerate(percentages):
                amount = total * (p / 100)
                self.result_text.insert(tk.END, f"Person {i+1} pays ({p:.2f}%): €{amount:.2f}\n")

        # Disable editing of the result text again
        self.result_text.config(state="disabled")

if __name__ == "__main__":
    # Run the application
    app = ExpenseSplitterApp()
    app.mainloop()
