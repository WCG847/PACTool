from PyQt5.QtWidgets import (
	QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QFileDialog,
	QMessageBox, QHBoxLayout, QAbstractItemView, QTreeWidget, QTreeWidgetItem,
	QMenu, QFileIconProvider
)
from PyQt5.QtCore import Qt, QPoint
import sys, os
from DPAC import DirectoryPackage


def human_readable_size(size):
	for unit in ['B', 'KB', 'MB', 'GB']: # windows formatting
		if size < 1024.0:
			return f"{size:.2f} {unit}"
		size /= 1024.0
	return f"{size:.2f} TB"


class DPACGUI(QMainWindow):
	def __init__(self):
		super().__init__()
		self.setWindowTitle("PACTool")
		self.resize(900, 600)

		self.dpac = DirectoryPackage()
		self.contents = []

		self.init_ui()

	def init_ui(self):
		main_widget = QWidget()
		self.setCentralWidget(main_widget)

		main_layout = QVBoxLayout()
		main_widget.setLayout(main_layout)

		# Control buttons
		top_layout = QHBoxLayout()
		self.load_btn = QPushButton("Load DPAC")
		self.load_btn.clicked.connect(self.load_dpac)

		self.export_btn = QPushButton("Export Selected")
		self.export_btn.clicked.connect(self.export_selected)

		top_layout.addWidget(self.load_btn)
		top_layout.addWidget(self.export_btn)
		top_layout.addStretch()
		main_layout.addLayout(top_layout)

		# File explorer-style tree
		self.tree = QTreeWidget()
		self.tree.setHeaderLabels(["Name", "Size", "Offset"])
		self.tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
		self.tree.setColumnWidth(0, 300)
		self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
		self.tree.customContextMenuRequested.connect(self.context_menu)
		main_layout.addWidget(self.tree)

		# Set default icons

		icon_provider = QFileIconProvider()
		self.folder_icon = icon_provider.icon(QFileIconProvider.Folder)
		self.file_icon = icon_provider.icon(QFileIconProvider.File)

	def load_dpac(self):
		file_path, _ = QFileDialog.getOpenFileName(self, "Select DPAC File", "", "DPAC files (*.pac);;All files (*.*)")
		if not file_path:
			return

		try:
			self.dpac.Load(file_path)
			self.contents = self.dpac.Bin2Dict()
			self.display_contents()
		except Exception as e:
			QMessageBox.critical(self, "Error", f"Failed to load DPAC file:\n{str(e)}")

	def display_contents(self):
		self.tree.clear()
		for folder, file_count, entries in self.contents:
			folder_item = QTreeWidgetItem([folder])
			folder_item.setIcon(0, self.folder_icon)
			folder_item.setExpanded(True)

			for entry in entries:
				name, size, offset = entry
				h_size = human_readable_size(size)
				file_item = QTreeWidgetItem([name, h_size, str(offset)])
				file_item.setIcon(0, self.file_icon)
				folder_item.addChild(file_item)

			self.tree.addTopLevelItem(folder_item)

	def export_selected(self):
		selected_items = self.tree.selectedItems()
		if not selected_items:
			QMessageBox.information(self, "Info", "No file selected.")
			return

		export_dir = QFileDialog.getExistingDirectory(self, "Select Export Directory")
		if not export_dir:
			return

		export_count = 0
		for item in selected_items:
			parent = item.parent()
			if not parent:
				continue  # Skip top-level folders

			folder_name = parent.text(0)
			name = item.text(0)
			size = self.parse_size(item.text(1))  # convert back to int
			offset = int(item.text(2))

			self.dpac.Data.seek(offset)
			data = self.dpac.Data.read(size)

			out_folder = os.path.join(export_dir, folder_name)
			os.makedirs(out_folder, exist_ok=True)
			with open(os.path.join(out_folder, name), 'wb') as f:
				f.write(data)
			export_count += 1

		QMessageBox.information(self, "Success", f"Export completed. Files exported: {export_count}")

	def parse_size(self, size_str):
		# Reverse conversion from human-readable back to int bytes
		multipliers = {'B': 1, 'KiB': 1024, 'MiB': 1024**2, 'GiB': 1024**3}
		try:
			value, unit = size_str.split()
			return int(float(value) * multipliers.get(unit, 1))
		except:
			return int(size_str)

	def context_menu(self, position: QPoint):
		item = self.tree.itemAt(position)
		if not item or not item.parent():
			return  # Don't show menu on folders

		menu = QMenu()
		export_action = menu.addAction("Export")
		info_action = menu.addAction("View Info")
		action = menu.exec_(self.tree.viewport().mapToGlobal(position))

		if action == export_action:
			self.export_selected()
		elif action == info_action:
			name = item.text(0)
			size = item.text(1)
			offset = item.text(2)
			QMessageBox.information(self, "File Info", f"Name: {name}\nSize: {size}\nOffset: {offset}")


if __name__ == '__main__':
	app = QApplication(sys.argv)
	window = DPACGUI()
	window.show()
	sys.exit(app.exec_())
