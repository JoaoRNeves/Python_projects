# ===============================
# Word Frequency Counter (Tkinter GUI)
# ===============================

# ---- Imports ----
import os
import re
from collections import Counter
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from docx import Document
from PyPDF2 import PdfReader

# ===============================
# Text Analysis Functions
# ===============================

def get_frequency(text: str) -> list[tuple[str, int]]:
    """
    Count and return the 10 most common words in the input text.
    """
    lowered_text = text.lower()
    words = re.findall(r'\b\w+\b', lowered_text)
    word_counts = Counter(words)
    return word_counts.most_common(10)

def extract_text_from_file(file_path: str) -> str:
    """
    Extract text content from .txt, .docx, or .pdf files.
    """
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    if ext == '.txt':
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    elif ext == '.docx':
        doc = Document(file_path)
        return '\n'.join([para.text for para in doc.paragraphs])
    elif ext == '.pdf':
        reader = PdfReader(file_path)
        return '\n'.join([page.extract_text() or '' for page in reader.pages])
    else:
        raise ValueError(f"Unsupported file type: {ext}")

# ===============================
# GUI Button Callback Functions
# ===============================

def load_file():
    """
    Open file dialog and load text from the selected file into the input box.
    """
    file_path = filedialog.askopenfilename(
        filetypes=[
            ("Text files", "*.txt"),
            ("Word files", "*.docx"),
            ("PDF files", "*.pdf")
        ]
    )
    if not file_path:
        return

    try:
        content = extract_text_from_file(file_path)
        text_input.delete(1.0, tk.END)
        text_input.insert(tk.END, content)
    except Exception as e:
        messagebox.showerror("Error", f"Could not load file:\n{e}")

def process_text():
    """
    Analyze input text and display the top 10 most frequent words.
    """
    text = text_input.get("1.0", tk.END).strip()
    if not text:
        messagebox.showwarning("Empty Input", "Please enter or load some text.")
        return

    frequencies = get_frequency(text)

    output.config(state='normal')
    output.delete(1.0, tk.END)
    for word, count in frequencies:
        output.insert(tk.END, f"{word}: {count}\n")
    output.config(state='disabled')

def export_results():
    """
    Export the results area content to a .txt file.
    """
    content = output.get("1.0", tk.END).strip()
    if not content:
        messagebox.showinfo("No Data", "No results to export.")
        return

    save_path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text File", "*.txt")]
    )
    if save_path:
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(content)
            messagebox.showinfo("Success", "Results saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file:\n{e}")

# ===============================
# Main GUI Layout
# ===============================

root = tk.Tk()
root.title("Word Frequency Counter")
root.geometry("700x600")

# --- Instruction Label ---
label = tk.Label(root, text="Upload a file or enter text below:", font=("Arial", 14))
label.pack(pady=10)

# --- File Buttons Frame ---
file_frame = tk.Frame(root)
file_frame.pack(pady=5)

file_btn = tk.Button(file_frame, text="Choose File", command=load_file)
file_btn.pack(side="left", padx=10)

export_btn = tk.Button(file_frame, text="Export Results", command=export_results)
export_btn.pack(side="left", padx=10)

# --- Manual Text Input ---
text_input = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=80, height=12)
text_input.pack(pady=10)

# --- Process Button ---
process_btn = tk.Button(root, text="Count Words", command=process_text)
process_btn.pack(pady=10)

# --- Results Output Box ---
output = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=80, height=10, state='disabled')
output.pack(pady=10)

# --- Start Application Loop ---
root.mainloop()

