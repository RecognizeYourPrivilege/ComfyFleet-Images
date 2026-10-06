"""Impact bake contract for both instance images.

The manager app's host bind, chown, and prune behavior is not part of this
repo. These checks cover the Dockerfiles, pin files, and bake scripts the
images run.
"""

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACK = "429d0159ad429e64d2b3916e6e7be9c22d025c3c"
SUB = "50c7b71a6a224734cc9b21963c6d1926816a97f1"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ImpactBakeContractTests(unittest.TestCase):
    def test_both_dockerfiles_pin_the_same_impact_shas_and_keep_opencv(self):
        cu130 = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        cu124 = (ROOT / "Dockerfile.cu124").read_text(encoding="utf-8")
        pins = (ROOT / "docker" / "PINS.txt").read_text(encoding="utf-8")
        pins124 = (ROOT / "docker" / "PINS.cu124.txt").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        entry = (ROOT / "docker" / "entrypoint.sh").read_text(encoding="utf-8")
        for text in (cu130, cu124, pins, pins124):
            self.assertIn(PACK, text)
            self.assertIn(SUB, text)
        self.assertIn("ComfyUI-Impact-Pack", readme)
        self.assertIn("ComfyUI-Impact-Subpack", readme)
        self.assertNotIn(PACK, readme)
        self.assertNotIn(SUB, readme)
        for dockerfile in (cu130, cu124):
            self.assertIn("https://github.com/ltdrdata/ComfyUI-Impact-Pack.git", dockerfile)
            self.assertIn("https://github.com/ltdrdata/ComfyUI-Impact-Subpack.git", dockerfile)
            self.assertIn("opencv-python-headless==99.0.0", dockerfile)
            self.assertNotIn("opencv-python-headless<0", dockerfile)
            self.assertIn(
                "pip install --no-cache-dir --no-index --find-links /opt/comfyfleet/wheels "
                "'opencv-python-headless==99.0.0'",
                dockerfile,
            )
            self.assertIn("PIP_FIND_LINKS=/opt/comfyfleet/wheels", dockerfile)
            self.assertIn("opencv_headless_shim.py", dockerfile)
            self.assertNotIn("submodule update", dockerfile)
            self.assertIn("SAM2_BUILD_CUDA=0", dockerfile)
            self.assertIn("impact_bake.py", dockerfile)
            self.assertIn(
                "SAM2_BUILD_CUDA=0 pip install --no-cache-dir",
                dockerfile,
            )
            self.assertIn("--check-weights", dockerfile)
            self.assertIn("seed_impact_config.py", dockerfile)
            touch = dockerfile.index("touch /opt/comfyfleet/baked_custom_nodes/skip_download_model")
            install = dockerfile.index("ComfyUI-Impact-Pack/install.py")
            sub_install = dockerfile.index("ComfyUI-Impact-Subpack/install.py")
            remove = dockerfile.index("rm -f /opt/comfyfleet/baked_custom_nodes/skip_download_model")
            self.assertLess(touch, install)
            self.assertLess(install, sub_install)
            self.assertLess(sub_install, remove)
            self.assertLess(remove, dockerfile.index("--check-weights"))
        for name in ("ComfyUI-Impact-Pack", "ComfyUI-Impact-Subpack"):
            self.assertIn(f'link_baked "{name}"', entry)
            self.assertLess(entry.index(f'link_baked "{name}"'), entry.index("exec /opt/venv/bin/python main.py"))
        self.assertIn("/opt/comfyfleet/seed_impact_config.py", entry)
        self.assertLess(
            entry.index("/opt/comfyfleet/seed_impact_config.py"),
            entry.index("exec /opt/venv/bin/python main.py"),
        )
        script = (ROOT / "docker" / "verify_image_pins.py").read_text(encoding="utf-8")
        self.assertIn("opencv_python_headless", script)
        self.assertIn("import cv2", script)
        self.assertIn("RES4LYF/images.py", script)
        self.assertIn("ComfyUI-Impact-Pack/modules/impact/utils.py", script)

    def test_both_lines_build_sam2_against_the_installed_torch(self):
        cases = (
            ("Dockerfile", "2.13.0+cu130", "docker/PINS.txt"),
            ("Dockerfile.cu124", "2.6.0+cu124", "docker/PINS.cu124.txt"),
        )
        for name, torch_pin, pins_name in cases:
            text = (ROOT / name).read_text(encoding="utf-8")
            pins = (ROOT / pins_name).read_text(encoding="utf-8")
            section = text.split("python /opt/comfyfleet/impact_bake.py", 1)[1]
            section = section.split("impact_bake.py --check-weights", 1)[0]
            wheel_at = section.index(
                "pip install --no-cache-dir -c /opt/comfyfleet/torch-constraints.txt wheel 'setuptools>=70.1'"
            )
            probe_at = section.index("from setuptools.command.bdist_wheel import bdist_wheel")
            sam_at = section.index(
                "SAM2_BUILD_CUDA=0 pip install --no-cache-dir --no-build-isolation "
                "-c /opt/comfyfleet/torch-constraints.txt -r /tmp/impact-requirements.txt"
            )
            torch_at = section.index(
                'import importlib.metadata as metadata; assert metadata.version("torch") == '
                f'"{torch_pin}"'
            )
            sam2_import = section.index("import sam2")
            self.assertLess(wheel_at, probe_at, name)
            self.assertLess(probe_at, sam_at, name)
            self.assertLess(sam_at, torch_at, name)
            self.assertLess(torch_at, sam2_import, name)
            self.assertIn(f"torch=={torch_pin}", pins)
            self.assertIn("setuptools>=70.1", pins)
            self.assertIn("bdist_wheel", pins)
            self.assertIn("--no-build-isolation", pins)
        cu124_pins = (ROOT / "docker" / "PINS.cu124.txt").read_text(encoding="utf-8")
        self.assertIn("torchvision==0.21.0+cu124", cu124_pins)
        self.assertIn("torchaudio==2.6.0+cu124", cu124_pins)

    def test_requirement_filter_drops_headless_and_keeps_the_git_line(self):
        bake = _load(ROOT / "docker" / "impact_bake.py", "impact_bake")
        body = bake.merged_requirements(
            [
                "segment-anything\nopencv-python-headless\ngit+https://github.com/facebookresearch/sam2\n",
                "ultralytics>=8.3.162\nopencv-python-headless\nmatplotlib\n",
            ]
        )
        self.assertNotIn("opencv-python-headless", body)
        self.assertNotIn("opencv-python\n", body)
        self.assertIn("git+https://github.com/facebookresearch/sam2", body)
        self.assertIn("ultralytics>=8.3.162", body)
        self.assertIn("segment-anything", body)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sam_vit_b_01ec64.pth").write_bytes(b"weight")
            with self.assertRaises(SystemExit) as ctx:
                bake.assert_no_weight_files([root])
            self.assertIn("sam_vit_b", str(ctx.exception))
            (root / "sam_vit_b_01ec64.pth").unlink()
            bake.assert_no_weight_files([root])

    def test_opencv_distribution_check_allows_only_the_placeholder(self):
        verify = _load(ROOT / "docker" / "verify_image_pins.py", "verify_image_pins_impact")
        shim = verify.HEADLESS_SHIM_VERSION
        self.assertEqual(
            verify.opencv_distribution_errors(
                {"opencv_python": "5.0.0.93", "opencv_python_headless": shim}
            ),
            [],
        )
        errors = verify.opencv_distribution_errors(
            {"opencv_python": "5.0.0.93", "opencv_python_headless": "5.0.0.93"}
        )
        self.assertTrue(any("headless" in item for item in errors))
        missing_shim = verify.opencv_distribution_errors({"opencv_python": "5.0.0.93"})
        self.assertTrue(any("placeholder" in item for item in missing_shim))
        missing = verify.opencv_distribution_errors({})
        self.assertTrue(any("opencv-python is not installed" in item for item in missing))


if __name__ == "__main__":
    unittest.main()
