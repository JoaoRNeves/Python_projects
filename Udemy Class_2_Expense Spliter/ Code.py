import tkinter as tk
from tkinter import ttk, messagebox

class ExpenseSplitterApp(tk.Tk):
    """
    A GUI application for splitting expenses evenly or by custom proportions among multiple people.
    """
    def __init__(self):
        super().__init__()
        self.title("Expense Splitter with Proportional Custom Split")
        self.geometry("500x600")
        self.resizable(False, False)

        # Variables to hold user inputs
        self.total_amount_var = tk.StringVar()
        self.num_people_var = tk.StringVar()
        self.split_type_var = tk.StringVar(value="even")  # Default split type

        self.custom_percentage_vars = []  # List to hold StringVars for custom percentages
        self.updating = False  # Flag to prevent recursive trace callbacks

        self.create_widgets()

    def create_widgets(self):
        """
        Creates all the widgets in the main window:
        - Inputs for total amount and number of people
        - Radio buttons for split type selection
        - Dynamic inputs for custom split percentages
        - Calculate button and result display area
        """
        # Total amount input
        ttk.Label(self, text="Total amount:").pack(pady=(20, 5))
        ttk.Entry(self, textvariable=self.total_amount_var).pack()

        # Number of people input
        ttk.Label(self, text="Number of people:").pack(pady=(15, 5))
        ttk.Entry(self, textvariable=self.num_people_var).pack()

        # Split type selection radio buttons
        ttk.Label(self, text="Split type:").pack(pady=(15, 5))

        split_frame = ttk.Frame(self)
        split_frame.pack()

        ttk.Radiobutton(
            split_frame, text="Even split", variable=self.split_type_var, value="even",
            command=self.update_custom_inputs
        ).grid(row=0, column=0, padx=10)

        ttk.Radiobutton(
            split_frame, text="Custom split", variable=self.split_type_var, value="custom",
            command=self.update_custom_inputs
        ).grid(row=0, column=1, padx=10)

        # Frame to hold dynamic custom percentage inputs
        self.custom_inputs_frame = ttk.Frame(self)
        self.custom_inputs_frame.pack(pady=(10, 10))

        # Calculate button
        ttk.Button(self, text="Calculate", command=self.calculate).pack(pady=10)

        # Text widget to display results (read-only)
        self.result_text = tk.Text(self, height=12, state="disabled")
        self.result_text.pack(padx=10, pady=10, fill="x")

    def update_custom_inputs(self):
        """
        Called when split type or number of people changes.
        Clears and rebuilds the custom percentage input fields if 'custom' split is selected.
        Sets up trace callbacks to keep percentages consistent.
        """
        # Clear any existing widgets and variables in the custom input frame
        for widget in self.custom_inputs_frame.winfo_children():
            widget.destroy()
        self.custom_percentage_vars.clear()

        if self.split_type_var.get() == "custom":
            # Validate number of people for custom split
            try:
                num = int(self.num_people_var.get())
                if num < 2:
                    messagebox.showerror("Input Error", "Number of people must be at least 2 for custom split.")
                    return
            except ValueError:
                return  # If number of people input is invalid, silently return

            ttk.Label(self.custom_inputs_frame, text="Enter percentage for each person:").pack()

            # Create StringVars and Entry widgets for each person's percentage
            for i in range(num):
                var = tk.StringVar()
                self.custom_percentage_vars.append(var)

                frame = ttk.Frame(self.custom_inputs_frame)
                frame.pack(fill="x", pady=2)

                ttk.Label(frame, text=f"Person {i+1} (%):", width=15).pack(side="left")
                entry = ttk.Entry(frame, textvariable=var, width=10)
                entry.pack(side="left")

                # Add trace callbacks for live synchronization of percentages
                if i < num - 1:
                    # For all but last person, update the last person's percentage when changed
                    var.trace_add('write', self.make_handler(i))
                else:
                    # For last person, adjust others proportionally on change
                    var.trace_add('write', self.last_person_handler)

            # Initialize all percentages equally
            equal_percent = 100 / num
            for var in self.custom_percentage_vars:
                var.set(f"{equal_percent:.2f}")

            # Update last person's percentage to correct any rounding issues
            self.update_last_percentage()

    def make_handler(self, index):
        """
        Factory function that returns a handler to update the last person's
        percentage when any other person's percentage changes.
        """
        def handler(*args):
            if self.updating:
                return  # Prevent recursive updates
            self.updating = True
            try:
                total = 0.0
                # Sum percentages of all but the last person
                for i, var in enumerate(self.custom_percentage_vars[:-1]):
                    try:
                        val = float(var.get())
                        if val < 0:
                            raise ValueError
                        total += val
                    except ValueError:
                        # Ignore invalid inputs while typing
                        self.updating = False
                        return

                # Calculate remaining percentage for last person
                last_val = 100 - total
                if last_val < 0:
                    last_val = 0  # Clamp to zero if total exceeds 100

                self.custom_percentage_vars[-1].set(f"{last_val:.2f}")
            finally:
                self.updating = False
        return handler

    def last_person_handler(self, *args):
        """
        Handler to adjust other persons' percentages proportionally when
        the last person's percentage is changed.
        """
        if self.updating:
            return
        self.updating = True
        try:
            # Validate last person's percentage
            try:
                last_val = float(self.custom_percentage_vars[-1].get())
                if last_val < 0 or last_val > 100:
                    self.updating = False
                    return
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

            diff = 100 - current_total

            if abs(diff) < 0.01:
                # Percentages already sum to ~100%
                self.updating = False
                return

            if total_others == 0:
                # Distribute difference evenly if others are zero
                per_person_adjust = diff / len(others)
                new_vals = [max(0, val + per_person_adjust) for val in others_vals]
            else:
                # Adjust others proportionally
                new_vals = []
                for val in others_vals:
                    proportion = val / total_others if total_others != 0 else 0
                    new_val = val + diff * proportion
                    new_val = max(0, new_val)
                    new_vals.append(new_val)

            # Normalize to make sure sum + last_val = 100
            new_sum = sum(new_vals)
            scale = (100 - last_val) / new_sum if new_sum != 0 else 0
            new_vals = [v * scale for v in new_vals]

            # Update other percentages without triggering trace callbacks
            for var, new_val in zip(others, new_vals):
                var.set(f"{new_val:.2f}")
        finally:
            self.updating = False

    def update_last_percentage(self):
        """
        Helper method to update the last person's percentage based on others.
        Called during initialization to ensure total 100%.
        """
        try:
            total = 0.0
            for var in self.custom_percentage_vars[:-1]:
                total += float(var.get())
            last_val = 100 - total
            if last_val < 0:
                last_val = 0
            self.custom_percentage_vars[-1].set(f"{last_val:.2f}")
        except Exception:
            # Ignore errors during initial setup
            pass

    def calculate(self):
        """
        Calculates and displays the expense split based on user input.
        Validates inputs and shows errors if invalid.
        Supports both even and custom splits.
        """
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
            self.result_text.insert(tk.END, f"Number of people:

