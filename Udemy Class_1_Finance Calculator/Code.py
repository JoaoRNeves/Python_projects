# ===============================
# Finance Calculator (Tkinter + Matplotlib)
# ===============================

# ---- Imports ----
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

# ---- Global Configuration ----
FONT = ("Helvetica Neue", 14)
ACCENT_COLOR = "#007AFF"
CURRENCIES = ["KR", "USD", "EUR", "GBP"]

# ===============================
# Financial Calculation Functions
# ===============================
def calculate_finances():
    try:
        monthly_income = float(monthly_income_entry.get())
        expenses = float(expenses_entry.get())
        tax_rate = float(tax_rate_entry.get())
        currency = currency_var.get()

        # --- Corrected Financial Logic ---
        monthly_tax = monthly_income * (tax_rate / 100)
        monthly_net_income = monthly_income - monthly_tax - expenses

        yearly_salary = monthly_income * 12
        yearly_expenses = expenses * 12
        yearly_tax = monthly_tax * 12
        yearly_net_income = yearly_salary - yearly_expenses - yearly_tax

        display_results(
            monthly_income, expenses, tax_rate,
            monthly_net_income, yearly_salary,
            yearly_tax, yearly_net_income, currency
        )

    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter valid numeric values.")

# ===============================
# Result Display Window
# ===============================
def display_results(monthly_income, expenses, tax_rate, monthly_net_income, yearly_salary, yearly_tax, yearly_net_income, currency):
    result_window = tk.Toplevel()
    result_window.title("Finance Calculation Results")
    result_window.geometry("650x750")
    result_window.config(bg='white')

    # --- Header ---
    tk.Label(result_window, text="Financial Summary", font=("Helvetica Neue", 20, "bold"),
             bg="white", fg=ACCENT_COLOR).pack(pady=15)

    # --- Financial Summary Text ---
    results = (
        f"Monthly Income: {currency}{monthly_income:,.2f}\n"
        f"Tax Rate: {tax_rate:.0f}%\n"
        f"Monthly Tax: {currency}{monthly_income * (tax_rate / 100):,.2f}\n"
        f"Monthly Expenses: {currency}{expenses:,.2f}\n"
        f"Monthly Net Income: {currency}{monthly_net_income:,.2f}\n"
        f"Yearly Salary: {currency}{yearly_salary:,.2f}\n"
        f"Yearly Tax Paid: {currency}{yearly_tax:,.2f}\n"
        f"Yearly Net Income: {currency}{yearly_net_income:,.2f}"
    )

    tk.Label(result_window, text=results, justify="left", font=FONT,
             bg="white", fg="black", padx=10, pady=10).pack()

    # ===============================
    # Matplotlib Savings Plot
    # ===============================
    def plot_graph():
        years = list(range(1, 11))
        savings = [monthly_net_income * 12 * year for year in years]

        fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
        ax.plot(years, savings, color=ACCENT_COLOR, marker='o', linewidth=2)
        ax.set_title("Estimated Savings Over 10 Years", fontsize=14, color=ACCENT_COLOR)
        ax.set_xlabel("Years")
        ax.set_ylabel(f"Savings ({currency})")
        ax.grid(True)

        # --- Tooltip on Hover ---
        tooltip = ax.annotate("", xy=(0, 0), xytext=(10, 10), textcoords="offset points",
                              bbox=dict(boxstyle="round", fc="white"),
                              arrowprops=dict(arrowstyle="->"))
        tooltip.set_visible(False)

        def on_move(event):
            if event.inaxes == ax:
                x = event.xdata
                if x:
                    index = int(round(x)) - 1
                    if 0 <= index < len(years):
                        tooltip.xy = (years[index], savings[index])
                        tooltip.set_text(f"Year {years[index]}: {currency}{savings[index]:,.2f}")
                        tooltip.set_visible(True)
                        fig.canvas.draw_idle()
                    else:
                        tooltip.set_visible(False)
                        fig.canvas.draw_idle()

        fig.canvas.mpl_connect('motion_notify_event', on_move)

        canvas = FigureCanvasTkAgg(fig, master=result_window)
        canvas.draw()
        canvas.get_tk_widget().pack(pady=20)

    plot_graph()

    # --- Close Button ---
    tk.Button(result_window, text="Close", command=result_window.destroy,
              font=FONT, bg=ACCENT_COLOR, fg="white",
              relief="flat", padx=10, pady=5).pack(pady=10)

# ===============================
# Main GUI Layout
# ===============================
root = tk.Tk()
root.title("Finance Calculator")
root.config(bg="white")  # set main window background

# --- Input Fields ---
tk.Label(root, text="Enter Monthly Salary:", font=FONT, bg="white", fg="black").grid(row=0, column=0, padx=10, pady=10, sticky="w")
monthly_income_entry = tk.Entry(root, font=FONT, bg="white", fg="black", insertbackground="black")
monthly_income_entry.grid(row=0, column=1)

tk.Label(root, text="Enter Monthly Expenses:", font=FONT, bg="white", fg="black").grid(row=1, column=0, padx=10, pady=10, sticky="w")
expenses_entry = tk.Entry(root, font=FONT, bg="white", fg="black", insertbackground="black")
expenses_entry.grid(row=1, column=1)

tk.Label(root, text="Enter Tax Rate (%):", font=FONT, bg="white", fg="black").grid(row=2, column=0, padx=10, pady=10, sticky="w")
tax_rate_entry = tk.Entry(root, font=FONT, bg="white", fg="black", insertbackground="black")
tax_rate_entry.grid(row=2, column=1)

# --- Currency Selection ---
tk.Label(root, text="Select Currency:", font=FONT, bg="white", fg="black").grid(row=3, column=0, padx=10, pady=10, sticky="w")
currency_var = tk.StringVar(value=CURRENCIES[0])

# Using ttk.OptionMenu - set style to fix dark theme issues
style = ttk.Style(root)
style.theme_use('clam')
style.configure('TMenubutton', background='white', foreground='black')

currency_menu = ttk.OptionMenu(root, currency_var, CURRENCIES[0], *CURRENCIES)
currency_menu.grid(row=3, column=1)

# --- Calculate Button ---
tk.Button(root, text="Calculate", command=calculate_finances,
          font=FONT, bg=ACCENT_COLOR, fg="white",
          relief="flat", padx=10, pady=5).grid(row=4, column=0, columnspan=2, pady=20)

root.mainloop()
