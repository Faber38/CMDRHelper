DARK_STYLESHEET = r"""
QWidget {
    background: #080d12;
    color: #d8dde3;
    font-size: 12px;
}

QMainWindow {
    background: #080d12;
}

QFrame#sidebar {
    background: #090d11;
    border-right: 1px solid #20272e;
}

QFrame#topbar {
    background: #090d11;
    border-bottom: 1px solid #20272e;
}

QFrame#card {
    background: #0b1015;
    border: 1px solid #282f35;
    border-radius: 8px;
}

QScrollArea {
    background: #080d12;
    border: 0;
}

QScrollArea QWidget {
    background: #080d12;
}

QSplitter::handle {
    background: #1b252e;
    border: 1px solid #2d3943;
}

QSplitter::handle:hover {
    background: #5a3a0b;
    border-color: #9a620e;
}

QSplitter::handle:vertical {
    height: 7px;
}

QLabel#appTitle {
    font-size: 18px;
    font-weight: 700;
    color: #f2f4f5;
}

QLabel#appSubTitle,
QLabel#muted {
    color: #8e969e;
}

QLabel#commanderTitle {
    font-size: 18px;
    font-weight: 700;
    color: #ff9d00;
}

QLabel#sectionTitle {
    font-size: 13px;
    font-weight: 700;
    color: #ff9d00;
}

QLabel#cardValue {
    font-size: 18px;
    font-weight: 700;
    color: #f6f7f8;
}

QLabel#statusOk {
    color: #79d45a;
}

QLabel#statusWarn {
    color: #f0ad4e;
}

QPushButton {
    background: #111820;
    color: #d7dce1;
    border: 1px solid #28323b;
    border-radius: 6px;
    padding: 3px 7px;
    text-align: left;
}

QPushButton:hover {
    background: #17222c;
}

QPushButton#navActive {
    background: #20180b;
    color: #ff9d00;
    border-left: 3px solid #ff9d00;
    border-top: 0;
    border-right: 0;
    border-bottom: 0;
    border-radius: 0;
}

QPushButton#primary {
    background: #3a2609;
    color: #ffae28;
    border: 1px solid #704712;
}

QLineEdit {
    background: #0d141b;
    border: 1px solid #28323b;
    border-radius: 5px;
    padding: 8px;
}

QTableWidget {
    background: #0a1015;
    alternate-background-color: #0d141a;
    gridline-color: #232c34;
    border: 1px solid #232c34;
}

QHeaderView::section {
    background: #10161c;
    color: #aeb5bc;
    padding: 8px;
    border: 0;
    border-bottom: 1px solid #27313a;
}

QTableWidget::item {
    padding: 6px;
}

QTableWidget::item:selected {
    background: #2b3640;
}

QStatusBar {
    background: #080d12;
    color: #8c959d;
}
"""


LIGHT_STYLESHEET = r"""
QWidget {
    background: #eef1f4;
    color: #20262c;
    font-size: 12px;
}

QMainWindow {
    background: #eef1f4;
}

QFrame#sidebar {
    background: #f7f8fa;
    border-right: 1px solid #cbd2d9;
}

QFrame#topbar {
    background: #f7f8fa;
    border-bottom: 1px solid #cbd2d9;
}

QFrame#card {
    background: #ffffff;
    border: 1px solid #cbd2d9;
    border-radius: 8px;
}

QScrollArea {
    background: #eef1f4;
    border: 0;
}

QScrollArea QWidget {
    background: #eef1f4;
}

QSplitter::handle {
    background: #cbd2d9;
    border: 1px solid #b7c0c8;
}

QSplitter::handle:hover {
    background: #e4c28e;
    border-color: #c57a00;
}

QSplitter::handle:vertical {
    height: 7px;
}

QLabel#appTitle {
    font-size: 18px;
    font-weight: 700;
    color: #20262c;
}

QLabel#appSubTitle,
QLabel#muted {
    color: #65717c;
}

QLabel#commanderTitle {
    font-size: 18px;
    font-weight: 700;
    color: #c56f00;
}

QLabel#sectionTitle {
    font-size: 13px;
    font-weight: 700;
    color: #c56f00;
}

QLabel#cardValue {
    font-size: 18px;
    font-weight: 700;
    color: #171b1f;
}

QLabel#statusOk {
    color: #37852d;
}

QLabel#statusWarn {
    color: #b36a00;
}

QPushButton {
    background: #ffffff;
    color: #252b31;
    border: 1px solid #bfc7ce;
    border-radius: 6px;
    padding: 3px 7px;
    text-align: left;
}

QPushButton:hover {
    background: #e9edf1;
}

QPushButton#navActive {
    background: #fff1da;
    color: #b96500;
    border-left: 3px solid #d77d00;
    border-top: 0;
    border-right: 0;
    border-bottom: 0;
    border-radius: 0;
}

QPushButton#primary {
    background: #fff0d6;
    color: #a85d00;
    border: 1px solid #d99a3e;
}

QLineEdit {
    background: #ffffff;
    color: #20262c;
    border: 1px solid #bfc7ce;
    border-radius: 5px;
    padding: 8px;
}

QCheckBox {
    background: transparent;
    color: #20262c;
}

QTableWidget {
    background: #ffffff;
    alternate-background-color: #f3f5f7;
    color: #20262c;
    gridline-color: #d7dde2;
    border: 1px solid #cbd2d9;
}

QHeaderView::section {
    background: #e8ecef;
    color: #404950;
    padding: 8px;
    border: 0;
    border-bottom: 1px solid #c7ced5;
}

QTableWidget::item {
    padding: 6px;
}

QTableWidget::item:selected {
    background: #cfdce8;
    color: #15191d;
}

QStatusBar {
    background: #eef1f4;
    color: #65717c;
}

QToolTip {
    background: #ffffff;
    color: #20262c;
    border: 1px solid #aeb7bf;
}
"""
