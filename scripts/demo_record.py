from __future__ import annotations

import io
import os
from pathlib import Path

from PIL import Image
from PyQt6.QtCore import QBuffer, QIODevice, QTimer
from PyQt6.QtWidgets import QApplication

from l2_features.ui.windows.main_window import MainWindow


def qpixmap_to_pil(window: MainWindow) -> Image.Image:
    pixmap = window.grab()
    buf = QBuffer()
    buf.open(QIODevice.OpenModeFlag.ReadWrite)
    pixmap.save(buf, "PNG")
    image = Image.open(io.BytesIO(bytes(buf.data())))
    return image.convert("RGB")


def main() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    project_root = Path(__file__).resolve().parents[1]
    data_path = project_root / "examples" / "sample_data" / "l2_sample.csv"
    out_path = project_root / "assets" / "demo_replay.gif"

    app = QApplication([])
    window = MainWindow()
    window.show()

    window.path_input.setText(str(data_path))
    window._load_data()  # noqa: SLF001 - demo automation script
    window._vm.set_speed(2.0)  # noqa: SLF001

    frames: list[Image.Image] = []
    frame_count = 0
    max_frames = 80

    def capture_frame() -> None:
        nonlocal frame_count
        frame_count += 1
        if frame_count % 2 == 0:
            frames.append(qpixmap_to_pil(window))
        if len(frames) >= max_frames:
            finish()

    def finish() -> None:
        window._vm.pause()  # noqa: SLF001
        if frames:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            frames[0].save(
                out_path,
                save_all=True,
                append_images=frames[1:],
                duration=80,
                loop=0,
                optimize=True,
            )
            print(f"Saved demo gif: {out_path}")
            print(f"Captured frames: {len(frames)}")
        else:
            print("No frames captured")
        app.quit()

    window._vm.frame_changed.connect(lambda _frame: capture_frame())  # noqa: SLF001
    window._vm.replay_finished.connect(finish)  # noqa: SLF001
    QTimer.singleShot(200, window._vm.play)  # noqa: SLF001

    app.exec()


if __name__ == "__main__":
    main()
