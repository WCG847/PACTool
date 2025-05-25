import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
from .Yukes.cdata import CData

class PacViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PAC Viewer - WinRAR Cursed Edition")
        self.file_list = []

        self.tree = ttk.Treeview(root, columns=('Index', 'Size', 'Pointer'), show='headings')
        self.tree.heading('Index', text='Index')
        self.tree.heading('Size', text='Size')
        self.tree.heading('Pointer', text='Pointer')
        self.tree.pack(fill=tk.BOTH, expand=True)

        btn_frame = tk.Frame(root)
        btn_frame.pack(fill=tk.X)

        self.load_btn = tk.Button(btn_frame, text="Open PAC", command=self.load_pac)
        self.load_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.extract_btn = tk.Button(btn_frame, text="Extract Selected", command=self.extract_selected)
        self.extract_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.extract_all_btn = tk.Button(btn_frame, text="Extract All", command=self.extract_all)
        self.extract_all_btn.pack(side=tk.LEFT, padx=5, pady=5)

    def load_pac(self):
        path = filedialog.askopenfilename(title="Select PAC File", filetypes=[("PAC Files", "*.PAC"), ("All Files", "*.*")])
        if not path:
            return
        try:
            self.data = CData(wanted_path=path)
            self.file_list = self.data.Search()
            self.tree.delete(*self.tree.get_children())
            for entry in self.file_list:
                self.tree.insert('', tk.END, values=(entry['INDEX'], entry['SIZE'], hex(entry['POINTER'])))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def extract_selected(self):
        selected = self.tree.selection()
        if not selected:
            return
        index = self.tree.item(selected[0])['values'][0]
        for entry in self.file_list:
            if entry['INDEX'] == index:
                self.extract_entry(entry)

    def extract_all(self):
        for entry in self.file_list:
            self.extract_entry(entry)

    def extract_entry(self, entry):
        self.data.PAC.seek(entry['POINTER'])
        file_data = self.data_
