import sys
import ctypes
import os
import datetime
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

if not is_admin():
    # Relaunch the script with admin rights
    params = ' '.join([f'"{arg}"' for arg in sys.argv])
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, params, None, 1)
    sys.exit(0)

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

        # Main horizontal layout: left = list, right = form+buttons
        main_layout = QHBoxLayout()

        # Left side: Product List with label
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Stockpile List:"))
        self.product_list = QListWidget()
        left_layout.addWidget(self.product_list)

        # Right side: Form + Buttons
        right_layout = QVBoxLayout()

        form_layout = QFormLayout()
        self.name_input = QLineEdit()
        self.amount_input = QLineEdit()
        self.purchased_input = QLineEdit()
        self.expiry_input = QLineEdit()

        form_layout.addRow("Product Name:", self.name_input)
        form_layout.addRow("Amount:", self.amount_input)
        form_layout.addRow("Date Purchased:", self.purchased_input)
        form_layout.addRow("Date Expiry:", self.expiry_input)

        right_layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add Product")
        self.edit_button = QPushButton("Edit")
        self.delete_button = QPushButton("Delete")
        self.edit_button.setEnabled(False)
        self.delete_button.setEnabled(False)

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)

        right_layout.addLayout(button_layout)

        # Add left and right layouts to main layout
        main_layout.addLayout(left_layout, stretch=3)   # list gets more space
        main_layout.addLayout(right_layout, stretch=2)  # form/buttons less space

        central_widget.setLayout(main_layout)

        # Connect signals after widgets created
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

            add_product(name, amount, str(purchase_date), str(expiry_date))
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
            item_text = f"{name} | Qty: {amount} | Bought: {purchased} | Expires: {expires} [{status}]"
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
        text = item.text()
        product_id = int(item.data(Qt.UserRole))
        self.selected_product_id = product_id

        # Parse values back from text
        parts = text.split(" | ")
        name = parts[0]
        amount = parts[1].split(":")[1].strip()
        purchased = parts[2].split(":")[1].strip()
        expires = parts[3].split(":")[1].split(" ")[0].strip()

        self.name_input.setText(name)
        self.amount_input.setText(amount)
        self.purchased_input.setText(purchased)
        self.expiry_input.setText(expires)

        self.edit_button.setEnabled(True)
        self.delete_button.setEnabled(True)

    def edit_product(self):
        if self.selected_product_id is None:
            return

        try:
            name = self.name_input.text().strip()
            amount = int(self.amount_input.text())
            purchased = parse_date(self.purchased_input.text(), self.config["date_format"])
            expires = parse_date(self.expiry_input.text(), self.config["date_format"])

            from modules.db_manager import update_product
            update_product(self.selected_product_id, name, amount, str(purchased), str(expires))
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
    window = StockpileApp()
    window.show()
    sys.exit(app.exec_())
