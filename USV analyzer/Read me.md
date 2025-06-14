# 📊 USV Data Analysis and Visualization

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20MacOS%20%7C%20Linux-lightgrey)]()

A user-friendly desktop application for advanced statistical analysis and visualization of Ultrasonic Vocalization (USV) data. Designed for preclinical researchers working with USV metrics across various experimental conditions such as sex, genotype, and developmental timepoints.

---

## ✨ Key Features

- **Flexible Data Loading**  
  Load aggregated USV data with a simple folder selection (supports `animal_metadata.csv` and multiple USV `.csv` files).

- **Automated Data Merging**  
  Integrates metadata and USV data into a single dataset for seamless analysis.

- **Descriptive Statistics**  
  Compute count, mean, standard deviation, min, max, median, and standard error, grouped by experimental factors.

- **Inferential Statistics**  
  Supports a wide range of statistical tests:
  - One-Way ANOVA / Kruskal-Wallis
  - Independent t-test / Mann-Whitney U
  - Repeated Measures ANOVA / Friedman Test
  - Two-Way ANOVA / Rank-transformed ANOVA
  - Mixed ANOVA

- **Post-hoc Testing**  
  Automatically performs Tukey HSD, Bonferroni-corrected t-tests, Dunn's test, and Wilcoxon signed-rank tests where applicable.

- **Assumption Checks**  
  Includes normality (Shapiro-Wilk) and homogeneity of variance (Levene’s test) checks with user control over analysis paths.

- **Interactive Visualization**  
  High-quality plots with significance annotations, interactive zoom/pan, and export capabilities.

- **Results Export**  
  Export statistical results, descriptive statistics, and plots for reporting and publication.

- **Clean and Intuitive GUI**  
  Simple multi-tabbed interface built with Tkinter to guide the entire analysis workflow.

---

## 📷 Screenshots

Main Interface


---

## 🚀 Installation

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/JoaoRNeves/Python_projects.git
cd "Python_projects/USV analyzer"
```


2️⃣ (Optional but recommended) Create Virtual Environment
```
python3 -m venv venv

# Activate on Unix/macOS
source venv/bin/activate

# Activate on Windows
venv\Scripts\activate
```

3️⃣ Install Dependencies
```
pip install pandas numpy scipy statsmodels matplotlib seaborn pingouin
```

4️⃣ Prepare Your Data


See next section

5️⃣ Run the Application
```
python "Code.py"
```
___
## 📂 Data Preparation

Before running the application, ensure your data is organized in the following structure:

### 🔖 Folder Structure
```
your-data-folder/
│
├── animal_metadata.csv
├── A01_P4_USVs.csv
├── A01_P6_USVs.csv
├── A02_P4_USVs.csv
├── A02_P6_USVs.csv
├── A03_P4_USVs.csv
├── A03_P6_USVs.csv
└── ...
```
All files should be located inside a single folder.

The filenames of individual USV files must match exactly the values listed in the Filename column of animal_metadata.csv.

### 🗂️ Metadata File: animal_metadata.csv
```
animal_id	Sex	Genotype	Timepoint	Filename
A01	M	WT	P4	A01_P4_USVs.csv
A01	M	WT	P6	A01_P6_USVs.csv
A02	M	WT	P4	A02_P4_USVs.csv
A02	M	WT	P6	A02_P6_USVs.csv
A03	M	MUT	P4	A03_P4_USVs.csv
...	...	...	...	...
```
animal_id: unique animal identifier.

Sex: biological sex (e.g. M, F).

Genotype: genotype group (WT, MUT, etc.).

Timepoint: developmental stage (P4, P6, etc.).

Filename: exact filename of the corresponding USV file.

### 🐭 USV Files: {animal_id}_{Timepoint}_USVs.csv
These files are directly exported from DeepSqueak and contain call-by-call ultrasonic vocalization data.
```
ID	Label	Accepted	Score	Begin Time (s)	End Time (s)	Call Length (s)	Principal Frequency (kHz)	Low Freq (kHz)	High Freq (kHz)	Delta Freq (kHz)	Frequency Standard Deviation (kHz)	Slope (kHz/s)	Sinuosity	Mean Power (dB/Hz)	Tonality	Peak Freq (kHz)
1	Downward	TRUE	0.79	0.236	0.275	0.039	72.16	63.99	75.22	11.22	2.87	-207.46	1.39	-92.48	0.60	69.10
...	...	...	...	...	...	...	...	...	...	...	...	...	...	...	...	...
```
### ⚠ Important Notes:
Column names must match exactly (case-sensitive).

Avoid missing values in critical fields like Call Length (s) or Peak Freq (kHz) to prevent errors during processing.

The application automatically reads and merges metadata with these files using the Filename field.

---
## 🖱️ Quick Usage Guide

1. Launch Code_data visualization.py.
2. Use Data Input tab to select your dataset folder.
3. Review merged data in Data Report.
4. Select metrics and grouping variables in Analysis Options.
5. View results under Statistical Output.
6. Visualize data in Graphic tab, interact with plots, and export results.

---

## 🧰 Tech Stack
- Python 3.9+
- Tkinter - GUI
- Pandas - data manipulation
- NumPy - numerical calculations
- SciPy - core statistics
- Statsmodels - ANOVA & linear models
- Seaborn & Matplotlib - plotting
- Pingouin - advanced stats (e.g., mixed ANOVA, sphericity)

---
## ⚠ Limitations

While the USV Data Analyzer provides a robust framework for analyzing ultrasonic vocalization data, there are some current limitations to keep in mind:

### 🔧 Fixed Variable Names
The code assumes fixed column names in the metadata file for key experimental factors:

`Sex` `Genotype` `Timepoint`

Any deviations from these column names will require manual adjustment of the source code.

### 🔠 Predefined Factor Labels
Certain categorical values are hardcoded:

`SEX_LABELS = ['F', 'M']` `GENOTYPE_LABELS = ['WT', 'MUT']` `TIMEPOINT_ORDER = ['P4', 'P6']`

If your dataset includes additional groups or uses different labels (e.g., P2 or alternative genotype codes), you must update these lists in the code manually.

### 📊 Assumed Data Structure
The tool expects:
- A animal_metadata.csv file with the columns: animal_id, Sex, Genotype, Timepoint, Filename.
- Individual USV files exported directly from DeepSqueak, containing specific numeric columns.
  
Any mismatch in column names, missing columns, or alternative structures will likely result in errors during data loading or processing.

### 📂 Hardcoded File Paths
File paths such as:
- aggregated_data_path
- plot_output_dir
- analysis_results_dir


These are defined relative to the main script directory. Users wishing to use different directories must edit these paths manually in the code.

### 📉 Specific Statistical Tests
The current version includes a predefined set of statistical analyses:
- ANOVA (One-Way, Two-Way, Mixed)
- Kruskal-Wallis
- Mann-Whitney U
- Tukey HSD
- Bonferroni-corrected pairwise t-tests
- Dunn's test
- Wilcoxon signed-rank tests


Additional or alternative statistical methods are not yet implemented and would require extending the codebase.

### 📄 Limited Input Format
- The application only accepts data in CSV format (.csv).
- Other data formats (e.g. Excel, SPSS, HDF5) are not supported without custom parsing modifications.
  
### 🖥 No GUI for Configuration
- Although the analysis workflow features a graphical interface for data loading and running analyses, configuration elements (e.g. factor labels, file paths, additional metrics) still require manual code editing.
- There is currently no GUI for advanced configuration or for adapting the code to new datasets automatically.
___

## 📄 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgements
- Developed by João R. Neves.
- Built with the support of AI-powered tools for debugging and GUI building.
- Special thanks to the open-source community for pandas, numpy, scipy, statsmodels, seaborn, matplotlib, and pingouin.

---

## 💡 Contributions

Suggestions, feature requests, or pull requests are welcome! Feel free to open an issue or contact me directly.
