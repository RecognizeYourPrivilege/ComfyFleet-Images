# ComfyFleet Images

ComfyUI instance images for ComfyFleet, tagged `cu130` and `cu124`.

## Install with Docker

Requirements: an NVIDIA driver that matches the tag (CUDA 13.0 for `cu130`, CUDA 12.4 for `cu124`), the NVIDIA Container Toolkit, and Docker.

ComfyFleet Manager no longer pulls instance images by default.

```bash
curl -fsSL https://raw.githubusercontent.com/RecognizeYourPrivilege/ComfyFleet-Manager/main/install.sh | COMFYFLEET_PASSWORD='your-password' COMFYFLEET_PUBLIC_HOST=<ip-address> bash -s -- --with-images cu130
```

`COMFYFLEET_PUBLIC_HOST=<ip-address>`: use `0.0.0.0` or the machine's LAN IP.

`cu124`: `--with-images cu124`. Both tags: `--with-images both`.

```bash
docker pull ghcr.io/recognizeyourprivilege/comfyfleet-images:cu130
docker pull ghcr.io/recognizeyourprivilege/comfyfleet-images:cu124
```

## Update

```bash
docker pull ghcr.io/recognizeyourprivilege/comfyfleet-images:cu130
```

Use `:cu124` for that line.

## Free up space

Remove an old tag of this image. This does not delete host files or volumes. Docker refuses while a container is still using the tag.

```bash
docker rmi ghcr.io/recognizeyourprivilege/comfyfleet-images:cu130
```

Remove dangling image layers left after a pull or rebuild. Tagged images stay.

```bash
docker image prune -f
```

Remove the Docker build cache. The next build downloads its layers again. Containers, tagged images, and volumes stay.

```bash
docker builder prune -af
```

Remove stopped containers. This deletes their writable layer. Data that exists only inside a stopped container is gone. Host bind mounts and named volumes are kept.

```bash
docker container prune -f
```

After switching, remove the legacy manager image: `docker rmi ghcr.io/recognizeyourprivilege/comfyfleet-manager-legacy`

## Features

- `cu130` for CUDA 13.0 drivers and `cu124` for CUDA 12.4 drivers.
- ComfyUI with PyTorch, ready to run on an NVIDIA GPU.
- Baked custom nodes: ComfyUI-Manager, ComfyUI-Pixaroma, ComfyUI-ComfyDock, RES4LYF, ComfyUI-Impact-Pack, ComfyUI-Impact-Subpack, and comfyfleet_default_workflow.
- llama-cpp-python for JoyCaption, installed from a prebuilt wheel.
- Listens on port 8188 and refuses to start without the operator workflow file.
- Links the baked nodes at startup and lets ComfyUI-Manager install missing nodes.

## Build your own

The build does not need a GPU.

```bash
docker build -f Dockerfile -t ghcr.io/recognizeyourprivilege/comfyfleet-images:cu130 .
docker build -f Dockerfile.cu124 -t ghcr.io/recognizeyourprivilege/comfyfleet-images:cu124 .
```
