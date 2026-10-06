"""Publish script and workflow for the two instance images."""

import stat
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IMAGE = "ghcr.io/recognizeyourprivilege/comfyfleet-images"
LEGACY_CLEANUP = "docker rmi ghcr.io/recognizeyourprivilege/comfyfleet-manager-legacy"


class PublishScriptTests(unittest.TestCase):
    def test_publish_script_pushes_both_instance_lines(self):
        script = ROOT / "scripts" / "publish-images.sh"
        text = script.read_text(encoding="utf-8")
        self.assertTrue(script.stat().st_mode & stat.S_IXUSR, "publish-images.sh must be executable")
        self.assertIn("Dockerfile.cu124", text)
        self.assertIn("linux/amd64", text)
        self.assertIn("comfyfleet-images:cu130", text)
        self.assertIn("comfyfleet-images:cu124", text)
        self.assertIn("${sha}-cu130", text)
        self.assertIn("${sha}-cu124", text)
        self.assertIn("comfy_kitchen", text)
        self.assertIn("write:packages", text)
        self.assertIn("org.opencontainers.image.source=${source_url}", text)
        self.assertIn("https://github.com/RecognizeYourPrivilege/ComfyFleet-Images", text)
        self.assertNotIn("Dockerfile.manager", text)
        self.assertNotIn("comfyfleet-manager-legacy", text)
        self.assertNotIn(":phase1", text)
        self.assertNotIn(":latest", text)
        self.assertNotRegex(text, r"ghcr\.io/<owner>/comfyfleet:")
        self.assertNotRegex(text, r"ghcr\.io/\$\{owner\}/comfyfleet:")
        checked = subprocess.run(
            ["bash", "-n", str(script)],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(checked.returncode, 0, checked.stderr)
        help_run = subprocess.run(
            ["bash", str(script), "--help"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(help_run.returncode, 0, help_run.stderr)
        self.assertIn("comfyfleet-images:cu130", help_run.stdout)
        self.assertIn("comfyfleet-images:cu124", help_run.stdout)
        self.assertNotIn("comfyfleet-manager-legacy", help_run.stdout)
        self.assertNotIn("phase1", help_run.stdout)

    def test_workflow_builds_both_images_and_frees_disk(self):
        text = (ROOT / ".github" / "workflows" / "publish-images.yml").read_text(encoding="utf-8")
        self.assertIn("dockerfile: Dockerfile\n", text)
        self.assertIn("dockerfile: Dockerfile.cu124\n", text)
        self.assertNotIn("Dockerfile.manager", text)
        self.assertIn("packages: write", text)
        self.assertIn("linux/amd64", text)
        self.assertIn("cuda_tag: cu130", text)
        self.assertIn("cuda_tag: cu124", text)
        self.assertIn(":cu130", text)
        self.assertIn(":cu124", text)
        self.assertIn("${GITHUB_SHA}-${cuda_tag}", text)
        self.assertNotIn(":phase1", text)
        self.assertNotIn(":latest", text)
        self.assertNotIn("comfyfleet-manager-legacy", text)
        self.assertIn('echo "image=ghcr.io/${owner}/comfyfleet-images"', text)
        self.assertNotRegex(text, r'echo "image=ghcr\.io/\$\{owner\}/comfyfleet"')
        self.assertIn("provenance: false", text)
        self.assertIn("org.opencontainers.image.source=https://github.com/${{ github.repository }}", text)
        self.assertIn("ubuntu-24.04", text)
        self.assertIn("timeout-minutes: 180", text)
        self.assertIn("Free runner disk", text)
        self.assertIn("/opt/hostedtoolcache", text)
        self.assertIn("docker builder prune -af", text)
        self.assertIn("No GPU", text)
        self.assertIn("actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1", text)


class ReadmeContractTests(unittest.TestCase):
    def test_readme_matches_the_install_and_cleanup_contract(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(
            "curl -fsSL https://raw.githubusercontent.com/RecognizeYourPrivilege/ComfyFleet-Manager/main/install.sh "
            "| COMFYFLEET_PASSWORD='your-password' COMFYFLEET_PUBLIC_HOST=<ip-address> bash -s -- --with-images cu130",
            readme,
        )
        self.assertIn("COMFYFLEET_PUBLIC_HOST=<ip-address>`: use `0.0.0.0` or the machine's LAN IP.", readme)
        self.assertIn(f"docker pull {IMAGE}:cu130", readme)
        self.assertIn(f"docker pull {IMAGE}:cu124", readme)
        self.assertIn(LEGACY_CLEANUP, readme)
        self.assertEqual(readme.count("comfyfleet-manager-legacy"), 1)
        self.assertNotIn("192.168.", readme)
        self.assertNotRegex(readme, r"ghcr\.io/recognizeyourprivilege/comfyfleet:")
        self.assertIn("docker build -f Dockerfile -t ghcr.io/recognizeyourprivilege/comfyfleet-images:cu130 .", readme)
        self.assertIn("docker build -f Dockerfile.cu124 -t ghcr.io/recognizeyourprivilege/comfyfleet-images:cu124 .", readme)
        self.assertIn("The build does not need a GPU.", readme)


if __name__ == "__main__":
    unittest.main()
