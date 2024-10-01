import struct
import sys
from pathlib import Path
from PySide6.QtCore import Qt, QSize
from qoi.decoder import QoiDecoder
from PySide6.QtWidgets import (
    QLabel,
    QWidget,
    QMainWindow,
    QVBoxLayout,
    QMessageBox,
    QApplication,
)
from PySide6.QtGui import (
    QImage,
    QColor,
    QPixmap,
    QShortcut,
    QDropEvent,
    QMouseEvent,
    QKeySequence,
    QWheelEvent,
    QPainter,
)


class QoiViewer(QMainWindow):
    def __init__(self, title_bar=False, qoi_path=None):
        super().__init__()
        self.setWindowTitle("QOI Viewer")
        self.setAcceptDrops(True)
        self.current_qoi_path = None
        if not title_bar:
            self.setWindowFlags(Qt.FramelessWindowHint)
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setText("Drag and drop a QOI image here")
        self.image_label.setMinimumSize(1, 1)
        self.image_label.setScaledContents(False)

        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        layout.setContentsMargins(0, 0, 0, 0)
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        self.decoder = QoiDecoder()
        self.pixmap = None
        self.image_locked = False
        self.zoom_factor = 1.0
        self.image_x_offset = 0
        self.image_y_offset = 0
        self.moving_image = False
        self._dragging = False
        self._resizing = False
        self._last_mouse_pos = None
        self.is_always_on_top = False
        self._title_bar = title_bar

        self.shortcut_q = QShortcut(QKeySequence("Q"), self)
        self.shortcut_q.activated.connect(self.close)

        self.shortcut_esc = QShortcut(QKeySequence(Qt.Key_Escape), self)
        self.shortcut_esc.activated.connect(self.close)

        self.shortcut_lock = QShortcut(QKeySequence("L"), self)
        self.shortcut_lock.activated.connect(self.toggle_image_lock)

        self.shortcut_reset_zoom = QShortcut(QKeySequence("R"), self)
        self.shortcut_reset_zoom.activated.connect(self.reset_zoom)

        self.shortcut_always_on_top = QShortcut(QKeySequence("T"), self)
        self.shortcut_always_on_top.activated.connect(self.toggle_always_on_top)

        self.shortcut_left_arrow = QShortcut(QKeySequence(Qt.Key_Left), self)
        self.shortcut_left_arrow.activated.connect(self.open_previous_image)

        self.shortcut_right_arrow = QShortcut(QKeySequence(Qt.Key_Right), self)
        self.shortcut_right_arrow.activated.connect(self.open_next_image)

        self.image_files = {}
        self.current_image_index = None

        self.shortcut_move_image = QShortcut(QKeySequence("M"), self)
        self.shortcut_move_image.activated.connect(self.toggle_image_moving)

        if qoi_path:
            self.load_qoi_image(qoi_path)
            self.update_image_list(qoi_path)

    def dragEnterEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile() and url.fileName().endswith(".qoi"):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            if url.isLocalFile() and url.fileName().endswith(".qoi"):
                self.load_qoi_image(url.toLocalFile())
                break

    def load_qoi_image(self, file_path):
        try:
            with open(file_path, "rb") as f:
                data = f.read()

            headers = self.decoder.headers(data)
            if headers.magic != b"qoif":
                raise ValueError("Invalid QOI file magic.")

            pixels = self.decoder.decoder(data, headers)

            image = QImage(headers.width, headers.height, QImage.Format_RGBA8888)
            for y in range(headers.height):
                for x in range(headers.width):
                    r, g, b, a = pixels[y * headers.width + x]
                    image.setPixelColor(x, y, QColor(r, g, b, a))

            self.pixmap = QPixmap.fromImage(image)
            self.image_label.setPixmap(self.pixmap)

            self.resize(headers.width, headers.height)

            self.setWindowTitle(f"QOI Viewer - {file_path}")
            self.current_qoi_path = file_path

        except (struct.error, ValueError) as e:
            QMessageBox.critical(self, "Error", f"Invalid QOI file: {e}")

    def update_image_list(self, file_path):
        qoi_directory = Path(file_path).absolute().parent
        if qoi_directory:
            self.image_files = {
                index: file.absolute()
                for index, file in enumerate(sorted(qoi_directory.glob("*.qoi")))
            }
            file_path = Path(file_path).absolute()
            self.current_image_index = list(self.image_files.values()).index(file_path)
        else:
            self.image_files = {}
            self.current_image_index = None

    def open_previous_image(self):
        if self.current_image_index is not None and self.image_files:
            self.current_image_index = (self.current_image_index - 1) % len(
                self.image_files
            )
            self.load_qoi_image(str(self.image_files[self.current_image_index]))

    def open_next_image(self):
        if self.current_image_index is not None and self.image_files:
            self.current_image_index = (self.current_image_index + 1) % len(
                self.image_files
            )
            self.load_qoi_image(str(self.image_files[self.current_image_index]))

    def resizeEvent(self, event):
        if not self.image_locked and self.pixmap:
            self.update_image_size()
        else:
            self.update_image_position()

    def wheelEvent(self, event: QWheelEvent):
        if self.pixmap:
            degrees = event.angleDelta().y() / 8
            steps = degrees / 15

            if steps > 0:
                self.zoom_factor += 0.1
            elif steps < 0:
                self.zoom_factor -= 0.1

            self.zoom_factor = max(0.1, self.zoom_factor)
            self.update_image_size()

    def update_image_size(self):
        if self.pixmap:
            aspect_ratio = self.pixmap.width() / self.pixmap.height()

            new_width = int(self.width() * self.zoom_factor)
            new_height = int(new_width / aspect_ratio)

            scaled_pixmap = self.pixmap.scaled(
                QSize(new_width, new_height),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )

            self.image_label.setPixmap(scaled_pixmap)
            self.image_label.setAlignment(Qt.AlignCenter)

    def mousePressEvent(self, event: QMouseEvent):
        if not self._title_bar:
            if event.button() == Qt.LeftButton:
                if self.moving_image:
                    self._dragging = True
                    self._last_mouse_pos = event.globalPosition()
                else:
                    self._dragging = True
                    self._last_mouse_pos = event.globalPosition()
            elif event.button() == Qt.RightButton:
                self._resizing = True
                self._last_mouse_pos = event.globalPosition()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging:
            if self.moving_image:
                delta = event.globalPosition() - self._last_mouse_pos
                self.image_x_offset += delta.x()
                self.image_y_offset += delta.y()
                self._last_mouse_pos = event.globalPosition()
                self.update_image_position()
            else:
                delta = event.globalPosition() - self._last_mouse_pos
                self.move(self.pos() + delta.toPoint())
                self._last_mouse_pos = event.globalPosition()
        elif self._resizing and not self.image_locked:
            delta = event.globalPosition() - self._last_mouse_pos
            aspect_ratio = self.pixmap.width() / self.pixmap.height()
            new_width = self.width() + delta.x()
            new_height = int(new_width / aspect_ratio)
            self.resize(new_width, new_height)
            self._last_mouse_pos = event.globalPosition()
        elif self._resizing and self.image_locked:
            delta = event.globalPosition() - self._last_mouse_pos

            zone_width = self.width() // 4
            zone_height = self.height() // 4

            if event.pos().x() < zone_width:
                self.setGeometry(
                    self.x() + delta.x(),
                    self.y(),
                    self.width() - delta.x(),
                    self.height(),
                )
            elif event.pos().x() > self.width() - zone_width:
                self.resize(self.width() + delta.x(), self.height())
            if event.pos().y() < zone_height:
                self.setGeometry(
                    self.x(),
                    self.y() + delta.y(),
                    self.width(),
                    self.height() - delta.y(),
                )
            elif event.pos().y() > self.height() - zone_height:
                self.resize(self.width(), self.height() + delta.y())

            self._last_mouse_pos = event.globalPosition()
            self.update_image_position()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._dragging = False
            self._last_mouse_pos = None
        elif event.button() == Qt.RightButton:
            self._resizing = False
            self._last_mouse_pos = None

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton or event.button() == Qt.RightButton:
            if self.isMaximized():
                self.showNormal()
                self.update_image_size()
            else:
                self.original_size = self.size()
                self.showMaximized()
                QApplication.instance().processEvents()
                self.zoom_to_fit()

    def zoom_to_fit(self):
        if self.isMaximized():
            aspect_ratio = self.pixmap.width() / self.pixmap.height()
            if self.width() / self.height() > aspect_ratio:
                self.resize(self.height() * aspect_ratio, self.height())
            else:
                self.resize(self.original_size)

    def toggle_image_lock(self):
        self.image_locked = not self.image_locked
        if self.image_locked:
            print("Image size locked.")
        else:
            print("Image size unlocked. Resizing will affect the image.")
            self.resizeEvent(None)

    def reset_zoom(self):
        self.zoom_factor = 1.0
        self.update_image_size()

    def toggle_always_on_top(self):
        self.is_always_on_top = not self.is_always_on_top
        if self.is_always_on_top:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            print("Window set to always on top.")
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
            print("Window is no longer always on top.")
        self.show()

    def toggle_image_moving(self):
        self.moving_image = not self.moving_image
        if self.moving_image:
            print("Image moving enabled.")
        else:
            print("Image moving disabled.")

    def update_image_position(self):
        if self.pixmap:
            x_offset = self.image_x_offset
            y_offset = self.image_y_offset

            new_pixmap = QPixmap(self.size())
            new_pixmap.fill(Qt.transparent)

            painter = QPainter(new_pixmap)
            painter.drawPixmap(x_offset, y_offset, self.pixmap)
            painter.end()

            self.image_label.setPixmap(new_pixmap)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    title_bar = "--title" in sys.argv
    qoi_path = None
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        qoi_path = sys.argv[1]

    viewer = QoiViewer(title_bar=title_bar, qoi_path=qoi_path)
    viewer.show()
    sys.exit(app.exec())
