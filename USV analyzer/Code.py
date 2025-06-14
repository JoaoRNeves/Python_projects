import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.formula.api import ols
import statsmodels.api as sm
from statsmodels.stats.multicomp import pairwise_tukeyhsd
import matplotlib.pyplot as plt
import seaborn as sns
from itertools import combinations
import pingouin as pg
import traceback
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import webbrowser  # For opening plot folder
import sys


# --- Helper class to redirect print statements to the Tkinter Text widget ---
class TextRedirector(object):
    def __init__(self, widget):
        self.widget = widget

    def write(self, str_val):
        self.widget.insert(tk.END, str_val)
        self.widget.see(tk.END)

    def flush(self):  # Required for file-like objects
        pass


# --- Main Application Class ---
class USVAnalyzerApp:
    def __init__(self, master):
        self.master = master
        master.title("USV Analyzer")
        master.geometry("1200x800")  # Adjusted initial window size for results display

        # Configure grid for responsiveness
        master.grid_rowconfigure(0, weight=1)
        master.grid_columnconfigure(0, weight=1)

        # --- Configuration (as class attributes) ---
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.plot_output_dir = os.path.join(self.script_dir, 'plots')
        self.analysis_results_dir = os.path.join(self.script_dir, 'analysis_results')

        # Change here if you have other variables to be test or add more subgroups
        self.SEX_LABELS = {'F': 'Females', 'M': 'Males'}
        self.GENOTYPE_LABELS = {'WT': 'Wild Type', 'MUT': 'Mutant'}
        self.TIMEPOINT_ORDER = ['P4', 'P6']

        # Ensure output directories exist
        os.makedirs(self.plot_output_dir, exist_ok=True)
        os.makedirs(self.analysis_results_dir, exist_ok=True)

        # --- Data Storage ---
        self.df_aggregated = None
        self.selected_folder_path = None
        self.available_metrics = []
        self.available_grouping_variables = []
        self.last_generated_plot_path = None  # To store path of the last plot

        # --- Notebook (Tabbed Interface) ---
        self.notebook = ttk.Notebook(master)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # --- Tabs ---
        self.create_data_input_tab()
        self.create_report_tab()
        self.create_analysis_tab()
        self.create_statistical_output_tab()  # New tab for tables
        self.create_graphic_tab()  # New tab for plot

        # --- Status Bar ---
        self.status_bar = ttk.Label(master, text="Ready", relief=tk.SUNKEN, anchor="w")
        self.status_bar.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        self.update_status("Welcome to USV Analyzer!")

        # Disable tabs initially, except the first one
        self.notebook.tab(self.report_frame, state='disabled')
        self.notebook.tab(self.analysis_frame, state='disabled')
        self.notebook.tab(self.statistical_output_frame, state='disabled')  # Initially disabled
        self.notebook.tab(self.graphic_frame, state='disabled')  # Initially disabled

        # --- Menu Bar ---
        self.create_menu_bar()

    def update_status(self, message):
        """Updates the message in the status bar."""
        self.status_bar.config(text=message)
        self.master.update_idletasks()  # Ensures the status bar updates immediately

    def create_menu_bar(self):
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about_dialog)

    def show_about_dialog(self):
        messagebox.showinfo(
            "About USV Analyzer",
            "USV Analyzer v1.0\n\n"
            "A tool for analyzing Ultrasonic Vocalizations (USVs) data.\n"
            "Developed by João Neves with AI assistance.\n\n"
            "© 2025"
        )

    # --- Tab 1: Data Input ---
    def create_data_input_tab(self):
        self.data_input_frame = ttk.Frame(self.notebook, padding="10 10 10 10")
        self.notebook.add(self.data_input_frame, text="1. Data Input")

        # Configure grid for this frame
        self.data_input_frame.grid_rowconfigure(0, weight=0)  # Label
        self.data_input_frame.grid_rowconfigure(1, weight=0)  # Entry/Button
        self.data_input_frame.grid_rowconfigure(2, weight=1)  # Spacer
        self.data_input_frame.grid_rowconfigure(3, weight=0)  # Next button
        self.data_input_frame.grid_columnconfigure(0, weight=1)  # Entry
        self.data_input_frame.grid_columnconfigure(1, weight=0)  # Button

        # Widgets for folder selection
        ttk.Label(self.data_input_frame, text="Select Folder with Animal Data:").grid(
            row=0, column=0, sticky="w", pady=(20, 5)
        )

        self.folder_path_entry = ttk.Entry(self.data_input_frame, width=80, state='readonly')
        self.folder_path_entry.grid(row=1, column=0, sticky="ew", padx=(0, 10))

        self.browse_button = ttk.Button(self.data_input_frame, text="Browse Folder", command=self.browse_folder)
        self.browse_button.grid(row=1, column=1, sticky="e")

        # Next button for navigation
        self.next_button_data_input = ttk.Button(
            self.data_input_frame, text="Next", command=self.process_data_input, state=tk.DISABLED
        )
        self.next_button_data_input.grid(row=3, column=1, sticky="se", pady=(20, 0))  # Aligned to bottom right

        # Spacer row for better layout
        self.data_input_frame.grid_rowconfigure(2, weight=1)

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.selected_folder_path = folder_selected
            self.folder_path_entry.config(state='normal')
            self.folder_path_entry.delete(0, tk.END)
            self.folder_path_entry.insert(0, self.selected_folder_path)
            self.folder_path_entry.config(state='readonly')
            self.next_button_data_input.config(state=tk.NORMAL)
            self.update_status(f"Folder selected: {self.selected_folder_path}")
        else:
            self.selected_folder_path = None
            self.folder_path_entry.config(state='normal')
            self.folder_path_entry.delete(0, tk.END)
            self.folder_path_entry.config(state='readonly')
            self.next_button_data_input.config(state=tk.DISABLED)
            self.update_status("Folder selection cancelled.")

    def process_data_input(self):
        if not self.selected_folder_path:
            messagebox.showwarning("Input Error", "Please select a data folder first.")
            return

        self.update_status("Loading and merging data... This may take a moment.")

        # --- CALL TO THE INTEGRATED DATA LOADING/MERGING LOGIC ---
        self.df_aggregated = self._load_and_merge_data_backend(self.selected_folder_path)

        if self.df_aggregated is not None:
            self.update_status("Data loaded and merged successfully!")

            # Identify available metrics and variables from the loaded DataFrame
            all_cols = self.df_aggregated.columns.tolist()

            # Define common grouping variables that you expect
            # NOTE: These names MUST match the columns in your aggregated DataFrame
            common_grouping_vars = ['Sex', 'Genotype', 'Timepoint']

            # Filter for only those common grouping variables that actually exist in the DataFrame
            self.available_grouping_variables = [col for col in common_grouping_vars if
                                                 col in self.df_aggregated.columns]

            # Metrics are typically numerical columns that are not 'animal_id' or a grouping variable
            identifying_cols = ['animal_id'] + self.available_grouping_variables
            self.available_metrics = [
                col for col in all_cols
                if col not in identifying_cols and pd.api.types.is_numeric_dtype(self.df_aggregated[col])
            ]

            # Proceed to the next tab (Report)
            self.notebook.tab(self.report_frame, state='normal')
            self.notebook.select(self.report_frame)
            self.populate_report_tab()  # Call to populate report details
        else:
            self.update_status("Data loading failed.")

    # --- INTEGRATED CORE BACKBONE FOR DATA LOADING AND MERGING ---
    def _load_and_merge_data_backend(self, raw_data_folder):
        """
        Integrates the original data loading and merging logic.
        This function now internally manages loading metadata and individual USV files.
        """
        metadata_file_name = 'animal_metadata.csv'  # Assumed name for metadata file within the folder, change if you need
        full_metadata_path = os.path.join(raw_data_folder, metadata_file_name)

        # --- Core Backbone 1.1: Load Metadata ---
        def load_metadata_internal(file_path):
            if not os.path.exists(file_path):
                messagebox.showerror("Metadata Error", f"Metadata file not found at expected path: {file_path}\n"
                                                       "Please ensure 'animal_metadata.csv' is in the selected folder.")
                return None
            try:
                df_meta = pd.read_csv(file_path)
                print(f"Loaded metadata from: {file_path}")
                return df_meta
            except Exception as e:
                messagebox.showerror("Metadata Error", f"Error loading metadata file: {e}")
                return None

        # --- Core Backbone 1.2: Process Individual USV Files and Aggregate ---
        def process_single_usv_file_internal(file_path, animal_id, timepoint):
            if not os.path.exists(file_path):
                return None
            try:
                df_usv = pd.read_csv(file_path)
                df_usv['animal_id'] = animal_id
                df_usv['Timepoint'] = timepoint

                if 'Accepted' not in df_usv.columns:
                    return None
                df_usv['Accepted'] = df_usv['Accepted'].astype(str).str.lower().isin(['true', '1'])
                df_accepted_usv = df_usv[df_usv['Accepted'] == True].copy()

                def sanitize_col_name(col_name):
                    return col_name.replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_").replace(".",
                                                                                                                  "")

                # Initialize all expected metrics with pd.NA or 0 for counts
                all_expected_metrics_init = {
                    'animal_id': animal_id,
                    'Timepoint': timepoint,
                    'Total_USVs_Count': 0,
                    'Call_Length_s_Mean': pd.NA,
                    'Call_Length_s_Sum': pd.NA,
                    'Principal_Frequency_kHz_Mean': pd.NA,
                    'Low_Freq_kHz_Mean': pd.NA,
                    'High_Freq_kHz_Mean': pd.NA,
                    'Delta_Freq_kHz_Mean': pd.NA,
                    'Frequency_Standard_Deviation_kHz_Mean': pd.NA,
                    'Slope_kHz_s_Mean': pd.NA,
                    'Sinuosity_Mean': pd.NA,
                    'Mean_Power_dB_Hz_Mean': pd.NA,
                    'Tonality_Mean': pd.NA,
                    'Peak_Freq_kHz_Mean': pd.NA,
                }
                # Dynamically add all Label_X_Count columns based on common labels from typical USV analysis
                # This makes the output consistent even if a specific label is missing in a file
                common_usv_labels = ['Downward', '2Syllabes', 'Complex', 'Chevron', 'Harmonic', 'Composite', 'Flat',
                                     'Frequency_Step', 'DChevron', 'Upward']
                for label in common_usv_labels:
                    all_expected_metrics_init[f'Label_{label}_Count'] = 0

                if df_accepted_usv.empty:
                    return pd.Series(all_expected_metrics_init)

                aggregated_metrics = {
                    'animal_id': animal_id,
                    'Timepoint': timepoint,
                    'Total_USVs_Count': len(df_accepted_usv)
                }

                numerical_mean_cols = [
                    'Call Length (s)', 'Principal Frequency (kHz)', 'Low Freq (kHz)',
                    'High Freq (kHz)', 'Delta Freq (kHz)', 'Frequency Standard Deviation (kHz)',
                    'Slope (kHz/s)', 'Sinuosity', 'Mean Power (dB/Hz)', 'Tonality', 'Peak Freq (kHz)'
                ]

                for col in numerical_mean_cols:
                    if col in df_accepted_usv.columns and pd.api.types.is_numeric_dtype(df_accepted_usv[col]):
                        aggregated_metrics[f'{sanitize_col_name(col)}_Mean'] = df_accepted_usv[col].mean()
                    else:
                        aggregated_metrics[f'{sanitize_col_name(col)}_Mean'] = pd.NA

                if 'Call Length (s)' in df_accepted_usv.columns and pd.api.types.is_numeric_dtype(
                        df_accepted_usv['Call Length (s)']):
                    aggregated_metrics['Call_Length_s_Sum'] = df_accepted_usv['Call Length (s)'].sum()
                else:
                    aggregated_metrics['Call_Length_s_Sum'] = pd.NA

                if 'Label' in df_accepted_usv.columns:
                    label_counts = df_accepted_usv['Label'].value_counts().to_dict()
                    for label, count in label_counts.items():
                        sanitized_label = label.replace(" ", "_").replace(".", "").replace("/", "_").replace("(",
                                                                                                             "").replace(
                            ")", "")
                        aggregated_metrics[f'Label_{sanitized_label}_Count'] = count
                else:
                    pass

                final_series_data = {**all_expected_metrics_init, **aggregated_metrics}
                return pd.Series(final_series_data)

            except pd.errors.EmptyDataError:
                return None
            except Exception as e:
                messagebox.showerror("File Processing Error",
                                     f"Error processing USV file {os.path.basename(file_path)} for {animal_id} at {timepoint}: {e}. Skipping.")
                return None

        # --- Core Backbone 1.3: Process All USV Files and Combine into a DataFrame ---
        def process_all_usv_files_internal(df_meta, folder_path):
            all_aggregated_data = []
            self.update_status(f"Starting aggregation of all USV files from {folder_path}...")

            # Ensure df_meta has 'Filename', 'animal_id', 'Timepoint'
            required_meta_cols = ['Filename', 'animal_id', 'Timepoint']
            if not all(col in df_meta.columns for col in required_meta_cols):
                messagebox.showerror("Metadata Error",
                                     f"Metadata file must contain '{', '.join(required_meta_cols)}' columns.")
                return None

            total_files = len(df_meta)
            for index, row in df_meta.iterrows():
                animal_id = row['animal_id']
                timepoint = row['Timepoint']
                filename = row['Filename']

                file_path = os.path.join(folder_path, filename)
                self.update_status(f"Processing file {index + 1}/{total_files}: {filename}")

                aggregated_series = process_single_usv_file_internal(file_path, animal_id, timepoint)

                if aggregated_series is not None:
                    all_aggregated_data.append(aggregated_series)

            if not all_aggregated_data:
                messagebox.showerror("Data Aggregation Error",
                                     "No data was successfully aggregated from any USV files. Check file names and structure.")
                return None

            df_aggregated_raw = pd.DataFrame(all_aggregated_data)

            # Merge the metadata columns (Sex, Genotype) into the aggregated DataFrame
            metadata_cols_for_merge = df_meta[['animal_id', 'Timepoint', 'Sex', 'Genotype']].drop_duplicates()
            df_final_results = pd.merge(
                df_aggregated_raw,
                metadata_cols_for_merge,
                on=['animal_id', 'Timepoint'],
                how='left'
            )
            self.update_status("Successfully aggregated and merged data.")
            return df_final_results

        # --- Main orchestration within _load_and_merge_data_backend ---
        df_metadata = load_metadata_internal(full_metadata_path)

        if df_metadata is not None:
            final_aggregated_df = process_all_usv_files_internal(df_metadata, raw_data_folder)
            return final_aggregated_df
        else:
            return None

    # --- Tab 2: Data Report ---
    def create_report_tab(self):
        self.report_frame = ttk.Frame(self.notebook, padding="10 10 10 10")
        self.notebook.add(self.report_frame, text="2. Data Report")

        # Text widget for scrollable report
        self.report_text_area = tk.Text(self.report_frame, wrap="word", height=15, width=80, state='disabled')
        self.report_text_area.pack(pady=10, padx=10, expand=True, fill="both")

        # Scrollbar for the text area
        report_text_scroll = ttk.Scrollbar(self.report_text_area, command=self.report_text_area.yview)
        report_text_scroll.pack(side="right", fill="y")
        self.report_text_area.config(yscrollcommand=report_text_scroll.set)

        self.next_button_report = ttk.Button(
            self.report_frame, text="Next", command=self.go_to_analysis_tab
        )
        self.next_button_report.pack(side="bottom", anchor="se", pady=(20, 0))

    def populate_report_tab(self):
        """Populates the report tab with detailed information."""
        self.report_text_area.config(state='normal')  # Enable editing
        self.report_text_area.delete(1.0, tk.END)  # Clear previous content

        if self.df_aggregated is not None:
            num_animals = len(self.df_aggregated['animal_id'].unique())

            report_text = f"Your dataset contains data for {num_animals} animals.\n\n"

            report_text += "Identified variables:\n"
            for var in self.available_grouping_variables:
                report_text += f"  - {var}\n"

            report_text += "\nAvailable metrics:\n"
            for metric in self.available_metrics:
                report_text += f"  - {metric}\n"

            self.report_text_area.insert(tk.END, report_text)
            self.notebook.tab(self.analysis_frame, state='normal')  # Enable next tab after report is shown
        else:
            self.report_text_area.insert(tk.END, "No data loaded to generate report.")

        self.report_text_area.config(state='disabled')  # Disable editing

    # --- Tab 3: Analysis Options ---
    def create_analysis_tab(self):
        self.analysis_frame = ttk.Frame(self.notebook, padding="10 10 10 10")
        self.notebook.add(self.analysis_frame, text="3. Analysis Options")

        # Configure grid for this tab's frame
        self.analysis_frame.grid_columnconfigure(0, weight=1)
        self.analysis_frame.grid_columnconfigure(1, weight=1)
        self.analysis_frame.grid_rowconfigure(0, weight=0)  # Labels and dropdowns
        self.analysis_frame.grid_rowconfigure(1, weight=0)
        self.analysis_frame.grid_rowconfigure(2, weight=0)
        self.analysis_frame.grid_rowconfigure(3, weight=1)  # Spacer
        self.analysis_frame.grid_rowconfigure(4, weight=0)  # Run button

        # Metric Selection
        ttk.Label(self.analysis_frame, text="Select Metric:").grid(row=0, column=0, sticky="w", pady=(10, 5), padx=5)
        self.metric_combobox = ttk.Combobox(self.analysis_frame, state="readonly")
        self.metric_combobox.grid(row=0, column=1, sticky="ew", pady=(10, 5), padx=5)

        # Primary Grouping Variable
        ttk.Label(self.analysis_frame, text="Select Primary Grouping Variable:").grid(row=1, column=0, sticky="w",
                                                                                      pady=5, padx=5)
        self.primary_group_combobox = ttk.Combobox(self.analysis_frame, state="readonly")
        self.primary_group_combobox.grid(row=1, column=1, sticky="ew", pady=5, padx=5)
        self.primary_group_combobox.bind("<<ComboboxSelected>>",
                                         self.update_secondary_grouping_options)  # Bind to update secondary

        # Secondary Grouping Variable
        self.secondary_group_enabled_var = tk.BooleanVar(value=False)  # Default to unchecked
        self.secondary_group_checkbox = ttk.Checkbutton(
            self.analysis_frame, text="Enable Secondary Grouping Variable",
            variable=self.secondary_group_enabled_var,
            command=self.toggle_secondary_group_state
        )
        self.secondary_group_checkbox.grid(row=2, column=0, sticky="w", pady=5, padx=5)

        self.secondary_group_combobox = ttk.Combobox(self.analysis_frame, state="disabled")
        self.secondary_group_combobox.grid(row=2, column=1, sticky="ew", pady=5, padx=5)

        # Run Analysis Button
        self.run_analysis_button = ttk.Button(self.analysis_frame, text="Run Analysis", command=self.run_analysis)
        self.run_analysis_button.grid(row=4, column=1, sticky="se", pady=(20, 0))

        # Back button for navigation
        ttk.Button(self.analysis_frame, text="Back", command=lambda: self.notebook.select(self.report_frame)).grid(
            row=4, column=0, sticky="sw", pady=(20, 0)
        )

    def toggle_secondary_group_state(self):
        """Enables/disables secondary group combobox and populates it."""
        if self.secondary_group_enabled_var.get():
            self.secondary_group_combobox.config(state="readonly")
            self.update_secondary_grouping_options()
        else:
            self.secondary_group_combobox.config(state="disabled")
            self.secondary_group_combobox.set("")  # Clear selection when disabled

    def update_secondary_grouping_options(self, event=None):
        """Populates secondary grouping combobox based on primary selection."""
        if self.secondary_group_enabled_var.get():
            selected_primary = self.primary_group_combobox.get()
            if self.df_aggregated is not None and selected_primary:
                # Secondary grouping cannot be the same as primary
                filtered_secondary_options = [gv for gv in self.available_grouping_variables if gv != selected_primary]
                self.secondary_group_combobox['values'] = filtered_secondary_options
                # If current secondary selection is the same as new primary, or not in new options, reset it
                current_secondary_selection = self.secondary_group_combobox.get()
                if current_secondary_selection == selected_primary or current_secondary_selection not in filtered_secondary_options:
                    if filtered_secondary_options:  # Select first option if available
                        self.secondary_group_combobox.set(filtered_secondary_options[0])
                    else:
                        self.secondary_group_combobox.set("")  # Clear if no options
            else:
                self.secondary_group_combobox['values'] = []
                self.secondary_group_combobox.set("")
        # No action needed if checkbox is not checked, as state is 'disabled' then.

    def go_to_analysis_tab(self):
        # Populate comboboxes before going to the tab
        self.metric_combobox['values'] = self.available_metrics
        if self.available_metrics:
            self.metric_combobox.set(self.available_metrics[0])  # Select first by default

        self.primary_group_combobox['values'] = self.available_grouping_variables
        if self.available_grouping_variables:
            self.primary_group_combobox.set(self.available_grouping_variables[0])  # Select first by default

        # Initialize secondary combobox and checkbox
        self.secondary_group_enabled_var.set(False)  # Ensure it's unchecked by default
        self.toggle_secondary_group_state()  # Apply initial disabled state and clear values

        self.notebook.select(self.analysis_frame)

    # --- Statistical Analysis & Plotting Methods (integrated from your code) ---

    def get_significance_label(self, p_value):
        if p_value < 0.001:
            return '***'
        elif p_value < 0.01:
            return '**'
        elif p_value < 0.05:
            return '*'
        else:
            return 'ns'

    def calculate_cohens_d(self, group1_data, group2_data):
        n1, n2 = len(group1_data), len(group2_data)
        if n1 == 0 or n2 == 0: return np.nan
        s1, s2 = np.std(group1_data, ddof=1), np.std(group2_data, ddof=1)
        pooled_std = np.sqrt(((n1 - 1) * s1 ** 2 + (n2 - 1) * s2 ** 2) / (n1 + n2 - 2)) if (n1 + n2 - 2) > 0 else 0
        if pooled_std == 0: return 0.0
        return (np.mean(group1_data) - np.mean(group2_data)) / pooled_std

    def calculate_partial_eta_squared(self, anova_table, effect_row_name):
        ss_effect = anova_table.loc[effect_row_name, 'sum_sq']
        if 'Residual' in anova_table.index:
            ss_error = anova_table.loc['Residual', 'sum_sq']
        else:
            ss_error = 0  # Fallback
        if ss_effect + ss_error == 0: return np.nan
        return ss_effect / (ss_effect + ss_error)

    def check_normality(self, df, group_var, metric):
        is_normal_all_groups = True
        normality_results_str = "\n  - Assessing Normality (Shapiro-Wilk Test):\n"
        for name, group in df.groupby(group_var, observed=False):
            data = group[metric].dropna()
            if len(data) >= 3:
                stat, p = stats.shapiro(data)
                normality_results_str += f"    - Group '{name}' (p={p:.3f}) {'is normally distributed.' if p >= 0.05 else 'is NOT normally distributed.'}\n"
                if p < 0.05: is_normal_all_groups = False
            else:
                normality_results_str += f"    - Group '{name}' has too few samples ({len(data)}) for Shapiro-Wilk test. Skipping normality check.\n"
                is_normal_all_groups = False
        return is_normal_all_groups, normality_results_str

    def check_homogeneity_of_variance(self, df, group_var, metric):
        groups_data = [group[metric].dropna() for name, group in
                       df.groupby(group_var, observed=False)]
        groups_data = [g for g in groups_data if len(g) > 1]

        if len(groups_data) < 2:
            return True, np.nan, "    - Not enough groups or data points per group for Levene's test. Skipping homogeneity of variance check."

        stat, p = stats.levene(*groups_data)
        homogeneity_str = f"  - Assessing Homogeneity of Variances (Levene's Test):\n"
        homogeneity_str += f"    - Levene's test (p={p:.3f}) indicates {'equal variances (homoscedasticity).' if p >= 0.05 else 'unequal variances (heteroscedasticity).'} \n"
        return p >= 0.05, p, homogeneity_str

    def _get_user_choice_on_assumptions_gui(self, assumption_type, test_name, default_to_parametric=False):
        """
        Presents a Tkinter messagebox for user choice on assumption violation.
        Returns True for "Yes, run parametric", False for "No, run non-parametric".
        """
        if default_to_parametric:
            title = "Assumption Warning"
            message = f"Statistical assumptions ({assumption_type}) for {test_name} (parametric) were not met.\n" \
                      "Do you want to proceed with the parametric test anyway? (Selecting 'No' will run non-parametric alternative)"
            return messagebox.askyesno(title, message)
        else:
            title = "Assumption Violation - Proceeding Non-Parametric"
            message = f"Statistical assumptions ({assumption_type}) for {test_name} (parametric) were not met.\n" \
                      "Proceeding with non-parametric alternative. Do you wish to override and run parametric anyway?"
            # In this case, 'No' means stick to non-parametric (default behavior if assumptions are violated)
            # 'Yes' means override and run parametric
            return messagebox.askyesno(title, message)

    def perform_statistical_analysis(self, df, metric, group_var1, group_var2=None):
        all_statistical_results = []
        significant_comparisons_for_plot = []

        self.log_to_gui(f"\n--- Statistical Analysis for '{metric}' ---")

        df_analysis = df.copy()
        # Explicitly convert to categorical AFTER replacing labels
        if 'Sex' in df_analysis.columns:
            df_analysis['Sex'] = df_analysis['Sex'].replace(self.SEX_LABELS).astype('category')
        if 'Genotype' in df_analysis.columns:
            df_analysis['Genotype'] = df_analysis['Genotype'].replace(self.GENOTYPE_LABELS).astype('category')
        if 'Timepoint' in df_analysis.columns:
            present_timepoints = [tp for tp in self.TIMEPOINT_ORDER if tp in df_analysis['Timepoint'].unique()]
            if present_timepoints:
                df_analysis['Timepoint'] = pd.Categorical(df_analysis['Timepoint'], categories=present_timepoints,
                                                          ordered=True)
            else:
                df_analysis['Timepoint'] = df_analysis['Timepoint'].astype(
                    'category')  # Convert even if no specific order

        grouping_vars_for_dropna = [metric] + [gv for gv in [group_var1, group_var2, 'animal_id'] if gv is not None]
        df_cleaned = df_analysis.dropna(
            subset=grouping_vars_for_dropna).copy()

        if df_cleaned.empty:
            self.log_to_gui(f"Not enough complete data for statistical analysis of '{metric}' after dropping NaNs.")
            return [], []

        min_samples_per_group = 3
        actual_grouping_for_counts = [gv for gv in [group_var1, group_var2] if gv is not None]
        if actual_grouping_for_counts:
            group_counts = df_cleaned.groupby(actual_grouping_for_counts, observed=False).size()
            if any(group_counts < min_samples_per_group):
                self.log_to_gui(f"Warning: Some groups have fewer than {min_samples_per_group} samples.")
                self.log_to_gui("Statistical tests may not be reliable. Group counts:")
                self.log_to_gui(group_counts.to_string())
        else:
            if len(df_cleaned) < min_samples_per_group:
                self.log_to_gui(
                    f"Warning: Total samples ({len(df_cleaned)}) less than {min_samples_per_group}. Statistical tests may not be reliable.")

        is_time_as_factor = ('Timepoint' == group_var1) or ('Timepoint' == group_var2)

        # Determine if it's a Repeated Measures design based on 'animal_id' and 'Timepoint'
        is_repeated_measures = False
        if 'animal_id' in df_cleaned.columns and 'Timepoint' in df_cleaned.columns:
            # Check if each animal_id has multiple entries across timepoints
            animal_timepoint_counts = df_cleaned.groupby('animal_id', observed=False)[
                'Timepoint'].nunique()
            if (animal_timepoint_counts > 1).any():
                # For this specific analysis, assuming Timepoint is within-subject
                if 'Timepoint' == group_var1 or 'Timepoint' == group_var2:  # Only flag as RM if timepoint is a factor being analyzed
                    is_repeated_measures = True

        # --- Case 1: One-way independent (e.g., Genotype, Sex) or One-way RM (Timepoint only) ---
        if group_var2 is None:
            if is_repeated_measures:  # One-way Repeated Measures ANOVA
                self.log_to_gui(f"\n  - Considering One-way Repeated Measures ANOVA for '{metric}' by '{group_var1}':")
                try:
                    self.log_to_gui(f"  - Dataframe head for RM ANOVA:\n{df_cleaned.head()}")
                    self.log_to_gui(
                        f"  - Dataframe dtypes for RM ANOVA:\n{df_cleaned[[metric, group_var1, 'animal_id']].dtypes}")
                    self.log_to_gui(f"  - Unique subjects: {df_cleaned['animal_id'].nunique()}")
                    self.log_to_gui(f"  - Unique within-levels ({group_var1}): {df_cleaned[group_var1].unique()}")

                    aov_rm = pg.rm_anova(data=df_cleaned, dv=metric, within=group_var1, subject='animal_id',
                                         effsize='np2', correction='auto')  # Removed 'detailed=True'
                    self.log_to_gui(str(aov_rm))

                    mauchly_spher = pg.sphericity(data=df_cleaned, dv=metric, within=group_var1, subject='animal_id')
                    sphericity_p = mauchly_spher['p-unc'].iloc[0] if isinstance(mauchly_spher,
                                                                                pd.DataFrame) and not mauchly_spher.empty else np.nan

                    self.log_to_gui(
                        f"  - Mauchly's Test for Sphericity (p={sphericity_p:.3f}): {'Sphericity assumed.' if sphericity_p >= 0.05 else 'Sphericity violated. Greenhouse-Geisser/Huynh-Feldt correction applied.'}")

                    p_value_rm = aov_rm['p-unc'].iloc[0]
                    partial_eta_sq_rm = aov_rm['np2'].iloc[0]

                    all_statistical_results.append({
                        'Metric': metric, 'Test_Type': 'One-Way Repeated Measures ANOVA', 'Comparison': group_var1,
                        'F_Statistic': aov_rm['F'].iloc[0], 'P_Value': p_value_rm, 'Effect_Size': partial_eta_sq_rm,
                        'Significance': self.get_significance_label(p_value_rm),
                        'Details': f"Sphericity p: {sphericity_p:.3f}"
                    })
                    self.log_to_gui(
                        f"    - Effect of {group_var1}: F-statistic={aov_rm['F'].iloc[0]:.3f}, p-value={p_value_rm:.3f}, Partial Eta-squared={partial_eta_sq_rm:.3f}")
                    if p_value_rm < 0.05:
                        self.log_to_gui(f"      -> Statistically significant effect of {group_var1}.")
                        self.log_to_gui("\n    - Performing pairwise post-hoc tests (Bonferroni corrected):")
                        # Changed from pairwise_t-tests to pairwise_tests
                        posthoc_rm = pg.pairwise_tests(data=df_cleaned, dv=metric, within=group_var1,
                                                       subject='animal_id', padjust='bonferroni')
                        self.log_to_gui(str(posthoc_rm))
                        for _, row in posthoc_rm.iterrows():
                            # Add individual post-hoc results to the table
                            all_statistical_results.append({
                                'Metric': metric,
                                'Test_Type': 'Pairwise t-test (Bonferroni)',
                                'Comparison': f"{row['A']} vs {row['B']}",
                                'F_Statistic': np.nan,  # Not applicable for pairwise t-test
                                'P_Value': row['p-corr'],
                                'Effect_Size': row['cohen-d'] if 'cohen-d' in row else np.nan,
                                'Significance': self.get_significance_label(row['p-corr']),
                                'Details': 'Post-hoc for RM ANOVA'
                            })
                            if row['p-corr'] < 0.05:
                                significant_comparisons_for_plot.append({
                                    'groups': (row['A'], row['B']), 'p': row['p-corr'],
                                    'label': self.get_significance_label(row['p-corr'])
                                })
                    else:
                        self.log_to_gui(
                            f"      -> No statistically significant effect of {group_var1} (p={p_value_rm:.3f}).")


                except Exception as e:
                    self.log_to_gui(f"Error performing Repeated Measures ANOVA: {e}")
                    self.log_to_gui(traceback.format_exc())  # Log the full traceback
                    messagebox.showerror("Analysis Error",
                                         "Failed to perform Repeated Measures ANOVA. Check data structure and raw log output for details. Falling back to non-parametric Friedman test.")
                    # Fallback to Friedman test
                    try:
                        df_friedman = df_cleaned.pivot_table(index='animal_id', columns=group_var1, values=metric,
                                                             aggfunc='first')
                        df_friedman = df_friedman.dropna()
                        if df_friedman.empty:
                            self.log_to_gui(
                                "    - Not enough complete cases for Friedman test after pivoting and dropping NaNs.")
                            return [], []
                        friedman_stat, friedman_p = stats.friedmanchisquare(
                            *[df_friedman[col].values for col in df_friedman.columns])
                        self.log_to_gui(
                            f"    - Friedman Test: Chi-square={friedman_stat:.3f}, p-value={friedman_p:.3f}")

                        all_statistical_results.append({
                            'Metric': metric, 'Test_Type': 'Friedman Test', 'Comparison': group_var1,
                            'F_Statistic': friedman_stat, 'P_Value': friedman_p, 'Effect_Size': np.nan,
                            'Significance': self.get_significance_label(friedman_p),
                            'Details': 'Non-parametric alternative due to RM ANOVA failure.'
                        })

                        if friedman_p < 0.05:
                            self.log_to_gui(
                                f"    - Conclusion: Statistically significant difference in ranks of {metric} across {group_var1} timepoints.")
                            self.log_to_gui(
                                "\n    - Performing post-hoc Wilcoxon signed-rank tests (Bonferroni corrected):")
                            timepoints = df_friedman.columns.tolist()
                            for t1, t2 in combinations(timepoints, 2):
                                data1 = df_friedman[t1].dropna()
                                data2 = df_friedman[t2].dropna()
                                if len(data1) > 0 and len(data2) > 0:
                                    wilcox_stat, wilcox_p = stats.wilcoxon(data1, data2, alternative='two-sided')
                                    num_comparisons = len(list(combinations(timepoints, 2)))
                                    corrected_p = wilcox_p * num_comparisons

                                    all_statistical_results.append({
                                        'Metric': metric,
                                        'Test_Type': 'Wilcoxon Signed-Rank Test (Bonferroni)',
                                        'Comparison': f"{t1} vs {t2}",
                                        'F_Statistic': np.nan,
                                        'P_Value': corrected_p,
                                        'Effect_Size': np.nan,  # No standard effect size from scipy wilcoxon
                                        'Significance': self.get_significance_label(corrected_p),
                                        'Details': 'Post-hoc for Friedman Test'
                                    })

                                    if corrected_p < 0.05:
                                        significant_comparisons_for_plot.append({
                                            'groups': (t1, t2), 'p': corrected_p,
                                            'label': self.get_significance_label(corrected_p)
                                        })
                                    self.log_to_gui(
                                        f"      - {t1} vs {t2}: W={wilcox_stat:.3f}, p={wilcox_p:.3f} (Bonferroni corrected p={corrected_p:.3f})")
                        else:
                            self.log_to_gui(
                                f"    - Conclusion: No statistically significant difference in ranks of {metric} across {group_var1} timepoints.")

                    except Exception as fe:
                        self.log_to_gui(f"Error performing Friedman test: {fe}")
                        self.log_to_gui(traceback.format_exc())  # Log the full traceback for fallback
                        messagebox.showerror("Analysis Error",
                                             "Cannot perform repeated measures analysis (Friedman fallback also failed).")
                        return [], []

            else:  # One-way independent ANOVA (or t-test)
                unique_groups = df_cleaned[group_var1].unique()
                if len(unique_groups) < 2:
                    self.log_to_gui(
                        f"  - Not enough unique groups in {group_var1} for statistical comparison ({len(unique_groups)} groups found).")
                    return [], []

                self.log_to_gui(f"\n  - Considering analysis for {metric} by {group_var1}:")

                is_normal_all_groups, normality_str = self.check_normality(df_cleaned, group_var1, metric)
                self.log_to_gui(normality_str)
                is_homogeneous_variance, levene_p, homogeneity_str = self.check_homogeneity_of_variance(df_cleaned,
                                                                                                        group_var1,
                                                                                                        metric)
                self.log_to_gui(homogeneity_str)

                run_parametric = is_normal_all_groups and is_homogeneous_variance

                if not run_parametric:
                    self.log_to_gui("\n  - Assumptions not fully met for parametric test.")
                    user_choice = messagebox.askyesno(
                        "Assumption Violation",
                        "Statistical assumptions (Normality and/or Homogeneity of Variances) were not met.\n"
                        "Do you want to proceed with the parametric test (ANOVA/t-test) anyway?\n"
                        "Click 'No' to run a non-parametric alternative (Kruskal-Wallis/Mann-Whitney U)."
                    )
                    run_parametric = user_choice
                    if run_parametric:
                        self.log_to_gui(
                            "  - Proceeding with parametric test despite assumption warnings. Interpret results with caution.")
                    else:
                        self.log_to_gui("  - Proceeding with non-parametric alternative as requested.")
                else:
                    self.log_to_gui("\n  - Assumptions met for parametric test.")

                if run_parametric:
                    if len(unique_groups) == 2:
                        self.log_to_gui("\n  - Performing Independent Samples t-test (parametric):")
                        group1_data = df_cleaned[df_cleaned[group_var1] == unique_groups[0]][metric]
                        group2_data = df_cleaned[df_cleaned[group_var1] == unique_groups[1]][metric]

                        test_name_full = "Independent t-test"
                        t_stat = np.nan
                        p_value = np.nan
                        cohens_d_val = np.nan

                        if not is_homogeneous_variance:
                            t_stat, p_value = stats.ttest_ind(group1_data, group2_data, equal_var=False)
                            test_name_full = "Welch's Independent t-test"
                            self.log_to_gui("    (Using Welch's t-test due to unequal variances)")
                        else:
                            t_stat, p_value = stats.ttest_ind(group1_data, group2_data, equal_var=True)

                        cohens_d_val = self.calculate_cohens_d(group1_data, group2_data)

                        self.log_to_gui(
                            f"    - {test_name_full}: t-statistic={t_stat:.3f}, p-value={p_value:.3f}, Cohen's d={cohens_d_val:.3f}")

                        all_statistical_results.append({
                            'Metric': metric, 'Test_Type': test_name_full,
                            'Comparison': f'{unique_groups[0]} vs {unique_groups[1]}',
                            'F_Statistic': t_stat, 'P_Value': p_value, 'Effect_Size': cohens_d_val,
                            'Significance': self.get_significance_label(p_value),
                            'Details': f"Homogeneity_of_Variance_p: {levene_p:.3f}"
                        })
                        if p_value < 0.05:
                            self.log_to_gui(
                                f"    - Conclusion: Statistically significant difference in {metric} between {unique_groups[0]} and {unique_groups[1]}.")
                            significant_comparisons_for_plot.append({
                                'groups': (unique_groups[0], unique_groups[1]), 'p': p_value,
                                'label': self.get_significance_label(p_value)
                            })
                        else:
                            self.log_to_gui(
                                f"    - Conclusion: No statistically significant difference in {metric} between {unique_groups[0]} and {unique_groups[1]}.")

                    else:  # More than 2 unique groups -> One-way ANOVA (parametric)
                        self.log_to_gui("\n  - Performing One-way ANOVA (parametric):")
                        formula = f'{metric} ~ C({group_var1})'
                        model = ols(formula, data=df_cleaned).fit()
                        anova_table = sm.stats.anova_lm(model, typ=2)
                        self.log_to_gui(str(anova_table))

                        p_value = anova_table['PR(>F)'][f'C({group_var1})']
                        partial_eta_sq = self.calculate_partial_eta_squared(anova_table, f'C({group_var1})')

                        all_statistical_results.append({
                            'Metric': metric, 'Test_Type': 'One-Way ANOVA', 'Comparison': group_var1,
                            'F_Statistic': anova_table['F'][f'C({group_var1})'], 'P_Value': p_value,
                            'Effect_Size': partial_eta_sq,
                            'Significance': self.get_significance_label(p_value),
                            'Details': f"Homogeneity_of_Variance_p: {levene_p:.3f}"
                        })

                        if p_value < 0.05:
                            self.log_to_gui(
                                f"    - Conclusion: Statistically significant effect of {group_var1} on {metric}.")
                            self.log_to_gui("\n    - Performing Tukey HSD post-hoc test:")
                            tukey_results = pairwise_tukeyhsd(endog=df_cleaned[metric], groups=df_cleaned[group_var1],
                                                              alpha=0.05)
                            self.log_to_gui(str(tukey_results))
                            for row in tukey_results.summary().data[1:]:
                                group1, group2, mean_diff, lower_ci, upper_ci, p_val, reject = row[
                                                                                               :7]  # Extract relevant columns
                                # Only add significant comparisons to the plot annotations, but add all to table
                                all_statistical_results.append({
                                    'Metric': metric,
                                    'Test_Type': 'Tukey HSD Post-hoc',
                                    'Comparison': f"{group1} vs {group2}",
                                    'F_Statistic': np.nan,  # Not applicable for post-hoc
                                    'P_Value': p_val,
                                    'Effect_Size': mean_diff,  # Using mean difference as effect size for Tukey
                                    'Significance': self.get_significance_label(p_val),
                                    'Details': f"Mean Diff: {mean_diff:.3f}, CI: [{lower_ci:.3f}, {upper_ci:.3f}]"
                                })
                                if p_val < 0.05:
                                    significant_comparisons_for_plot.append({
                                        'groups': (group1, group2), 'p': p_val,
                                        'label': self.get_significance_label(p_val)
                                    })
                        else:
                            self.log_to_gui(
                                f"    - Conclusion: No statistically significant effect of {group_var1} on {metric} (p={p_value:.3f}).")

                else:  # Non-parametric alternative (if parametric test declined or assumptions not met)
                    if len(unique_groups) == 2:
                        self.log_to_gui("\n  - Performing Mann-Whitney U test (non-parametric):")
                        group1_data = df_cleaned[df_cleaned[group_var1] == unique_groups[0]][metric]
                        group2_data = df_cleaned[df_cleaned[group_var1] == unique_groups[1]][metric]
                        stat, p_value = stats.mannwhitneyu(group1_data, group2_data, alternative='two-sided')

                        r_effect_size = \
                        pg.pairwise_tests(x=group1_data, y=group2_data, alternative='two-sided', parametric=False)[
                            'RBC'].iloc[0] if not group1_data.empty and not group2_data.empty else np.nan

                        self.log_to_gui(
                            f"    - Mann-Whitney U test: U-statistic={stat:.3f}, p-value={p_value:.3f}, Rank-Biserial Correlation={r_effect_size:.3f}")
                        all_statistical_results.append({
                            'Metric': metric, 'Test_Type': 'Mann-Whitney U test',
                            'Comparison': f'{unique_groups[0]} vs {unique_groups[1]}',
                            'F_Statistic': stat, 'P_Value': p_value, 'Effect_Size': r_effect_size,
                            'Significance': self.get_significance_label(p_value),
                            'Details': 'Non-parametric alternative.'
                        })
                        if p_value < 0.05:
                            self.log_to_gui(
                                f"    - Conclusion: Statistically significant difference in ranks of {metric} between {unique_groups[0]} and {unique_groups[1]}.")
                            significant_comparisons_for_plot.append({
                                'groups': (unique_groups[0], unique_groups[1]), 'p': p_value,
                                'label': self.get_significance_label(p_value)
                            })
                        else:
                            self.log_to_gui(
                                f"    - Conclusion: No statistically significant difference in ranks of {metric} between {unique_groups[0]} and {unique_groups[1]}.")

                    else:  # More than 2 unique groups -> Kruskal-Wallis H-test (non-parametric)
                        self.log_to_gui("\n  - Performing Kruskal-Wallis H-test (non-parametric):")
                        groups_data_kruskal = [df_cleaned[metric][df_cleaned[group_var1] == g].dropna() for g in
                                               unique_groups]
                        stat, p_value = stats.kruskal(*groups_data_kruskal)

                        all_statistical_results.append({
                            'Metric': metric, 'Test_Type': 'Kruskal-Wallis H-test', 'Comparison': group_var1,
                            'F_Statistic': stat, 'P_Value': p_value, 'Effect_Size': np.nan,
                            'Significance': self.get_significance_label(p_value),
                            'Details': 'Non-parametric alternative due to assumption violation or user choice.'
                        })
                        self.log_to_gui(f"    - Kruskal-Wallis H-test: H-statistic={stat:.3f}, p-value={p_value:.3f}")
                        if p_value < 0.05:
                            self.log_to_gui(
                                f"    - Conclusion: Statistically significant difference in ranks of {metric} between groups.")
                            self.log_to_gui(
                                "\n    - Performing Dunn's Post-hoc test (using Bonferroni correction for pairwise comparisons):")
                            # Changed from pairwise_ttests to pairwise_tests
                            posthoc_kw = pg.pairwise_tests(data=df_cleaned, dv=metric, between=group_var1,
                                                           parametric=False,
                                                           padjust='bonferroni')
                            self.log_to_gui(str(posthoc_kw))

                            for _, row in posthoc_kw.iterrows():
                                p_val_to_use = row['p-corr'] if 'p-corr' in row else row['p-unc']
                                # Add individual post-hoc results to the table
                                all_statistical_results.append({
                                    'Metric': metric,
                                    'Test_Type': 'Dunn\'s Post-hoc (Bonferroni)',
                                    'Comparison': f"{row['A']} vs {row['B']}",
                                    'F_Statistic': np.nan,
                                    'P_Value': p_val_to_use,
                                    'Effect_Size': row['RBC'] if 'RBC' in row else np.nan,  # Rank-Biserial Correlation
                                    'Significance': self.get_significance_label(p_val_to_use),
                                    'Details': 'Post-hoc for Kruskal-Wallis'
                                })
                                if p_val_to_use < 0.05:
                                    significant_comparisons_for_plot.append({
                                        'groups': (row['A'], row['B']),
                                        'p': p_val_to_use,
                                        'label': self.get_significance_label(p_val_to_use)
                                    })
                        else:
                            self.log_to_gui(
                                f"    - Conclusion: No statistically significant difference in ranks of {metric} between groups.")

        # --- Case 2: Two-way independent ANOVA or Case 3: Mixed ANOVA ---
        elif group_var2 is not None:
            if is_repeated_measures:  # Mixed ANOVA (Timepoint as one factor, other as between-subjects)
                independent_factor = group_var1 if group_var1 != 'Timepoint' else group_var2
                repeated_factor = 'Timepoint'

                if independent_factor not in df_cleaned.columns:
                    self.log_to_gui(f"Independent factor '{independent_factor}' not found in data for mixed ANOVA.")
                    return [], []

                self.log_to_gui(
                    f"\n  - Considering Mixed ANOVA for '{metric}' with between-subject factor '{independent_factor}' and within-subject factor '{repeated_factor}':")

                try:
                    self.log_to_gui(f"  - Dataframe head for Mixed ANOVA:\n{df_cleaned.head()}")
                    self.log_to_gui(
                        f"  - Dataframe dtypes for Mixed ANOVA:\n{df_cleaned[[metric, repeated_factor, independent_factor, 'animal_id']].dtypes}")
                    self.log_to_gui(f"  - Unique subjects: {df_cleaned['animal_id'].nunique()}")
                    self.log_to_gui(
                        f"  - Unique within-levels ({repeated_factor}): {df_cleaned[repeated_factor].unique()}")
                    self.log_to_gui(
                        f"  - Unique between-levels ({independent_factor}): {df_cleaned[independent_factor].unique()}")

                    aov_mixed = pg.mixed_anova(data=df_cleaned, dv=metric, within=repeated_factor,
                                               between=independent_factor, subject='animal_id', effsize='np2',
                                               correction='auto')
                    self.log_to_gui(str(aov_mixed))

                    mauchly_sphericity = pg.sphericity(data=df_cleaned, dv=metric, within=repeated_factor,
                                                       subject='animal_id')
                    sphericity_p = np.nan
                    if isinstance(mauchly_sphericity, pd.DataFrame) and not mauchly_sphericity.empty:
                        sphericity_p = mauchly_sphericity['p-unc'].iloc[0]
                    else:
                        self.log_to_gui(
                            f"  - Mauchly's Test for Sphericity returned non-DataFrame result (type: {type(mauchly_sphericity)}). Assuming sphericity or test not applicable.")

                    self.log_to_gui(
                        f"  - Mauchly's Test for Sphericity (p={sphericity_p:.3f}): {'Sphericity assumed.' if (sphericity_p >= 0.05 or pd.isna(sphericity_p)) else 'Sphericity violated. Greenhouse-Geisser correction applied.'}")

                    effects = [independent_factor, repeated_factor, f'{independent_factor} * {repeated_factor}']
                    for effect in effects:
                        row_source = effect
                        if effect == f'{independent_factor} * {repeated_factor}':
                            row_source = f'{independent_factor} * {repeated_factor}'

                        if row_source in aov_mixed['Source'].values:
                            row_data = aov_mixed[aov_mixed['Source'] == row_source].iloc[0]
                            p_value = row_data['p-unc']
                            partial_eta_sq = row_data['np2']

                            all_statistical_results.append({
                                'Metric': metric, 'Test_Type': 'Mixed ANOVA',
                                'Comparison': effect.replace(' * ', ' x '),
                                'F_Statistic': row_data['F'], 'P_Value': p_value,
                                'Effect_Size': partial_eta_sq, 'Significance': self.get_significance_label(p_value),
                                'Details': f"Sphericity p: {sphericity_p:.3f}"
                            })
                            self.log_to_gui(
                                f"    - Effect of {effect}: F-statistic={row_data['F']:.3f}, p-value={p_value:.3f}, Partial Eta-squared={partial_eta_sq:.3f}")
                            if p_value < 0.05:
                                self.log_to_gui(f"      -> Statistically significant effect of {effect}.")

                    # Post-hoc for interaction if significant
                    interaction_term = f'{independent_factor} * {repeated_factor}'
                    interaction_row = aov_mixed[aov_mixed['Source'] == interaction_term]
                    if not interaction_row.empty and interaction_row['p-unc'].iloc[0] < 0.05:
                        self.log_to_gui("\n    - Significant interaction detected. Performing post-hoc comparisons:")
                        # Changed from pairwise_ttests to pairwise_tests
                        posthoc_interaction = pg.pairwise_tests(data=df_cleaned, dv=metric, within=repeated_factor,
                                                                between=independent_factor, subject='animal_id',
                                                                padjust='bonferroni')
                        self.log_to_gui(str(posthoc_interaction))
                        for _, row in posthoc_interaction.iterrows():
                            # For plotting, need a way to identify the groups. Format as (between_group, within_group)
                            # Example: (Males, P4) vs (Males, P6)
                            g1_between_level = row[independent_factor]
                            g1_within_level = row['A']
                            g2_within_level = row['B']  # Only within-subject is changing in these comparisons

                            all_statistical_results.append({
                                'Metric': metric,
                                'Test_Type': f'Pairwise t-test (Mixed ANOVA Post-hoc)',
                                'Comparison': f"{independent_factor} ({g1_between_level}): {g1_within_level} vs {g2_within_level}",
                                'F_Statistic': np.nan,
                                'P_Value': row['p-corr'],
                                'Effect_Size': row['cohen-d'] if 'cohen-d' in row else np.nan,
                                'Significance': self.get_significance_label(row['p-corr']),
                                'Details': f'Post-hoc for significant {independent_factor} x {repeated_factor} interaction'
                            })
                            if row['p-corr'] < 0.05:
                                # For plot annotations, pass the tuple that represents the full group
                                significant_comparisons_for_plot.append({
                                    'groups': (
                                    (g1_between_level, g1_within_level), (g1_between_level, g2_within_level)),
                                    'p': row['p-corr'], 'label': self.get_significance_label(row['p-corr'])
                                })

                    else:
                        self.log_to_gui("\n    - No significant interaction. Checking main effects for post-hoc:")
                        # Post-hoc for main effect of independent_factor if significant
                        independent_effect_row = aov_mixed[aov_mixed['Source'] == independent_factor]
                        if not independent_effect_row.empty and independent_effect_row['p-unc'].iloc[0] < 0.05:
                            self.log_to_gui(
                                f"\n    - Significant main effect of {independent_factor}. Performing post-hoc (Tukey HSD):")
                            tukey_results = pairwise_tukeyhsd(endog=df_cleaned[metric],
                                                              groups=df_cleaned[independent_factor], alpha=0.05)
                            self.log_to_gui(str(tukey_results))
                            for row in tukey_results.summary().data[1:]:
                                group1, group2, mean_diff, lower_ci, upper_ci, p_val, reject = row[:7]
                                all_statistical_results.append({
                                    'Metric': metric,
                                    'Test_Type': f'Tukey HSD Post-hoc (Main Effect {independent_factor})',
                                    'Comparison': f"{group1} vs {group2}",
                                    'F_Statistic': np.nan,
                                    'P_Value': p_val,
                                    'Effect_Size': mean_diff,
                                    'Significance': self.get_significance_label(p_val),
                                    'Details': 'Post-hoc for Mixed ANOVA Main Effect'
                                })
                                if p_val < 0.05:
                                    significant_comparisons_for_plot.append({
                                        'groups': (group1, group2), 'p': p_val,
                                        'label': self.get_significance_label(p_val)
                                    })

                        # Post-hoc for main effect of repeated_factor if significant
                        repeated_effect_row = aov_mixed[aov_mixed['Source'] == repeated_factor]
                        if not repeated_effect_row.empty and repeated_effect_row['p-unc'].iloc[0] < 0.05:
                            self.log_to_gui(
                                f"\n    - Significant main effect of {repeated_factor}. Performing pairwise post-hoc (Bonferroni corrected):")
                            posthoc_rm_main = pg.pairwise_tests(data=df_cleaned, dv=metric, within=repeated_factor,
                                                                subject='animal_id', padjust='bonferroni')
                            self.log_to_gui(str(posthoc_rm_main))
                            for _, row in posthoc_rm_main.iterrows():
                                all_statistical_results.append({
                                    'Metric': metric,
                                    'Test_Type': f'Pairwise t-test (Main Effect {repeated_factor}, Bonferroni)',
                                    'Comparison': f"{row['A']} vs {row['B']}",
                                    'F_Statistic': np.nan,
                                    'P_Value': row['p-corr'],
                                    'Effect_Size': row['cohen-d'] if 'cohen-d' in row else np.nan,
                                    'Significance': self.get_significance_label(row['p-corr']),
                                    'Details': 'Post-hoc for Mixed ANOVA Main Effect'
                                })
                                if row['p-corr'] < 0.05:
                                    significant_comparisons_for_plot.append({
                                        'groups': (row['A'], row['B']), 'p': row['p-corr'],
                                        'label': self.get_significance_label(row['p-corr'])
                                    })

                except Exception as e:
                    self.log_to_gui(f"Error performing Mixed ANOVA: {e}")
                    self.log_to_gui(traceback.format_exc())  # Log the full traceback
                    messagebox.showerror("Analysis Error",
                                         "Failed to perform Mixed ANOVA. Check data structure and raw log output for details.")
                    return [], []

            else:  # Two-way independent ANOVA
                self.log_to_gui(f"\n  - Considering Two-way ANOVA for {metric} by {group_var1} and {group_var2}:")

                df_cleaned['__combined_group__'] = df_cleaned[group_var1].astype(str) + '_' + df_cleaned[
                    group_var2].astype(str)
                is_normal_all_groups, normality_str = self.check_normality(df_cleaned, '__combined_group__', metric)
                self.log_to_gui(normality_str)
                is_homogeneous_variance, levene_p, homogeneity_str = self.check_homogeneity_of_variance(df_cleaned,
                                                                                                        '__combined_group__',
                                                                                                        metric)
                self.log_to_gui(homogeneity_str)
                df_cleaned = df_cleaned.drop(columns='__combined_group__')

                run_parametric = is_normal_all_groups and is_homogeneous_variance
                if not run_parametric:
                    self.log_to_gui("\n  - Assumptions not fully met for Parametric Two-Way ANOVA.")
                    user_choice = messagebox.askyesno(
                        "Assumption Violation",
                        "Statistical assumptions (Normality and/or Homogeneity of Variances) were not met.\n"
                        "Do you want to proceed with the parametric Two-Way ANOVA anyway?\n"
                        "Click 'No' to attempt a non-parametric alternative (Rank-transformed ANOVA)."
                    )
                    run_parametric = user_choice
                    if run_parametric:
                        self.log_to_gui(
                            "  - Proceeding with Two-Way ANOVA despite assumption warnings. Interpret results with caution.")
                    else:
                        self.log_to_gui("  - Proceeding with non-parametric alternative as requested.")

                if run_parametric:
                    self.log_to_gui("\n  - Performing Two-way ANOVA (parametric):")
                    formula = f'{metric} ~ C({group_var1}) * C({group_var2})'
                    model = ols(formula, data=df_cleaned).fit()
                    anova_table = sm.stats.anova_lm(model, typ=2)
                    self.log_to_gui(str(anova_table))

                    effects = [group_var1, group_var2, f'{group_var1}:{group_var2}']
                    for effect in effects:
                        effect_col_name = f'C({effect})' if ':' not in effect else f'C({group_var1}):C({group_var2})'
                        if effect_col_name in anova_table.index:
                            p_value = anova_table['PR(>F)'][effect_col_name]
                            partial_eta_sq = self.calculate_partial_eta_squared(anova_table, effect_col_name)

                            all_statistical_results.append({
                                'Metric': metric, 'Test_Type': 'Two-Way ANOVA',
                                'Comparison': effect.replace(':', ' x '),
                                'F_Statistic': anova_table['F'][effect_col_name], 'P_Value': p_value,
                                'Effect_Size': partial_eta_sq, 'Significance': self.get_significance_label(p_value),
                                'Details': f"Homogeneity_of_Variance_p: {levene_p:.3f}"
                            })
                            self.log_to_gui(
                                f"    - Effect of {effect}: F-statistic={anova_table['F'][effect_col_name]:.3f}, p-value={p_value:.3f}, Partial Eta-squared={partial_eta_sq:.3f}")
                            if p_value < 0.05:
                                self.log_to_gui(
                                    f"      -> Statistically significant effect of {effect.replace(':', ' x ')}.")

                    interaction_term_formula = f'C({group_var1}):C({group_var2})'
                    interaction_p = anova_table['PR(>F)'][
                        interaction_term_formula] if interaction_term_formula in anova_table.index else 1.0

                    if interaction_p < 0.05:
                        self.log_to_gui(
                            "\n    - Significant interaction detected. Performing post-hoc comparisons (Tukey HSD) on combined groups:")
                        df_cleaned['combined_group_for_posthoc'] = df_cleaned[group_var1].astype(str) + ' x ' + \
                                                                   df_cleaned[group_var2].astype(str)
                        tukey_results = pairwise_tukeyhsd(endog=df_cleaned[metric],
                                                          groups=df_cleaned['combined_group_for_posthoc'], alpha=0.05)
                        self.log_to_gui(str(tukey_results))
                        for row in tukey_results.summary().data[1:]:
                            group1, group2, mean_diff, lower_ci, upper_ci, p_val, reject = row[:7]
                            all_statistical_results.append({
                                'Metric': metric,
                                'Test_Type': 'Tukey HSD Post-hoc (Interaction)',
                                'Comparison': f"{group1} vs {group2}",
                                'F_Statistic': np.nan,
                                'P_Value': p_val,
                                'Effect_Size': mean_diff,
                                'Significance': self.get_significance_label(p_val),
                                'Details': f"Mean Diff: {mean_diff:.3f}, CI: [{lower_ci:.3f}, {upper_ci:.3f}]"
                            })
                            if p_val < 0.05:
                                significant_comparisons_for_plot.append({
                                    'groups': (group1, group2), 'p': p_val, 'label': self.get_significance_label(p_val)
                                })
                    else:
                        self.log_to_gui("\n    - No significant interaction. Checking main effects for post-hoc:")
                        for g_var in [group_var1, group_var2]:
                            main_effect_p = anova_table['PR(>F)'][f'C({g_var})']
                            if main_effect_p < 0.05:
                                self.log_to_gui(
                                    f"\n    - Significant main effect of {g_var}. Performing post-hoc (Tukey HSD):")
                                tukey_results = pairwise_tukeyhsd(endog=df_cleaned[metric], groups=df_cleaned[g_var],
                                                                  alpha=0.05)
                                self.log_to_gui(str(tukey_results))
                                for row in tukey_results.summary().data[1:]:
                                    group1, group2, mean_diff, lower_ci, upper_ci, p_val, reject = row[:7]
                                    all_statistical_results.append({
                                        'Metric': metric,
                                        'Test_Type': f'Tukey HSD Post-hoc (Main Effect {g_var})',
                                        'Comparison': f"{group1} vs {group2}",
                                        'F_Statistic': np.nan,
                                        'P_Value': p_val,
                                        'Effect_Size': mean_diff,
                                        'Significance': self.get_significance_label(p_val),
                                        'Details': 'Post-hoc for Non-parametric Two-Way ANOVA Main Effect'
                                    })
                                    if p_val < 0.05:
                                        significant_comparisons_for_plot.append({
                                            'groups': (group1, group2), 'p': p_val,
                                            'label': self.get_significance_label(p_val)
                                        })
                else:  # Non-parametric two-way alternative (Rank-transformed ANOVA)
                    self.log_to_gui("\n  - Assumptions not met or parametric test declined for Two-Way ANOVA.")
                    self.log_to_gui("    Proceeding with Non-parametric Two-way ANOVA (Rank-transformed ANOVA).")

                    try:
                        df_cleaned['__ranked_metric__'] = df_cleaned[metric].rank(method='average')
                        formula_ranked = f'__ranked_metric__ ~ C({group_var1}) * C({group_var2})'
                        model_ranked = ols(formula_ranked, data=df_cleaned).fit()
                        anova_table_non_parametric = sm.stats.anova_lm(model_ranked, typ=2)
                        self.log_to_gui(str(anova_table_non_parametric))

                        for effect_name_raw in [group_var1, group_var2, f'{group_var1}:{group_var2}']:
                            effect_name_formula = f'C({effect_name_raw})' if ':' not in effect_name_raw else f'C({group_var1}):C({group_var2})'
                            if effect_name_formula in anova_table_non_parametric.index:
                                p_val = anova_table_non_parametric['PR(>F)'][effect_name_formula]
                                F_stat = anova_table_non_parametric['F'][effect_name_formula]
                                partial_eta_sq = self.calculate_partial_eta_squared(anova_table_non_parametric,
                                                                                    effect_name_formula)

                                all_statistical_results.append({
                                    'Metric': metric, 'Test_Type': 'Non-parametric Two-Way ANOVA (on ranks)',
                                    'Comparison': effect_name_raw.replace(':', ' x '),
                                    'F_Statistic': F_stat, 'P_Value': p_val, 'Effect_Size': partial_eta_sq,
                                    'Significance': self.get_significance_label(p_val),
                                    'Details': 'Non-parametric alternative (Rank-transformed).'
                                })
                                self.log_to_gui(
                                    f"    - Effect of {effect_name_raw.replace(':', ' x ')}: p-value={p_val:.3f}, Partial Eta Squared={partial_eta_sq:.3f}")
                                if p_val < 0.05:
                                    self.log_to_gui(f"      -> Statistically significant effect (non-parametric).")

                        p_val_interaction = anova_table_non_parametric['PR(>F)'][
                            f'C({group_var1}):C({group_var2})'] if f'C({group_var1}):C({group_var2})' in anova_table_non_parametric.index else 1.0

                        if p_val_interaction < 0.05:
                            self.log_to_gui(
                                "\n    - Statistically significant interaction (non-parametric). Performing Simple Effects Analysis (Mann-Whitney U) for significant interaction:")
                            for level_g2 in df_cleaned[group_var2].unique():
                                self.log_to_gui(
                                    f"\n--- Simple Effect of {group_var1} for {group_var2} = {level_g2} ---")
                                subset_df = df_cleaned[df_cleaned[group_var2] == level_g2].copy()
                                unique_g1_in_subset = subset_df[group_var1].unique()

                                if len(unique_g1_in_subset) < 2:
                                    self.log_to_gui(
                                        f"  Not enough unique groups for simple effect analysis for {group_var1} at {group_var2}={level_g2}.")
                                    continue

                                posthoc_simple = pg.pairwise_tests(data=subset_df, dv=metric, between=group_var1,
                                                                   parametric=False, padjust='bonferroni')
                                self.log_to_gui(str(posthoc_simple))

                                for _, row_simple in posthoc_simple.iterrows():
                                    p_value_to_use = row_simple['p-corr'] if 'p-corr' in row_simple else row_simple[
                                        'p-unc']

                                    all_statistical_results.append({
                                        'Metric': metric,
                                        'Test_Type': f'Mann-Whitney U (Simple Effect {group_var1} at {group_var2}={level_g2})',
                                        'Comparison': f"{row_simple['A']} vs {row_simple['B']}",
                                        'F_Statistic': np.nan,
                                        'P_Value': p_value_to_use,
                                        'Effect_Size': row_simple['RBC'] if 'RBC' in row_simple else np.nan,
                                        'Significance': self.get_significance_label(p_value_to_use),
                                        'Details': 'Post-hoc for Non-parametric Two-Way ANOVA Interaction'
                                    })
                                    if p_value_to_use < 0.05:
                                        g1_name = row_simple['A']
                                        g2_name = row_simple['B']
                                        significant_comparisons_for_plot.append({
                                            'groups': ((g1_name, level_g2), (g2_name, level_g2)),
                                            'p': p_value_to_use, 'label': self.get_significance_label(p_value_to_use)
                                        })

                        elif p_val_interaction >= 0.05:
                            self.log_to_gui("\n  - No statistically significant interaction (non-parametric).")
                            for effect_src in [group_var1, group_var2]:
                                effect_name_formula = f'C({effect_src})'
                                p_main_effect = anova_table_non_parametric['PR(>F)'][
                                    effect_name_formula] if effect_name_formula in anova_table_non_parametric.index else np.nan
                                if p_main_effect < 0.05:
                                    self.log_to_gui(
                                        f"\n  - Statistically significant main effect of {effect_src} (non-parametric).")
                                    self.log_to_gui(
                                        f"    Performing post-hoc (Dunn's) for main effect of {effect_src}:")
                                    posthoc_main = pg.pairwise_tests(data=df_cleaned, dv=metric, between=effect_src,
                                                                     parametric=False, padjust='bonferroni')
                                    self.log_to_gui(str(posthoc_main))

                                    for _, row_main in posthoc_main.iterrows():
                                        p_value_to_use = row_main['p-corr'] if 'p-corr' in row_main else row_main[
                                            'p-unc']

                                        all_statistical_results.append({
                                            'Metric': metric,
                                            'Test_Type': f'Dunn\'s Post-hoc (Main Effect {effect_src})',
                                            'Comparison': f"{row_main['A']} vs {row_main['B']}",
                                            'F_Statistic': np.nan,
                                            'P_Value': p_value_to_use,
                                            'Effect_Size': row_main['RBC'] if 'RBC' in row_main else np.nan,
                                            'Significance': self.get_significance_label(p_value_to_use),
                                            'Details': 'Post-hoc for Non-parametric Two-Way ANOVA Main Effect'
                                        })
                                        if p_value_to_use < 0.05:
                                            significant_comparisons_for_plot.append({
                                                'groups': (row_main['A'], row_main['B']),
                                                'p': p_value_to_use,
                                                'label': self.get_significance_label(p_value_to_use)
                                            })
                    except Exception as e:
                        self.log_to_gui(f"Error performing Non-parametric Two-way ANOVA: {e}")
                        self.log_to_gui(traceback.format_exc())  # Log the full traceback for fallback
                        messagebox.showerror("Analysis Error",
                                             "Could not perform non-parametric analysis. Returning no results.")
                        return [], []
                    finally:
                        if '__ranked_metric__' in df_cleaned.columns:
                            df_cleaned = df_cleaned.drop(columns='__ranked_metric__')

        self.log_to_gui("\n--- Statistical Analysis Complete ---")
        return all_statistical_results, significant_comparisons_for_plot

    def calculate_descriptive_statistics(self, df, metric, grouping_vars):
        """
        Calculates and prints descriptive statistics for a given metric,
        grouped by specified variables. Outputs to the GUI's log.
        """
        self.log_to_gui(f"\n--- Descriptive Statistics for '{metric}' ---")

        if not grouping_vars:
            desc_stats = df[metric].describe()
            self.log_to_gui("\nOverall Descriptive Statistics:")
            self.log_to_gui(str(desc_stats))
        else:
            df_display = df.copy()
            if 'Sex' in df_display.columns:
                df_display['Sex'] = df_display['Sex'].replace(self.SEX_LABELS)
            if 'Genotype' in df_display.columns:
                df_display['Genotype'] = df_display['Genotype'].replace(self.GENOTYPE_LABELS)

            # Use original grouping_vars for groupby, then display with labels
            grouped_stats = df_display.groupby(grouping_vars, observed=False)[metric].agg(
                ['count', 'mean', 'std', 'min', 'max', 'median', 'sem']).round(3)
            grouped_stats.rename(columns={'sem': 'standard_error_of_mean'}, inplace=True)
            self.log_to_gui(f"\nDescriptive Statistics by {', '.join(grouping_vars)}:")
            self.log_to_gui(str(grouped_stats))

        self.log_to_gui("\n--- Descriptive Statistics Complete ---")
        return grouped_stats

    def plot_dot_plot_with_mean_sd_reinstated(self, df, metric, primary_grouping, secondary_grouping, output_dir,
                                              sex_labels, genotype_labels, timepoint_order,
                                              significant_comparisons=None):
        """
        Generates a plot with mean and standard deviation, with
        optional secondary grouping and significance annotations.
        Returns the matplotlib Figure object.
        """
        self.log_to_gui(f"Generating plot for {metric} by {primary_grouping}" + (
            f" and {secondary_grouping}" if secondary_grouping else "") + " (Means and SDs Only)...")

        fig, ax = plt.subplots(figsize=(10, 7))
        sns.set_style("whitegrid")

        df_plot = df.copy()

        # Apply readable labels for plotting
        if 'Sex' in df_plot.columns:
            df_plot['Sex'] = df_plot['Sex'].replace(sex_labels)
        if 'Genotype' in df_plot.columns:
            df_plot['Genotype'] = df_plot['Genotype'].replace(genotype_labels)
        if 'Timepoint' in df_plot.columns:
            present_timepoints = [tp for tp in timepoint_order if tp in df_plot['Timepoint'].unique()]
            if present_timepoints:
                df_plot['Timepoint'] = pd.Categorical(df_plot['Timepoint'], categories=present_timepoints, ordered=True)

        # Determine x_axis and hue variables
        x_axis_var = primary_grouping

        pointplot_hue_var = None

        # Color palettes and marker maps
        SEX_COLOR_MAP_PLOT = {'Females': 'pink', 'Males': 'blue'}
        GENOTYPE_COLOR_MAP_PLOT = {'Wild Type': 'green', 'Mutant': 'purple'}

        point_palette_arg = None  # Will be either a dict
        point_hue_order = None  # Will be explicitly set or left for seaborn to infer

        plot_order_x = None
        if x_axis_var == 'Timepoint':
            plot_order_x = timepoint_order
        else:
            plot_order_x = sorted(df_plot[x_axis_var].dropna().unique())

        if secondary_grouping:
            pointplot_hue_var = secondary_grouping

            if secondary_grouping == 'Sex':
                point_palette_dict = {label: SEX_COLOR_MAP_PLOT.get(label, 'gray') for label in
                                      self.SEX_LABELS.values()}
                point_palette_arg = point_palette_dict
                # Ensure hue order matches the palette keys and available data
                point_hue_order = [lbl for lbl in point_palette_dict.keys() if
                                   lbl in df_plot[pointplot_hue_var].dropna().unique()]
            elif secondary_grouping == 'Genotype':
                point_palette_dict = {label: GENOTYPE_COLOR_MAP_PLOT.get(label, 'gray') for label in
                                      self.GENOTYPE_LABELS.values()}
                point_palette_arg = point_palette_dict
                # Ensure hue order matches the palette keys and available data
                point_hue_order = [lbl for lbl in point_palette_dict.keys() if
                                   lbl in df_plot[pointplot_hue_var].dropna().unique()]
            else:
                # For other secondary grouping variables, generate a palette dynamically
                unique_hue_levels = sorted(df_plot[pointplot_hue_var].dropna().unique().tolist())
                if not unique_hue_levels:
                    self.log_to_gui(
                        f"Warning: No valid data for hue variable '{pointplot_hue_var}' to plot. Plotting skipped.")
                    plt.close(fig)  # Close the empty figure
                    return None, None

                    # Generate a default color palette if not Sex/Genotype and create a dictionary
                colors = sns.color_palette("viridis", n_colors=len(unique_hue_levels))
                point_palette_arg = {level: colors[i] for i, level in enumerate(unique_hue_levels)}
                point_hue_order = unique_hue_levels  # Set hue order to all unique levels

            # Display Mean and SD only
            sns.pointplot(x=x_axis_var, y=metric, hue=pointplot_hue_var, data=df_plot,
                          linestyle='none', estimator=np.mean, errorbar='sd', capsize=0.1,
                          # Replaced join=False with linestyle='none'
                          palette=point_palette_arg, dodge=0.6, ax=ax, markers='D',
                          # Diamond marker for mean, explicit dodge width
                          order=plot_order_x, hue_order=point_hue_order)

            # --- Calculate x_group_positions for significance bars ---
            x_group_positions = {}

            num_x_categories = len(plot_order_x)
            num_hue_categories = len(point_hue_order)

            # Match the dodge width used in sns.pointplot
            explicit_dodge_width = 0.6
            if num_hue_categories > 1:
                point_width_in_dodge = explicit_dodge_width / num_hue_categories
                # The first point for an x-category is offset from the center of the x-tick
                start_offset = -(explicit_dodge_width / 2) + (point_width_in_dodge / 2)
            else:
                point_width_in_dodge = 0
                start_offset = 0

            for i, x_cat in enumerate(plot_order_x):
                for j, hue_cat in enumerate(point_hue_order):
                    actual_x_pos = i + start_offset + j * point_width_in_dodge
                    x_group_positions[(x_cat, hue_cat)] = actual_x_pos

            # Create a combined legend for means (diamond)
            handles = []
            labels = []
            for hue_val in point_hue_order:
                label = f"{hue_val}"
                handles.append(plt.Line2D([0], [0], marker='D',  # Diamond marker for mean
                                          color='w', markerfacecolor=point_palette_arg.get(hue_val, 'gray'),
                                          markeredgecolor='k', markersize=10, linestyle='None'))
                labels.append(label)

            ax.legend(handles, labels, title=pointplot_hue_var, bbox_to_anchor=(1.05, 1), loc='upper left')

        else:  # Only one grouping variable
            sns.pointplot(x=x_axis_var, y=metric, data=df_plot,
                          linestyle='none', estimator=np.mean, errorbar='sd', capsize=0.1,
                          # Replaced join=False with linestyle='none'
                          color='black', ax=ax, markers='D',  # Diamond marker for mean
                          order=plot_order_x)

            # For single grouping variable, x_coords for significance bars are simply 0, 1, 2...
            x_group_positions = {val: i for i, val in enumerate(plot_order_x)}

            # Add legend for single variable case: mean
            handles = [
                plt.Line2D([0], [0], marker='D', color='w', markerfacecolor='black', markeredgecolor='black',
                           markersize=10, linestyle='None', label='Mean ± SD')
            ]
            ax.legend(handles=handles, title="Legend", bbox_to_anchor=(1.05, 1), loc='upper left')

        plt.title(f'{metric} by {primary_grouping}' + (f' and {secondary_grouping}' if secondary_grouping else ''))
        plt.ylabel(metric)
        plt.xlabel(primary_grouping)
        plt.tight_layout(rect=[0, 0, 0.85, 1])  # Adjust layout to make space for legend

        # Add significance annotations
        if significant_comparisons:
            # Recalculate y_max_overall based on means + SDs visible in the plot, not just raw data points
            y_vals_upper_sd = []
            if secondary_grouping:
                for x_cat in plot_order_x:
                    for hue_cat in point_hue_order:
                        subset = df_plot[(df_plot[x_axis_var] == x_cat) & (df_plot[pointplot_hue_var] == hue_cat)]
                        if not subset.empty:
                            mean_val = subset[metric].mean()
                            std_val = subset[metric].std()
                            if pd.notna(mean_val) and pd.notna(std_val):
                                y_vals_upper_sd.append(mean_val + std_val)
            else:
                for x_cat in plot_order_x:
                    subset = df_plot[df_plot[x_axis_var] == x_cat]
                    if not subset.empty:
                        mean_val = subset[metric].mean()
                        std_val = subset[metric].std()
                        if pd.notna(mean_val) and pd.notna(std_val):
                            y_vals_upper_sd.append(mean_val + std_val)

            if y_vals_upper_sd:
                y_max_overall_plot = max(y_vals_upper_sd)
            else:
                y_max_overall_plot = df_plot[metric].max() if not df_plot.empty else 1  # Fallback if no data

            y_min_overall = df_plot[metric].min() if not df_plot.empty else 0
            y_range_overall = y_max_overall_plot - y_min_overall
            if y_range_overall == 0: y_range_overall = y_max_overall_plot * 0.2 if y_max_overall_plot != 0 else 1  # Avoid division by zero

            # Start position for significance bars
            y_pos_start = y_max_overall_plot + y_range_overall * 0.1

            # Store the current y-position to avoid overlaps
            current_y_pos = y_pos_start

            # Filter and sort comparisons to prevent overlap
            filtered_comparisons = []
            for comp in significant_comparisons:
                g1, g2 = comp['groups']

                formatted_g1 = g1
                formatted_g2 = g2

                if formatted_g1 in x_group_positions and formatted_g2 in x_group_positions:
                    filtered_comparisons.append(
                        {'groups': (formatted_g1, formatted_g2), 'p': comp['p'], 'label': comp['label']})
                else:
                    self.log_to_gui(
                        f"Warning: Comparison groups {g1} and {g2} (formatted as {formatted_g1} and {formatted_g2}) not found in plot positions. Skipping annotation.")

            filtered_comparisons.sort(
                key=lambda c: abs(x_group_positions[c['groups'][0]] - x_group_positions[c['groups'][1]]))

            for i, comp in enumerate(filtered_comparisons):
                g1_key, g2_key = comp['groups']
                p_label = comp['label']

                x1 = x_group_positions[g1_key]
                x2 = x_group_positions[g2_key]


                if secondary_grouping:
                    group1_primary_level = g1_key[0]
                    group1_secondary_level = g1_key[1]
                    group2_primary_level = g2_key[0]
                    group2_secondary_level = g2_key[1]


                    subset_g1 = df_plot[(df_plot[primary_grouping] == group1_primary_level) &
                                        (df_plot[secondary_grouping] == group1_secondary_level)]
                    subset_g2 = df_plot[(df_plot[primary_grouping] == group2_primary_level) &
                                        (df_plot[secondary_grouping] == group2_secondary_level)]

                    mean_g1 = subset_g1[metric].mean() if not subset_g1.empty else np.nan
                    std_g1 = subset_g1[metric].std() if not subset_g1.empty else np.nan
                    mean_g2 = subset_g2[metric].mean() if not subset_g2.empty else np.nan
                    std_g2 = subset_g2[metric].std() if not subset_g2.empty else np.nan

                    y_val1 = mean_g1 + std_g1 if pd.notna(mean_g1) and pd.notna(std_g1) else y_max_overall_plot
                    y_val2 = mean_g2 + std_g2 if pd.notna(mean_g2) and pd.notna(std_g2) else y_max_overall_plot

                else:  # Only primary grouping
                    subset_g1 = df_plot[df_plot[primary_grouping] == g1_key]
                    subset_g2 = df_plot[df_plot[primary_grouping] == g2_key]

                    mean_g1 = subset_g1[metric].mean() if not subset_g1.empty else np.nan
                    std_g1 = subset_g1[metric].std() if not subset_g1.empty else np.nan
                    mean_g2 = subset_g2[metric].mean() if not subset_g2.empty else np.nan
                    std_g2 = subset_g2[metric].std() if not subset_g2.empty else np.nan

                    y_val1 = mean_g1 + std_g1 if pd.notna(mean_g1) and pd.notna(std_g1) else y_max_overall_plot
                    y_val2 = mean_g2 + std_g2 if pd.notna(mean_g2) and pd.notna(std_g2) else y_max_overall_plot

                # Ensure y_val1 and y_val2 are finite numbers for comparison
                y_val1 = y_val1 if np.isfinite(y_val1) else y_max_overall_plot
                y_val2 = y_val2 if np.isfinite(y_val2) else y_max_overall_plot

                potential_bar_level = max(y_val1, y_val2) + y_range_overall * 0.05  # Initial buffer above the points

                # Ensure current_y_pos is always at least the potential bar level
                current_y_pos = max(current_y_pos + y_range_overall * 0.03, potential_bar_level)

                # Draw the bar
                ax.plot([x1, x1, x2, x2],
                        [current_y_pos, current_y_pos + y_range_overall * 0.01, current_y_pos + y_range_overall * 0.01,
                         current_y_pos],
                        lw=1.5, c='k')
                # Add the text label
                ax.text((x1 + x2) / 2, current_y_pos + y_range_overall * 0.01 + y_range_overall * 0.005, p_label,
                        ha='center', va='bottom', color='k', fontsize=10)

            # Adjust y-limit to ensure significance bars are visible
            # Maximize y-limit based on the highest `current_y_pos` used
            ax.set_ylim(top=current_y_pos + y_range_overall * 0.05)
            # Add autoscale to ensure all elements fit
            ax.autoscale_view()

        plt.tight_layout(rect=[0, 0, 0.85, 1])  # Re-adjust layout after adding sig bars

        # Save plot and return Figure object
        file_name = f'{metric}_by_{primary_grouping}'
        if secondary_grouping:
            file_name += f'_{secondary_grouping}'
        file_name = file_name.replace(' ', '_').replace('/',
                                                        '_') + '_mean_sd_plot.png'  # Changed filename to reflect plot type

        plot_path = os.path.join(output_dir, file_name)
        fig.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close(fig)  # Close the figure to free memory
        return fig, plot_path  # Return both the figure and its save path

    # --- Run Analysis Method ---
    def run_analysis(self):
        if self.df_aggregated is None:
            messagebox.showerror("Error", "Please load data first.")
            return

        selected_metric = self.metric_combobox.get()
        primary_grouping = self.primary_group_combobox.get()
        secondary_grouping = self.secondary_group_combobox.get()

        if not selected_metric or not primary_grouping:
            messagebox.showerror("Input Error", "Please select a Metric and a Primary Grouping Variable.")
            return

        if self.secondary_group_enabled_var.get() and not secondary_grouping:
            messagebox.showwarning("Input Error", "Please select a Secondary Grouping Variable or uncheck the option.")
            return

        if not self.secondary_group_enabled_var.get():
            secondary_grouping = None  # Ensure it's None if checkbox is unchecked

        if secondary_grouping and primary_grouping == secondary_grouping:
            messagebox.showerror("Input Error", "Primary and Secondary grouping variables cannot be the same.")
            return

        self.clear_output()
        self.log_to_gui(f"Starting analysis for Metric: {selected_metric}, Primary Group: {primary_grouping}" +
                        (f", Secondary Group: {secondary_grouping}" if secondary_grouping else ""))

        # Redirect print statements to the GUI's text widget
        old_stdout = sys.stdout
        sys.stdout = TextRedirector(self.raw_log_output_text)  # Directs prints to raw log output

        # Ensure the statistical output tab is always enabled for logging
        self.notebook.tab(self.statistical_output_frame, state='normal')

        try:
            # 1. Calculate Descriptive Statistics
            grouping_for_desc_stats = [primary_grouping]
            if secondary_grouping:
                grouping_for_desc_stats.append(secondary_grouping)

            descriptive_stats_df = self.calculate_descriptive_statistics(self.df_aggregated, selected_metric,
                                                                         grouping_for_desc_stats)
            self._current_descriptive_stats_df = descriptive_stats_df  # Store for potential saving and display
            self.populate_descriptive_stats_table(descriptive_stats_df)  # Populate the new descriptive stats table

            # 2. Perform Statistical Analysis
            statistical_results_list, significant_comparisons = self.perform_statistical_analysis(
                self.df_aggregated, selected_metric, primary_grouping, secondary_grouping
            )

            # 3. Generate Plot
            # Only attempt to generate plot if analysis was successful or didn't explicitly fail
            plot_fig, plot_path = None, None
            try:
                plot_fig, plot_path = self.plot_dot_plot_with_mean_sd_reinstated(
                    self.df_aggregated, selected_metric, primary_grouping, secondary_grouping,
                    self.plot_output_dir, self.SEX_LABELS, self.GENOTYPE_LABELS,
                    self.TIMEPOINT_ORDER, significant_comparisons
                )
            except Exception as plot_e:
                self.log_to_gui(f"\nAn error occurred during plot generation: {plot_e}")
                self.log_to_gui(traceback.format_exc())
                messagebox.showwarning("Plotting Error",
                                       f"Failed to generate plot: {plot_e}\nCheck 'Statistical Output' tab for details.")

            self.last_generated_plot_path = plot_path

            if plot_fig and plot_path:
                # Display plot in GUI
                self.display_plot(plot_fig)
                self.log_to_gui(f"\nPlot saved to: {plot_path}")
                self.notebook.tab(self.graphic_frame, state='normal')
            else:
                self.log_to_gui("\nPlot generation skipped due to previous errors or no valid data.")
                self.notebook.tab(self.graphic_frame, state='disabled')  # Keep plot tab disabled if no plot

            # Display statistical results in GUI (Treeview)
            if statistical_results_list:
                results_df = pd.DataFrame(statistical_results_list)
                self.populate_results_table(results_df)
                self._current_statistical_results_df = results_df  # Store for potential saving
                # Save statistical results to CSV
                output_file = os.path.join(self.analysis_results_dir, f'statistical_results_{selected_metric}.csv')
                results_df.to_csv(output_file, index=False)
                self.log_to_gui(f"\n--- Statistical results saved to '{output_file}' ---")
            else:
                self.log_to_gui("\nNo statistical results to display or save.")
                self.clear_results_table()

            self.update_status("Analysis complete!")
            # Switch to Statistical Output tab by default if analysis completed (even with plot errors)
            self.notebook.select(self.statistical_output_frame)

        except Exception as e:
            self.log_to_gui(f"\nAn unexpected error occurred during analysis: {e}")
            self.log_to_gui(traceback.format_exc())  # Log the full traceback
            messagebox.showerror("Analysis Error",
                                 f"An error occurred during analysis: {e}\nCheck the 'Statistical Output' tab for details.")
            self.notebook.select(self.statistical_output_frame)  # Switch to statistical output tab on error
        finally:
            sys.stdout = old_stdout  # Restore stdout

    # --- New Tab: Statistical Output ---
    def create_statistical_output_tab(self):
        self.statistical_output_frame = ttk.Frame(self.notebook, padding="10 10 10 10")
        self.notebook.add(self.statistical_output_frame, text="4. Statistical Output")

        # Configure grid for this tab
        self.statistical_output_frame.grid_rowconfigure(0, weight=1)  # Inferential table
        self.statistical_output_frame.grid_rowconfigure(1, weight=0)  # Separator
        self.statistical_output_frame.grid_rowconfigure(2, weight=1)  # Descriptive table
        self.statistical_output_frame.grid_rowconfigure(3,
                                                        weight=0)  # Raw log output (this is still here for console prints)
        self.statistical_output_frame.grid_rowconfigure(4, weight=0)  # Buttons
        self.statistical_output_frame.grid_columnconfigure(0, weight=1)  # Single column

        # Inferential Statistical Results Table
        self.results_table_frame = ttk.LabelFrame(self.statistical_output_frame, text="Inferential Statistical Results")
        self.results_table_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.results_table = ttk.Treeview(self.results_table_frame, show="headings")
        self.results_table.pack(side="left", fill="both", expand=True)
        self.results_table_scroll_y = ttk.Scrollbar(self.results_table_frame, orient="vertical",
                                                    command=self.results_table.yview)
        self.results_table_scroll_y.pack(side="right", fill="y")
        self.results_table.config(yscrollcommand=self.results_table_scroll_y.set)

        # Separator between Inferential and Descriptive Tables
        ttk.Separator(self.statistical_output_frame, orient='horizontal').grid(row=1, column=0, sticky='ew', padx=5,
                                                                               pady=(20, 15))

        # Descriptive Statistics Table
        self.descriptive_stats_frame = ttk.LabelFrame(self.statistical_output_frame, text="Descriptive Statistics")
        self.descriptive_stats_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        self.descriptive_stats_table = ttk.Treeview(self.descriptive_stats_frame, show="headings")
        self.descriptive_stats_table.pack(side="left", fill="both", expand=True)
        self.descriptive_stats_scroll_y = ttk.Scrollbar(self.descriptive_stats_frame, orient="vertical",
                                                        command=self.descriptive_stats_table.yview)
        self.descriptive_stats_scroll_y.pack(side="right", fill="y")
        self.descriptive_stats_table.config(yscrollcommand=self.descriptive_stats_scroll_y.set)

        # Raw Log Output (for general messages - still here for consistency with console output)
        self.raw_log_output_frame = ttk.LabelFrame(self.statistical_output_frame, text="Raw Log Output")
        self.raw_log_output_frame.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)
        self.raw_log_output_text = tk.Text(self.raw_log_output_frame, wrap="word", height=8, state='disabled')
        self.raw_log_output_text.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self.raw_log_output_scroll = ttk.Scrollbar(self.raw_log_output_frame, command=self.raw_log_output_text.yview)
        self.raw_log_output_scroll.pack(side="right", fill="y")
        self.raw_log_output_text.config(yscrollcommand=self.raw_log_output_scroll.set)

        # Buttons specific to statistical output
        self.statistical_buttons_frame = ttk.Frame(self.statistical_output_frame)
        self.statistical_buttons_frame.grid(row=4, column=0, sticky="ew", padx=5, pady=5)
        self.statistical_buttons_frame.columnconfigure(0, weight=1)  # Spacer
        self.statistical_buttons_frame.columnconfigure(1, weight=0)  # Back
        self.statistical_buttons_frame.columnconfigure(2, weight=0)  # Save Tables

        ttk.Button(self.statistical_buttons_frame, text="Back to Analysis",
                   command=lambda: self.notebook.select(self.analysis_frame)).grid(
            row=0, column=1, padx=5, pady=5, sticky="e"
        )
        ttk.Button(self.statistical_buttons_frame, text="Save Results Table", command=self.save_results_table).grid(
            row=0, column=2, padx=5, pady=5, sticky="e"
        )

    # --- Tab: Graphic ---
    def create_graphic_tab(self):
        self.graphic_frame = ttk.Frame(self.notebook, padding="10 10 10 10")
        self.notebook.add(self.graphic_frame, text="5. Graphic")

        # Configure grid for this tab
        self.graphic_frame.grid_rowconfigure(0, weight=1)  # Plot area
        self.graphic_frame.grid_rowconfigure(1, weight=0)  # Buttons
        self.graphic_frame.grid_columnconfigure(0, weight=1)  # Single column

        # Plot Display Area
        self.plot_canvas_frame = ttk.LabelFrame(self.graphic_frame, text="Generated Plot")
        self.plot_canvas_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.plot_canvas = None
        self.plot_toolbar = None

        # Buttons specific to graphic
        self.graphic_buttons_frame = ttk.Frame(self.graphic_frame)
        self.graphic_buttons_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        self.graphic_buttons_frame.columnconfigure(0, weight=1)  # Spacer
        self.graphic_buttons_frame.columnconfigure(1, weight=0)  # Back
        self.graphic_buttons_frame.columnconfigure(2, weight=0)  # Open Plot Folder
        self.graphic_buttons_frame.columnconfigure(3, weight=0)  # Save Plot

        ttk.Button(self.graphic_buttons_frame, text="Back to Analysis",
                   command=lambda: self.notebook.select(self.analysis_frame)).grid(
            row=0, column=1, padx=5, pady=5, sticky="e"
        )
        ttk.Button(self.graphic_buttons_frame, text="Open Plots Folder", command=self.open_plot_folder).grid(
            row=0, column=2, padx=5, pady=5, sticky="e"
        )
        ttk.Button(self.graphic_buttons_frame, text="Save Plot", command=self.save_current_plot).grid(
            row=0, column=3, padx=5, pady=5, sticky="e"
        )

    def display_plot(self, fig):
        """Displays a Matplotlib figure in the GUI."""
        # Clear previous plot if exists
        for widget in self.plot_canvas_frame.winfo_children():
            widget.destroy()

        self.plot_canvas = FigureCanvasTkAgg(fig, master=self.plot_canvas_frame)
        self.plot_canvas.draw()
        self.plot_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Add Matplotlib toolbar
        self.plot_toolbar = NavigationToolbar2Tk(self.plot_canvas, self.plot_canvas_frame)
        self.plot_toolbar.update()
        self.plot_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def populate_results_table(self, df_results):
        """Populates the Treeview widget with statistical results."""
        # Clear existing table
        self.clear_results_table()

        # Define columns for the inferential table
        # Ensure 'F_Statistic' is included, even if NaN for non-ANOVA tests
        required_cols = ['Metric', 'Test_Type', 'Comparison', 'F_Statistic', 'P_Value', 'Effect_Size', 'Significance',
                         'Details']
        for col in required_cols:
            if col not in df_results.columns:
                df_results[col] = np.nan  # Add missing columns with NaN

        # Reorder columns to ensure F_Statistic is in a consistent place
        df_results = df_results[required_cols]

        self.results_table["columns"] = list(df_results.columns)
        for col in df_results.columns:
            self.results_table.heading(col, text=col.replace('_', ' '),
                                       anchor=tk.CENTER)  # Make column headers more readable
            # Adjust column width based on content or a sensible default
            self.results_table.column(col, anchor=tk.CENTER, width=max(100, len(col) * 10))

            # Add data rows
        for index, row in df_results.iterrows():
            # Format numerical values for display
            display_values = []
            for col_name, value in row.items():
                if col_name in ['F_Statistic', 'P_Value', 'Effect_Size'] and pd.isna(value):
                    display_values.append('')  # Display NaN as empty string
                elif isinstance(value, (float, np.float32, np.float64)):
                    display_values.append(f"{value:.3f}")
                else:
                    display_values.append(value)
            self.results_table.insert("", "end", values=display_values)

    def clear_results_table(self):
        """Clears all data from the inferential results table."""
        for item in self.results_table.get_children():
            self.results_table.delete(item)
        self.results_table["columns"] = ()  # Clear column definitions

    def populate_descriptive_stats_table(self, df_descriptive_stats):
        """Populates the new Treeview widget with descriptive statistics."""
        # Clear existing table
        self.clear_descriptive_stats_table()

        # Add index as a column if it has a name (e.g., grouping variables)
        if df_descriptive_stats.index.name:
            columns = [df_descriptive_stats.index.name] + list(df_descriptive_stats.columns)
            # Reset index to make it a regular column
            df_display = df_descriptive_stats.reset_index()
        else:
            columns = list(df_descriptive_stats.columns)
            df_display = df_descriptive_stats

        self.descriptive_stats_table["columns"] = columns
        for col in columns:
            self.descriptive_stats_table.heading(col, text=col.replace('_', ' '),
                                                 anchor=tk.CENTER)  # Make column headers readable
            self.descriptive_stats_table.column(col, anchor=tk.CENTER, width=max(100, len(col) * 10))

        # Add data rows
        for index, row in df_display.iterrows():
            self.descriptive_stats_table.insert("", "end", values=list(row))

    def clear_descriptive_stats_table(self):
        """Clears all data from the descriptive statistics table."""
        for item in self.descriptive_stats_table.get_children():
            self.descriptive_stats_table.delete(item)
        self.descriptive_stats_table["columns"] = ()  # Clear column definitions

    def log_to_gui(self, message):
        """Inserts a message into the raw log output area."""
        # raw_log_output_text is now in the statistical_output_frame
        self.raw_log_output_text.config(state='normal')
        self.raw_log_output_text.insert(tk.END, message + "\n")
        self.raw_log_output_text.see(tk.END)
        self.raw_log_output_text.config(state='disabled')

    def clear_output(self):
        """Clears all output areas in the new result tabs."""
        # Clear raw log output
        self.raw_log_output_text.config(state='normal')
        self.raw_log_output_text.delete(1.0, tk.END)
        self.raw_log_output_text.config(state='disabled')

        # Clear tables
        self.clear_results_table()
        self.clear_descriptive_stats_table()

        # Clear plot area
        for widget in self.plot_canvas_frame.winfo_children():
            widget.destroy()
        self.plot_canvas = None
        self.plot_toolbar = None

    def open_plot_folder(self):
        """Opens the directory where plots are saved."""
        if os.path.exists(self.plot_output_dir):
            webbrowser.open(os.path.realpath(self.plot_output_dir))
        else:
            messagebox.showinfo("Folder Not Found",
                                f"The plots output directory does not exist: {self.plot_output_dir}")

    def save_current_plot(self):
        """Saves the currently displayed plot."""
        if self.last_generated_plot_path:
            initial_dir = os.path.dirname(self.last_generated_plot_path)
            initial_file = os.path.basename(self.last_generated_plot_path)
        else:
            initial_dir = self.plot_output_dir
            initial_file = "analysis_plot.png"

        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("PDF files", "*.pdf")],
            initialdir=initial_dir,
            initialfile=initial_file
        )
        if file_path:
            try:
                import shutil
                shutil.copy(self.last_generated_plot_path, file_path)
                messagebox.showinfo("Save Plot", f"Plot saved successfully to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save plot: {e}")
        else:
            messagebox.showinfo("Save Plot", "Save operation cancelled.")

    def save_results_table(self):
        """Saves the statistical results table (inferential or descriptive based on current display).
           Prompts user to choose which table to save if both are populated."""

        has_inferential_results = hasattr(self,
                                          '_current_statistical_results_df') and not self._current_statistical_results_df.empty
        has_descriptive_results = hasattr(self,
                                          '_current_descriptive_stats_df') and not self._current_descriptive_stats_df.empty

        df_to_save = None
        default_filename = "analysis_results.csv"

        if has_inferential_results and has_descriptive_results:
            # Ask user which table to save
            choice = messagebox.askyesnocancel(
                "Save Results",
                "Do you want to save Inferential Statistical Results?\n"
                "Click 'No' to save Descriptive Statistics instead.\n"
                "Click 'Cancel' to abort."
            )
            if choice is True:  # User wants Inferential
                df_to_save = self._current_statistical_results_df
                default_filename = "inferential_statistical_results.csv"
            elif choice is False:  # User wants Descriptive
                df_to_save = self._current_descriptive_stats_df
                default_filename = "descriptive_statistics.csv"
            else:  
                messagebox.showinfo("Save Table", "Save operation cancelled.")
                return
        elif has_inferential_results:
            df_to_save = self._current_statistical_results_df
            default_filename = "inferential_statistical_results.csv"
        elif has_descriptive_results:
            df_to_save = self._current_descriptive_stats_df
            default_filename = "descriptive_statistics.csv"
        else:
            messagebox.showwarning("No Data", "No statistical results or descriptive statistics to save in any table.")
            return

        if df_to_save is not None:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")],
                initialdir=self.analysis_results_dir,
                initialfile=default_filename
            )
            if file_path:
                try:
                    if file_path.endswith('.csv'):
                        df_to_save.to_csv(file_path, index=False)
                    elif file_path.endswith('.xlsx'):
                        df_to_save.to_excel(file_path, index=False)
                    messagebox.showinfo("Save Table", f"Results table saved successfully to:\n{file_path}")
                except Exception as e:
                    messagebox.showerror("Save Error", f"Failed to save results table: {e}")
            else:
                messagebox.showinfo("Save Table", "Save operation cancelled.")


# --- Main execution ---
if __name__ == "__main__":
    root = tk.Tk()
    app = USVAnalyzerApp(root)
    root.mainloop()
