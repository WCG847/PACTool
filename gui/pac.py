import tkinter as tk
from tkinter import PhotoImage, Toplevel, ttk, filedialog
import platform
import tempfile
import os
import subprocess
from decimal import Decimal, ROUND_HALF_UP


def human_size(n: int) -> str:
	units = ["B", "KiB", "MiB", "GiB", "TiB"]
	size = Decimal(n)

	for unit in units:
		if size < 1024:
			if unit == "B":
				return f"{int(size)} B"

			size = size.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
			text = format(size, "f").rstrip("0").rstrip(".")
			return f"{text} {unit}"

		size /= 1024


class PAC:
	def __init__(self):
		self.temp_dir = tempfile.mkdtemp(prefix="pactool_")
		self.payloads = {}

		self.os = platform.system().upper()
		self.slash = "\\" if self.os == "WINDOWS" else "/"
		self.root = tk.Tk()
		self.root.geometry("640x480")
		self.root.title("PACTool")
		self.folder = PhotoImage(file="folder_16x16.png")
		self.file = PhotoImage(file="file_16x16.png")
		self.save = PhotoImage(file="save16x16.png")
		self.build()

	def build(self):
		self.context_menu = tk.Menu(self.root, tearoff=0)
		self.context_menu.add_command(label="Open with", command=self.open_with)
		self.context_menu.add_command(label="Extract", command=self.extract_selected)
		self.context_menu.add_command(label="Extract All", command=self.extract_all)
		self.context_menu.add_separator()
		self.context_menu.add_command(label="Properties", command=self.show_properties)
		menubar = tk.Menu(self.root)
		file = tk.Menu(menubar, tearoff=0)
		self.build_file(file)
		menubar.add_cascade(label="File", menu=file)
		self.root.config(menu=menubar)
		self.tree = self.build_treeview()
		self.bind_keys()

	def open_with(self, event=None):
		path = filedialog.askopenfilename(
			defaultextension="*.exe",
			filetypes=[("Programmes", "*.exe *.elf")],
			title="Open with...",
		)
		sel = self.tree.selection()
		if not sel:
			return
		iid = sel[0]
		if self.tree.parent(iid) == "":
			return

		name = self.tree.item(iid, "text").strip()
		out_path = os.path.join(self.temp_dir, name)

		payload = self.payloads.get(iid)
		if payload is None:
			return

		with open(out_path, "wb") as f:
			f.write(payload.tobytes())

		subprocess.Popen([path, out_path])

	def build_treeview(self):
		tree = ttk.Treeview(self.root, columns=("Sector", "Size"), show="tree headings")

		tree.heading("#0", text="Name")
		tree.heading("Sector", text="Sector")
		tree.heading("Size", text="Size")
		tree.column("#0", width=200, anchor="w")
		tree.column("Sector", width=100, anchor="center")
		tree.column("Size", width=80, anchor="e")

		tree.pack(fill="both", expand=True)
		return tree

	def build_file(self: PAC, file: tk.Menu):
		file.add_command(label="Open", accelerator="Ctrl+O", command=self.open_pac)
		file.add_command(label="Close", accelerator="Ctrl+F4", command=self.close_pac)
		file.add_separator()
		file.add_command(
			label="Save",
			accelerator="Ctrl+S",
			command=self.export_pac,
			image=self.save,
			compound="left",
		)
		file.add_command(
			label="Save as",
			image=self.save,
			command=self.export_named_pac,
			compound="left",
		)
		file.add_separator()
		file.add_command(label="Exit", command=self.root.quit)

	def run(self):
		self.root.mainloop()

	def folder_size(self, folder_iid):
		total = 0
		for child in self.tree.get_children(folder_iid):
			size = int(self.tree.item(child, "tags")[0])
			total += size
		return total

	def bind_keys(self):
		self.root.bind("<Control-o>", self.open_pac)
		self.root.bind("<Control-s>", self.export_pac)
		self.root.bind("<Control-F4>", self.close_pac)
		self.root.bind("<Control-q>", lambda e: self.root.quit())
		self.tree.bind("<Button-3>", self.on_right_click)
		self.tree.bind('<Double-Button-1>', self.open_with)

	def on_right_click(self, event):
		iid = self.tree.identify_row(event.y)
		if not iid:
			return

		self.tree.selection_set(iid)
		self.context_menu.tk_popup(event.x_root, event.y_root)

	def extract_selected(self):
		iid = self.tree.selection()
		if not iid:
			return
		print("Extract:", self.tree.item(iid[0], "text"))

	def extract_all(self):
		print("Extract all files")

	def show_properties(self):
		sel = self.tree.selection()
		if not sel:
			return
		iid = sel[0]
		top = Toplevel(master=self.root)
		top.geometry("405x480")

		is_folder = self.tree.parent(iid) == ""
		name = self.tree.item(iid, "text").strip()
		top.title(f"{name} Properties")
		top.iconphoto(False, self.folder if is_folder else self.file)
		notebook = ttk.Notebook(top)
		notebook.pack(fill="both", expand=True)

		tab_browser = ttk.Frame(notebook)
		tab_info = ttk.Frame(notebook)
		# Row 1: icon + name
		row1 = ttk.Frame(tab_browser)
		row1.pack(anchor="w", padx=10, pady=(10, 4))

		tk.Label(row1, image=self.folder if is_folder else self.file).grid(
			row=0, column=0, sticky="w"
		)

		self.name_var = tk.StringVar(value=name)
		ttk.Entry(row1, textvariable=self.name_var, width=30).grid(
			row=0, column=1, sticky="w", padx=(8, 0)
		)

		# Separator
		ttk.Separator(tab_browser, orient="horizontal").pack(fill="x", padx=10, pady=10)

		# Row 2: Type
		row2 = ttk.Frame(tab_browser)
		row2.pack(anchor="w", padx=10)

		ttk.Label(row2, text="Type:" if is_folder else "Type of file:", width=24).grid(
			row=0, column=0, sticky="w"
		)
		ttk.Label(row2, text="File folder" if is_folder else "PAC file").grid(
			row=0, column=1, sticky="w"
		)
		ttk.Label(row2, text="Location:", width=24).grid(row=1, column=0, sticky="w")
		if is_folder:
			file = ""
			folder = name
		else:
			file = self.slash + name
			folder = self.tree.item(self.tree.parent(iid), "text").strip()
		ttk.Label(row2, text=f"{self.slash}{folder}{file}").grid(
			row=1, column=1, sticky="w"
		)
		if is_folder:
			total = self.folder_size(iid)
			ttk.Label(row2, text=human_size(total)).grid(row=2, column=1, sticky="w")
			ttk.Label(row2, text="Size:", width=24).grid(row=2, column=0, sticky="w")

		else:
			ttk.Label(row2, text=self.tree.item(iid, "values")[1]).grid(
				row=2, column=1, sticky="w"
			)
			ttk.Label(row2, text="Size:", width=24).grid(row=2, column=0, sticky="w")

		notebook.add(tab_browser, text="General")
		notebook.add(tab_info, text="Details")

	def open_pac(self, event=None):
		file = filedialog.askopenfile(
			mode="rb",
			defaultextension="*.PAC",
			filetypes=[("SmackDown! Files", "*.PAC")],
		)
		if file:
			match file.read(4):
				case b"DPAC":
					from logic.file import File

					treeview_things: dict = File.read(file)
					self.use_directories = True
		else:
			raise FileNotFoundError(f"not found")
		self.tree.delete(*self.tree.get_children())

		for folder_name, files in treeview_things.items():
			folder_id = self.tree.insert(
				"",
				"end",
				text=" " + folder_name.decode("ascii", errors="replace").rstrip(" "),
				image=self.folder,
				open=False,
			)

			for file_name, meta in files.items():
				iid = self.tree.insert(
					folder_id,
					"end",
					text=" " + file_name.decode("ascii", errors="replace").rstrip(" "),
					image=self.file,
					values=(meta["sector"], human_size(meta["size"] * 256)),
					tags=(str(meta["size"] * 256),),
				)

				self.payloads[iid] = meta["payload"]

	def close_pac(self, event=None): ...
	def export_pac(self, event=None): ...
	def export_named_pac(self, event=None): ...