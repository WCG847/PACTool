import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
from struct import unpack
from cdata import CData
from cfile import CFile
from io import BytesIO

class PacViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PAC/DPAC Viewer - WinRAR Cursed Edition")
        self.file_list = []

        self.tree = ttk.Treeview(root, columns=('Index', 'Size', 'Pointer', 'Type', 'VFS'), show='headings')
        self.tree.heading('Index', text='Index')
        self.tree.heading('Size', text='Size')
        self.tree.heading('Pointer', text='Pointer')
        self.tree.heading('Type', text='Type')
        self.tree.heading('VFS', text='VFS Path')
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<Double-1>", self.on_double_click)

        btn_frame = tk.Frame(root)
        btn_frame.pack(fill=tk.X)

        self.load_btn = tk.Button(btn_frame, text="Open PAC/DPAC", command=self.load_pac)
        self.load_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.extract_btn = tk.Button(btn_frame, text="Extract Selected", command=self.extract_selected)
        self.extract_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.extract_all_btn = tk.Button(btn_frame, text="Extract All", command=self.extract_all)
        self.extract_all_btn.pack(side=tk.LEFT, padx=5, pady=5)

    def get_file_type(self, blob):
        if len(blob) < 4:
            return "RAW"
        magic = blob[:4]
        if magic == b'PAC ':
            return "PAC"
        if magic == b'DPAC':
            return "DPAC"
        return "RAW"

    def is_pac_file(self, blob):
        if len(blob) < 8:
            return False
        if blob[:4] != b'PAC ':
            return False
        file_count = unpack('<I', blob[4:8])[0]
        return 0 < file_count <= 100000

    def format_size(self, bytes_size):
        for unit in ['B', 'KB', 'MB']:
            if bytes_size < 1024:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024
        return f"{bytes_size:.1f} MB"

    def load_pac(self):
        path = filedialog.askopenfilename(title="Select PAC/DPAC File", filetypes=[("PAC Files", "*.PAC"), ("All Files", "*.*")])
        if not path:
            return

        try:
            self.tree.delete(*self.tree.get_children())
            blob = open(path, 'rb').read(8)

            if blob[:4] == b'DPAC':
                pac = CFile()
                pac.Start()
                pac.AddEnt(path)
                self.data = pac

                vfs_list = pac.ListVFS()
                for vfsPath in vfs_list:
                    try:
                        logic, size = pac.Search(vfsPath)
                        pac_stream = pac.HostRead(path)
                        base = (logic << 11) + 0x4000
                        pac_stream.seek(base)
                        blob = pac_stream.read(size << 8)
                        file_type = self.get_file_type(blob)

                        self.tree.insert('', tk.END, values=("?", self.format_size(size << 8), hex(base), file_type, vfsPath))
                    except Exception as e:
                        print(f"Failed VFS {vfsPath}: {e}")

            else:
                self.data = CData(wanted_path=path)
                self.file_list = self.data.ExtractEntries()
                for entry in self.file_list:
                    self.data.PAC.seek(entry['POINTER'])
                    blob = self.data.PAC.read(entry['SIZE'])
                    file_type = self.get_file_type(blob)
                    self.tree.insert('', tk.END, values=(
                        entry['INDEX'],
                        self.format_size(entry['SIZE']),
                        hex(entry['POINTER']),
                        file_type,
                        ""
                    ))

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def on_double_click(self, event):
        selected = self.tree.selection()
        if not selected:
            return

        item = self.tree.item(selected[0])
        pointer = item['values'][2]
        file_type = item['values'][3]
        vfs_path = item['values'][4]

        try:
            if hasattr(self.data, 'PAC'):  # CData
                for entry in self.file_list:
                    if hex(entry['POINTER']) == pointer:
                        self.data.PAC.seek(entry['POINTER'])
                        file_data = self.data.PAC.read(entry['SIZE'])
                        break
            else:  # CFile
                logic, size = self.data.Search(vfs_path)
                base = (logic << 11) + 0x4000
                file_data = self.data.HostRead("temp.pac")  # path was passed originally
                file_data.seek(base)
                file_data = file_data.read(size << 8)

            if file_type == "PAC":
                temp_path = os.path.join(os.getcwd(), "_inner_temp.pac")
                with open(temp_path, 'wb') as f:
                    f.write(file_data)
                self.data = CData(wanted_path=temp_path)
                self.file_list = self.data.ExtractEntries()

                self.tree.delete(*self.tree.get_children())
                for entry in self.file_list:
                    self.data.PAC.seek(entry['POINTER'])
                    blob = self.data.PAC.read(entry['SIZE'])
                    file_type = self.get_file_type(blob)
                    self.tree.insert('', tk.END, values=(
                        entry['INDEX'],
                        self.format_size(entry['SIZE']),
                        hex(entry['POINTER']),
                        file_type,
                        ""
                    ))

                self.root.title("PAC Viewer - Inner PAC")

        except Exception as e:
            messagebox.showerror("Error opening file", str(e))

    def extract_selected(self):
        selected = self.tree.selection()
        if not selected:
            return
        index = int(self.tree.item(selected[0])['values'][0], 16)
        for entry in self.file_list:
            if entry['INDEX'] == index:
                self.extract_entry(entry)

    def extract_all(self):
        out_dir = filedialog.askdirectory(title="Select Output Folder")
        if not out_dir:
            return
        for entry in self.file_list:
            self.extract_entry(entry, out_dir)

    def extract_entry(self, entry, out_dir=None):
        self.data.PAC.seek(entry['POINTER'])
        file_data = self.data.PAC.read(entry['SIZE'])

        if not out_dir:
            out_dir = filedialog.askdirectory(title="Select Output Folder")
            if not out_dir:
                return

        filename = f"{entry['INDEX']:04X}.bin"
        with open(os.path.join(out_dir, filename), 'wb') as f:
            f.write(file_data)
        print(f"Extracted: {filename}")

if __name__ == '__main__':
    root = tk.Tk()
    app = PacViewerApp(root)
    root.geometry("800x500")
    root.mainloop()