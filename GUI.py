import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from DPAC import DirectoryPackage
import os

class DPACGUI:
	def __init__(self, root):
		self.root = root
		self.root.title("PACTool")
		self.dpac = DirectoryPackage()
		self.contents = []

		self.create_widgets()

	def create_widgets(self):
		# Top Frame
		top_frame = tk.Frame(self.root)
		top_frame.pack(fill=tk.X, padx=10, pady=5)

		self.load_btn = tk.Button(top_frame, text="Load DPAC", command=self.load_dpac)
		self.load_btn.pack(side=tk.LEFT)

		self.export_btn = tk.Button(top_frame, text="Export Selected", command=self.export_selected)
		self.export_btn.pack(side=tk.LEFT, padx=10)

		# Treeview for file contents
		self.tree = ttk.Treeview(self.root, columns=('Size', 'Offset'), show='tree headings')
		self.tree.heading('#0', text='File/Folder')
		self.tree.heading('Size', text='Size')
		self.tree.heading('Offset', text='Offset')
		self.tree.column('Size', width=100)
		self.tree.column('Offset', width=100)
		self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

	def load_dpac(self):
		file_path = filedialog.askopenfilename(title="Select DPAC File", filetypes=[("DPAC files", "*.pac"), ("All files", "*.*")])
		if not file_path:
			return

		try:
			self.dpac.Load(file_path)
			self.contents = self.dpac.Bin2Dict()
			self.display_contents()
		except Exception as e:
			messagebox.showerror("Error", f"Failed to load DPAC file:\n{e}")

	def display_contents(self):
		self.tree.delete(*self.tree.get_children())
		for folder, file_count, entries in self.contents:
			folder_id = self.tree.insert('', 'end', text=folder, open=True)
			for entry in entries:
				name_or_id, size, offset = entry[0], entry[1], entry[2]
				self.tree.insert(folder_id, 'end', text=name_or_id, values=(size, offset))

	def export_selected(self):
		selected = self.tree.selection()
		if not selected:
			messagebox.showinfo("Info", "No file selected.")
			return

		export_dir = filedialog.askdirectory(title="Select Export Directory")
		if not export_dir:
			return

		for item in selected:
			parent = self.tree.parent(item)
			if not parent:
				continue  # skip folders
			folder_name = self.tree.item(parent, 'text')
			name = self.tree.item(item, 'text')
			size, offset = self.tree.item(item, 'values')
			size = int(size)
			offset = int(offset)

			self.dpac.Data.seek(offset)
			data = self.dpac.Data.read(size)

			out_folder = os.path.join(export_dir, folder_name)
			os.makedirs(out_folder, exist_ok=True)
			with open(os.path.join(out_folder, name), 'wb') as f:
				f.write(data)

		messagebox.showinfo("Success", "Export completed.")

if __name__ == "__main__":
	root = tk.Tk()
	app = DPACGUI(root)
	root.mainloop()
