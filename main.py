import sys
import ctypes
import os
import datetime
import re
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QMessageBox, QComboBox, QMainWindow
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

from modules.db_manager import init_db, add_product, get_products
from modules.config_manager import load_config, save_config
from utils.date_parser import parse_date


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False



class StockpileApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Doomsday Prepper Stockpile")
        self.setWindowIcon(QIcon("assets/icon.ico"))
        self.resize(800, 500)

        self.selected_product_id = None



        self.config = load_config()
        if not self.config["date_format"]:
            self.ask_date_format()

        init_db()
        self.setup_ui()
        self.refresh_list()

    def ask_date_format(self):
        formats = ["dd/mm/yyyy", "mm/dd/yyyy", "yyyy/mm/dd", "yyyy/dd/mm"]
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Select Date Format")
        msg_box.setText("Choose your preferred date format:")
        combo = QComboBox()
        combo.addItems(formats)

        layout = msg_box.layout()
        layout.addWidget(combo, 1, 1)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()

        save_config(combo.currentText())
        self.config = load_config()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', sans-serif;
                font-size: 11pt;
            }
            QLineEdit {
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #3A7BD5;
                color: white;
                padding: 8px 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #285EA8;
            }
            QPushButton:disabled {
                background-color: #aaa;
            }
            QListWidget {
                background-color: #f9f9f9;
                border: 1px solid #ccc;
                padding: 5px;
            }
            QLabel {
                font-weight: bold;
            }
        """)

        main_layout = QHBoxLayout()

        # Left side: Product List
        left_layout = QVBoxLayout()
        list_label = QLabel("🧾 Stockpile List:")
        left_layout.addWidget(list_label)
        self.product_list = QListWidget()
        self.product_list.setAlternatingRowColors(True)
        left_layout.addWidget(self.product_list)

        # Right side: Form and Buttons
        right_layout = QVBoxLayout()
        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        self.name_input = QLineEdit()
        self.amount_input = QLineEdit()
        self.purchased_input = QLineEdit()
        self.expiry_input = QLineEdit()

        form_layout.addRow("🛒 Product Name:", self.name_input)
        form_layout.addRow("📦 Amount:", self.amount_input)
        form_layout.addRow("📅 Date Purchased:", self.purchased_input)
        form_layout.addRow("⏳ Date Expiry:", self.expiry_input)

        right_layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.add_button = QPushButton("➕ Add")
        self.edit_button = QPushButton("✏️ Edit")
        self.delete_button = QPushButton("🗑️ Delete")

        self.edit_button.setEnabled(False)
        self.delete_button.setEnabled(False)

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)

        right_layout.addLayout(button_layout)

        # Add layouts to main layout
        main_layout.addLayout(left_layout, stretch=3)
        main_layout.addLayout(right_layout, stretch=2)

        central_widget.setLayout(main_layout)

        # Signals
        self.product_list.itemClicked.connect(self.on_item_selected)
        self.add_button.clicked.connect(self.add_product)
        self.edit_button.clicked.connect(self.edit_product)
        self.delete_button.clicked.connect(self.delete_product)



    def add_product(self):
        try:
            name = self.name_input.text().strip()
            amount = int(self.amount_input.text())
            purchase_date = parse_date(self.purchased_input.text(), self.config["date_format"])
            expiry_date = parse_date(self.expiry_input.text(), self.config["date_format"])

            add_product(name, amount, purchase_date.date().isoformat(), expiry_date.date().isoformat())

            self.refresh_list()

            self.name_input.clear()
            self.amount_input.clear()
            self.purchased_input.clear()
            self.expiry_input.clear()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not add product:\n{e}")

    def refresh_list(self):
        self.product_list.clear()  # Clear existing items
        from modules.db_manager import get_products
        products = get_products()

        for prod in products:
            product_id, name, amount, purchased, expires = prod
            status = self.expiry_status(datetime.date.fromisoformat(expires))
            fmt_map = {
                "dd/mm/yyyy": "%d/%m/%Y",
                "mm/dd/yyyy": "%m/%d/%Y",
                "yyyy/mm/dd": "%Y/%m/%d",
                "yyyy/dd/mm": "%Y/%d/%m",
            }
            fmt = self.config["date_format"]
            date_fmt = fmt_map.get(fmt, "%Y-%m-%d")

            try:
                purchased_fmt = datetime.datetime.fromisoformat(purchased).strftime(date_fmt)
                expires_fmt = datetime.datetime.fromisoformat(expires).strftime(date_fmt)
            except Exception as e:
                purchased_fmt = purchased
                expires_fmt = expires

            item_text = f"{name} | Qty: {amount} | Bought: {purchased_fmt} | Expires: {expires_fmt} [{status}]"

            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, product_id)

            if status == "Expired":
                item.setForeground(Qt.red)
            elif status == "Expiring Soon":
                item.setForeground(Qt.darkYellow)
            else:
                item.setForeground(Qt.darkGreen)

            self.product_list.addItem(item)

    def expiry_status(self, expiry_date):
        today = datetime.date.today()
        days_left = (expiry_date - today).days
        if days_left < 0:
            return "Expired"
        elif days_left <= 30:
            return "Expiring Soon"
        return "Still Good"




    def on_item_selected(self, item):
        try:
            text = item.text()
            product_id = int(item.data(Qt.UserRole))
            self.selected_product_id = product_id

            parts = text.split(" | ")
            name = parts[0]
            amount = parts[1].split(":")[1].strip()
            purchased = parts[2].split(":")[1].strip()

            # Extract expiry date safely using regex
            expires_part = parts[3]
            match = re.search(r"Expires:\s*([\d/\\\-]+)", expires_part)

            if not match:
                raise ValueError("Could not parse expiry date")
            expires = match.group(1)

            purchased_dt = parse_date(purchased, self.config["date_format"])
            expires_dt = parse_date(expires, self.config["date_format"])

            fmt = self.config["date_format"]
            fmt_map = {
                "dd/mm/yyyy": "%d/%m/%Y",
                "mm/dd/yyyy": "%m/%d/%Y",
                "yyyy/mm/dd": "%Y/%m/%d",
                "yyyy/dd/mm": "%Y/%d/%m",
            }

            purchased_str = purchased_dt.strftime(fmt_map[fmt])
            expires_str = expires_dt.strftime(fmt_map[fmt])

            self.name_input.setText(name)
            self.amount_input.setText(amount)
            self.purchased_input.setText(purchased_str)
            self.expiry_input.setText(expires_str)

            self.edit_button.setEnabled(True)
            self.delete_button.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error selecting item:\n{e}")


    def edit_product(self):
        if self.selected_product_id is None:
            return

        try:
            name = self.name_input.text().strip()
            amount = int(self.amount_input.text())
            purchased = parse_date(self.purchased_input.text(), self.config["date_format"])
            expires = parse_date(self.expiry_input.text(), self.config["date_format"])

            from modules.db_manager import update_product
            update_product(self.selected_product_id, name, amount, purchased.date().isoformat(), expires.date().isoformat())

            self.refresh_list()
            self.clear_form()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not edit product:\n{e}")

    def delete_product(self):
        if self.selected_product_id is None:
            return

        from modules.db_manager import delete_product
        confirm = QMessageBox.question(
            self, "Confirm Delete",
            "Are you sure you want to delete this item?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            delete_product(self.selected_product_id)
            self.refresh_list()
            self.clear_form()

    def clear_form(self):
        self.name_input.clear()
        self.amount_input.clear()
        self.purchased_input.clear()
        self.expiry_input.clear()
        self.selected_product_id = None
        self.edit_button.setEnabled(False)
        self.delete_button.setEnabled(False)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    if not is_admin():
        # Relaunch the script with admin rights
        params = ' '.join([f'"{arg}"' for arg in sys.argv])
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, params, None, 1)
        sys.exit(0)

    window = StockpileApp()
    window.show()
    sys.exit(app.exec_())
