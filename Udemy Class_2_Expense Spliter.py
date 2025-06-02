import tkinter as tk
from tkinter import ttk, messagebox

class ExpenseSplitterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Expense Splitter with Proportional Custom Split")
        self.geometry("500x600")
        self.resizable(False, False)

        self.total_amount_var = tk.StringVar()
        self.num_people_var = tk.StringVar()
        self.split_type_var = tk.StringVar(value="even")

        self.custom_percentage_vars = []
        self.updating = False  # Flag to prevent recursive updates

        self.create_widgets()

    def create_widgets(self):
        ttk.Label(self, text="Total amount:").pack(pady=(20, 5))
        ttk.Entry(self, textvariable=self.total_amount_var).pack()

        ttk.Label(self, text="Number of people:").pack(pady=(15, 5))
        ttk.Entry(self, textvariable=self.num_people_var).pack()

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

        self.custom_inputs_frame = ttk.Frame(self)
        self.custom_inputs_frame.pack(pady=(10, 10))

        ttk.Button(self, text="Calculate", command=self.calculate).pack(pady=10)

        self.result_text = tk.Text(self, height=12, state="disabled")
        self.result_text.pack(padx=10, pady=10, fill="x")

    def update_custom_inputs(self):
        # Clear previous inputs and traces
        for widget in self.custom_inputs_frame.winfo_children():
            widget.destroy()
        self.custom_percentage_vars.clear()

        if self.split_type_var.get() == "custom":
            try:
                num = int(self.num_people_var.get())
                if num < 2:
                    messagebox.showerror("Input Error", "Number of people must be at least 2 for custom split.")
                    return
            except ValueError:
                return

            ttk.Label(self.custom_inputs_frame, text="Enter percentage for each person:").pack()

            # Create StringVars and entries for each person
            for i in range(num):
                var = tk.StringVar()
                self.custom_percentage_vars.append(var)

                frame = ttk.Frame(self.custom_inputs_frame)
                frame.pack(fill="x", pady=2)

                ttk.Label(frame, text=f"Person {i+1} (%):", width=15).pack(side="left")
                entry = ttk.Entry(frame, textvariable=var, width=10)
                entry.pack(side="left")

                # Attach trace for live updates
                if i < num - 1:
                    # For all but last person, update last percentage on change
                    var.trace_add('write', self.make_handler(i))
                else:
                    # For last person, adjust others proportionally on change
                    var.trace_add('write', self.last_person_handler)

            # Initialize with equal percentages
            equal_percent = 100 / num
            for i, var in enumerate(self.custom_percentage_vars):
                var.set(f"{equal_percent:.2f}")

            # Force last to auto-correct based on others
            self.update_last_percentage()

    def make_handler(self, index):
        # Return a handler function to update last person when var at index changes
        def handler(*args):
            if self.updating:
                return
            self.updating = True
            try:
                # Validate current inputs for others except last
                total = 0.0
                for i, var in enumerate(self.custom_percentage_vars[:-1]):
                    try:
                        val = float(var.get())
                        if val < 0:
                            raise ValueError
                        total += val
                    except ValueError:
                        # Ignore invalid input during typing
                        self.updating = False
                        return

                # Calculate last percentage
                last_val = 100 - total
                if last_val < 0:
                    # If sum > 100, clamp last to 0
                    last_val = 0

                self.custom_percentage_vars[-1].set(f"{last_val:.2f}")
            finally:
                self.updating = False
        return handler

    def last_person_handler(self, *args):
        if self.updating:
            return
        self.updating = True
        try:
            try:
                last_val = float(self.custom_percentage_vars[-1].get())
                if last_val < 0 or last_val > 100:
                    self.updating = False
                    return  # Invalid last percentage input
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

            # Calculate difference to adjust others by
            diff = 100 - current_total

            if abs(diff) < 0.01:
                # Already totals ~100%, no need to adjust
                self.updating = False
                return

            if total_others == 0:
                # If others are zero, distribute diff evenly
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

            # Normalize new_vals so sum + last_val = 100
            new_sum = sum(new_vals)
            scale = (100 - last_val) / new_sum if new_sum != 0 else 0
            new_vals = [v * scale for v in new_vals]

            # Update other vars without triggering traces
            for var, new_val in zip(others, new_vals):
                var.set(f"{new_val:.2f}")
        finally:
            self.updating = False

    def update_last_percentage(self):
        # Helper to set last percentage based on others (used on init)
        try:
            total = 0.0
            for var in self.custom_percentage_vars[:-1]:
                total += float(var.get())
            last_val = 100 - total
            if last_val < 0:
                last_val = 0
            self.custom_percentage_vars[-1].set(f"{last_val:.2f}")
        except Exception:
            pass

    def calculate(self):
        self.result_text.config(state="normal")
        self.result_text.delete("1.0", tk.END)

        try:
            total = float(self.total_amount_var.get())
            if total <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Input Error", "Total amount must be a positive number.")
            return

        try:
            num_people = int(self.num_people_var.get())
            if num_people < 1:
                raise ValueError
        except ValueError:
            messagebox.showerror("Input Error", "Number of people must be at least 1.")
            return

        if self.split_type_var.get() == "even":
            share = total / num_people
            self.result_text.insert(tk.END, f"Total expense: €{total:,.2f}\n")
            self.result_text.insert(tk.END, f"Number of people: {num_people}\n")
            self.result_text.insert(tk.END, f"Each person pays: €{share:.2f}\n")

        else:
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
                messagebox.showerror("Input Error", f"Percentages add up to {total_percent:.2f}%. They must total 100%.")
                return

            self.result_text.insert(tk.END, f"Total expense: €{total:,.2f}\n")
            self.result_text.insert(tk.END, f"Number of people: {num_people}\n")
            for i, p in enumerate(percentages):
                amount = total * (p / 100)
                self.result_text.insert(tk.END, f"Person {i+1} pays ({p:.2f}%): €{amount:.2f}\n")

        self.result_text.config(state="disabled")

if __name__ == "__main__":
    app = ExpenseSplitterApp()
    app.mainloop()
