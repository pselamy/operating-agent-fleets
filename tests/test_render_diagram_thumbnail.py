from __future__ import annotations

import importlib.util
import io
import struct
import subprocess
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).parents[1] / "tools" / "render_diagram_thumbnail.py"
SPEC = importlib.util.spec_from_file_location("render_diagram_thumbnail", MODULE_PATH)
thumbs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(thumbs)


class ThumbnailRendererTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.output = Path(self.directory.name) / "thumbnail.png"

    @staticmethod
    def png() -> bytes:
        def chunk(kind: bytes, data: bytes) -> bytes:
            return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        header = struct.pack(">IIBBBBB", 1200, 627, 8, 2, 0, 0, 0)
        pixels = b"".join(b"\x00" + b"\x00\x00\x00" * 1200 for _ in range(627))
        return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(pixels)) + chunk(b"IEND", b"")

    def arguments(self) -> dict:
        return {"title": "Work and system-learning loops", "takeaway": "Evidence closes work; measured outcomes improve the system.",
                "lanes": (("Durable work", "Bounded authority", "Verified outcome"),), "renderer": Path("/synthetic/sips")}

    def test_render_invokes_bounded_atomic_contract(self) -> None:
        source = thumbs.ROOT / "diagrams" / "chapter-01" / "two-coupled-loops.light.svg"
        def run(command, **kwargs):
            Path(command[-1]).write_bytes(self.png())
            return mock.Mock(returncode=0)
        with mock.patch.object(thumbs.subprocess, "run", side_effect=run) as invoked:
            thumbs.render_thumbnail(source, self.output, **self.arguments())
        command = invoked.call_args.args[0]
        self.assertEqual(command[:4], ["/synthetic/sips", "-s", "format", "png"])
        self.assertEqual(invoked.call_args.kwargs["timeout"], 15)
        self.assertEqual(self.output.read_bytes(), self.png())

    def test_rejects_bad_inputs_and_renderer_failure(self) -> None:
        source = thumbs.ROOT / "diagrams" / "chapter-01" / "two-coupled-loops.light.svg"
        with self.assertRaisesRegex(thumbs.ThumbnailRenderError, "repository light-theme"):
            thumbs.render_thumbnail(Path(__file__), self.output, **self.arguments())
        with self.assertRaisesRegex(thumbs.ThumbnailRenderError, "3–72"):
            thumbs.render_thumbnail(source, self.output, **(self.arguments() | {"title": "[]"}))
        with self.assertRaisesRegex(thumbs.ThumbnailRenderError, "rendered-width"):
            thumbs.render_thumbnail(source, self.output, **(self.arguments() | {"title": "W" * 40}))
        with self.assertRaisesRegex(thumbs.ThumbnailRenderError, "rendered-width"):
            thumbs.render_thumbnail(source, self.output, **(self.arguments() | {"lanes": (("W" * 22, "Second", "Third", "Fourth"),)}))
        with self.assertRaisesRegex(thumbs.ThumbnailRenderError, "overwrite"):
            thumbs.render_thumbnail(source, source, **self.arguments())
        with mock.patch.object(thumbs.subprocess, "run", return_value=mock.Mock(returncode=1)):
            with self.assertRaisesRegex(thumbs.ThumbnailRenderError, "failed"):
                thumbs.render_thumbnail(source, self.output, **self.arguments())

    def test_timeout_invalid_and_stale_output_fail_closed(self) -> None:
        source = thumbs.ROOT / "diagrams" / "chapter-01" / "two-coupled-loops.light.svg"
        self.output.write_bytes(self.png())
        with mock.patch.object(thumbs.subprocess, "run", side_effect=subprocess.TimeoutExpired("sips", 15)):
            with self.assertRaisesRegex(thumbs.ThumbnailRenderError, "timed out"):
                thumbs.render_thumbnail(source, self.output, **self.arguments())
        self.assertEqual(self.output.read_bytes(), self.png())
        with mock.patch.object(thumbs.subprocess, "run", return_value=mock.Mock(returncode=0)):
            with self.assertRaisesRegex(thumbs.ThumbnailRenderError, "valid PNG"):
                thumbs.render_thumbnail(source, self.output, **self.arguments())
        def corrupt_run(command, **kwargs):
            data = bytearray(self.png())
            data[45] ^= 1
            Path(command[-1]).write_bytes(data)
            return mock.Mock(returncode=0)
        with mock.patch.object(thumbs.subprocess, "run", side_effect=corrupt_run):
            with self.assertRaisesRegex(thumbs.ThumbnailRenderError, "corrupt PNG"):
                thumbs.render_thumbnail(source, self.output, **self.arguments())

    def test_locator_and_cli_failure(self) -> None:
        with self.assertRaisesRegex(thumbs.ThumbnailRenderError, "renderer"):
            thumbs.locate_renderer(Path(self.directory.name) / "missing")
        stderr = io.StringIO()
        argv = ["render", "--source", "missing.svg", "--output", str(self.output), "--title", "Title",
                "--takeaway", "A valid takeaway", "--lane", "one", "two"]
        with mock.patch("sys.argv", argv), mock.patch.object(thumbs, "locate_renderer", side_effect=thumbs.ThumbnailRenderError("missing")), mock.patch("sys.stderr", stderr):
            self.assertEqual(thumbs.main(), 1)
        self.assertIn("render failed", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
