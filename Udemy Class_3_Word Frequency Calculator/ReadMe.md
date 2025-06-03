# 📝 Word Frequency Counter

A simple desktop application to analyze and visualize the most frequent words in text documents. Supports .txt, .docx, and .pdf files. Built using Python and Tkinter with no external dependencies (except python-docx and PyPDF2).

---

## Features

- Upload .txt, .docx, or .pdf files
- Alternatively, paste text manually into the interface
- Automatically displays the top 10 most frequent words
- Export results to a .txt file
- Clean, scrollable interface using Tkinter widgets

---

## Preview
\<img width="507" alt="Image" src="https://github.com/user-attachments/assets/7fe1e7df-1794-47d7-8536-ff3bb3c521c3" />

<img width="506" alt="Image" src="https://github.com/user-attachments/assets/779930c9-1537-462e-84ab-8343bce1c07b" />

---

## Installation

Clone the repository
```
git clone https://github.com/JoaoRNeves/Python_projects.git
cd "Python_projects/Udemy Class_3_Word Frequency Calculator"
```
(Optional) Create a virtual environment
```
python3 -m venv venv
source venv/bin/activate     # On Windows: venv\Scripts\activate
```
Install dependencies
```
pip install python-docx PyPDF2
```
Run the application
```
python Code.py
```

---

## Usage

1. Open the app.
2. Either:
   
    * Click Choose File and load a .txt, .docx, or .pdf file
* Or:
    * Paste custom text directly into the input box
4. Click Count Words
5. View the top 10 most frequent words in the lower output box
6. Optionally click Export Results to save the output as a text file

---

# Technologies Used
* Python 3
* Tkinter
* python-docx
* PyPDF2

---

## License

This project is open-source and free to use.

---

## Acknowledgements

Created as part of a mini-project series for learning Python and GUI development.
Built with the support of AI tools to assist with code generation and structuring.
Suggestions and improvements are welcome!
