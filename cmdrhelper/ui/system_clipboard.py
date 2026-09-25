from PySide6.QtWidgets import QApplication


def copy_system_name(name):
    if isinstance(name, str) and name.strip() and name.strip() != "–":
        QApplication.clipboard().setText(name)
