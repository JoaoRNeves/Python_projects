import tkinter as tk
from tkinter import messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.widgets import Cursor
import numpy as np

def display_results(monthly_income, expenses, tax_rate, monthly_net_income, yearly_salary, yearly_tax, yearly_net_income, currency):
    # Create a new window with larger size and white background
    result_window = tk.Toplevel()
    result_window.title("Finance Calculation Results")
    result_window.geometry("600x700")
    result_window.config(bg='white')

    # Title Label
    tk.Label(result_window, text="Financial Summary", font=("Helvetica Neue", 20, "bold"), bg="white", fg="#007AFF").pack(pady=10)

    # Display the results
    results_text = (
        f"Monthly Income: {currency}{monthly_income:,.2f}\n"
        f"Tax Rate: {tax_rate:.0f}%\n"
        f"Monthly Tax: {currency}{monthly_income * (tax_rate / 100):,.2f}\n"
        f"Monthly Expenses: {currency}{expenses:,.2f}\n"
        f"Monthly Net Income: {currency}{monthly_net_income:,.2f}\n"
        f"Yearly Salary: {currency}{yearly_salary:,.2f}\n"
        f"Yearly Tax Paid: {currency}{yearly_tax:,.2f}\n"
        f"Yearly Net Income: {currency}{yearly_net_income:,.2f}"
    )
    result_label = tk.Label(result_window, text=results_text, justify="left", font=("Helvetica Neue", 14), bg="white", padx=10, pady=10)
    result_label.pack()

    # Graph Estimation of Savings over 10 years
    def plot_graph():
        years = list(range(1, 11))
        savings = [monthly_net_income * 12 * year for year in years]

        fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
        ax.plot(years, savings, color='#007AFF', marker='o', linestyle='-', linewidth=2)
        ax.set_title('Estimated Savings Over 10 Years', fontsize=14, color="#007AFF")
        ax.set_xlabel('Years', fontsize=12)
        ax.set_ylabel(f'Savings ({currency})', fontsize=12)
        ax.grid(True)

        # Add interactive tooltip
        def on_move(event):
            if event.inaxes == ax:
                xdata, ydata = event.xdata, event.ydata
                if xdata is not None:
                    index = int(round(xdata)) - 1
                    if 0 <= index < len(years):
                        tooltip.set_text(f"Year {years[index]}: {currency}{savings[index]:,.2f}")
                        tooltip.set_position((xdata, ydata))
                        fig.canvas.draw_idle()

        tooltip = ax.annotate("", xy=(0, 0), xytext=(10, 10), textcoords="offset points",
                              bbox=dict(boxstyle="round", fc="w"),
                              arrowprops=dict(arrowstyle="->"))
        tooltip.set_visible(False)
        fig.canvas.mpl_connect('motion_notify_event', on_move)

        canvas = FigureCanvasTkAgg(fig, master=result_window)
        canvas.draw()
        canvas.get_tk_widget().pack(pady=20)

    # Call the function to plot the graph
    plot_graph()

    # Add a close button with rounded corners
    def round_rectangle(x1, y1, x2, y2, radius=25, **kwargs):
        """ Draw a rounded rectangle on canvas """
        points = [x1 + radius, y1,
                  x2 - radius, y1,
                  x2, y1,
                  x2, y1 + radius,
                  x2, y2 - radius,
                  x2 - radius, y2,
                  x1 + radius, y2,
                  x1, y2,
                  x1, y2 - radius,
                  x1, y1 + radius,
                  x1 + radius, y1]
        return canvas.create_polygon(points, **kwargs, smooth=True)

    canvas = tk.Canvas(result_window, width=600, height=700, bg='white', highlightthickness=0)
    canvas.pack()

    round_rectangle(250, 640, 350, 670, radius=15, fill='#007AFF', outline='#007AFF')
    tk.Button(result_window, text="Close", command=result_window.destroy, padx=10, pady=5,
              font=("Helvetica Neue", 12), bg="#007AFF", fg="white", relief="flat",
              highlightthickness=0).place(x=250, y=640)

def calculate_finances():
    try:
        monthly_income = float(monthly_income_entry.get())
        expenses = float(expenses_entry.get())
        tax_rate = float(tax_rate_entry.get())
        selected_currency = currency_var.get()

        monthly_tax = monthly_income * (tax_rate / 100)
        monthly_net_income = monthly_income - monthly_tax - expenses
        yearly_salary = (monthly_income - expenses) * 12
        yearly_tax = monthly_tax * 12
        yearly_net_income = yearly_salary - yearly_tax

        display_results(monthly_income, expenses, tax_rate, monthly_net_income, yearly_salary, yearly_tax, yearly_net_income, selected_currency)

    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter valid numeric values.")

root = tk.Tk()
root.title("Finance Calculator")
root.geometry("400x300")
root.config(bg="white")

font_style = ("Helvetica Neue", 14)
accent_color = "#007AFF"

# Currency selection
currencies = ["KR", "USD", "EUR", "GBP"]
currency_var = tk.StringVar(root)
currency_var.set(currencies[0])

tk.Label(root, text="Enter Monthly Salary:", font=font_style, bg="white").grid(row=0, column=0, padx=10, pady=10)
monthly_income_entry = tk.Entry(root, font=font_style)
monthly_income_entry.grid(row=0, column=1)

tk.Label(root, text="Enter Monthly Expenses:", font=font_style, bg="white").grid(row=1, column=0, padx=10, pady=10)
expenses_entry = tk.Entry(root, font=font_style)
expenses_entry.grid(row=1, column=1)

tk.Label(root, text="Enter Tax Rate (%):", font=font_style, bg="white").grid(row=2, column=0, padx=10, pady=10)
tax_rate_entry = tk.Entry(root, font=font_style)
tax_rate_entry.grid(row=2, column=1)

tk.Label(root, text="Select Currency:", font=font_style, bg="white").grid(row=3, column=0, padx=10, pady=10)
currency_menu = tk.OptionMenu(root, currency_var, *currencies)
currency_menu.config(font=font_style, bg="white", highlightthickness=0)
currency_menu.grid(row=3, column=1)

# Rounded button
def round_rectangle(x1, y1, x2, y2, radius=25, **kwargs):
    points = [x1 + radius, y1,
              x2 - radius, y1,
              x2, y1,
              x2, y1 + radius,
              x2, y2 - radius,
              x2 - radius, y2,
              x1 + radius, y2,
              x1, y2,
              x1, y2 - radius,
              x1, y1 + radius,
              x1 + radius, y1]
    return canvas.create_polygon(points, **kwargs, smooth=True)

canvas = tk.Canvas(root, width=400, height=300, bg="white", highlightthickness=0)
canvas.grid(row=4, column=0, columnspan=2, pady=20)

round_rectangle(150, 230, 250, 260, radius=15, fill=accent_color, outline=accent_color)
tk.Button(root, text="Calculate", command=calculate_finances, font=font_style, padx=10, pady=5,
          bg=accent_color, fg="white", relief="flat", highlightthickness=0).place(x=150, y=230)

root.mainloop()

