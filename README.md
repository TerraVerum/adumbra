# adumbra
Web based coco annotation platform

This work builds on [coco-annotator](https://github.com/jsbroks/coco-annotator) and [coco-annotator-ng](https://github.com/SixK/coco-annotator-ng) projects. Many thanks to their authors!

## Installation
Start by cloning the repository:
```bash
git clone https://github.com/TerraVerum/adumbra.git
```

Adumbra is a dockerized application. You can get a minimal setup running by executing the following command in the root directory of the repository:
```bash
docker compose up --build
```
This will expose the application on http://localhost:8080.

> [!IMPORTANT]
> We use [`include`](https://docs.docker.com/compose/how-tos/multiple-compose-files/include/) to manage different configurations with minimal code duplication, which requires **Docker Composer 2.20.3** or later.

## Configuration
### Segmentation models
You can optionally run SAM2 and/or Zim segmentation models on either the CPU or GPU. First, run the installation scripts to ensure the weights are available on your system:
```bash
cd models
# Run either or both commands below
# For zim
./zim_model.sh
# For sam2
./sam2_model.sh
```

Next, pass the desired docker profile profiles on startup:
```bash
docker compose -f docker-compose.yml --profile ia-gpu up --build
# Or ia-cpu profile, but not both at once
```

> [!IMPORTANT]
> GPU models currently only expose cuda 0, so you may need to adjust [`ia-gpu.yml`](compose-extensions/ia-gpu.yml) to match your system.

### Development mode
To run the application in development mode, you can use the following command:
```bash
# Optionally use ia-cpu instead
docker compose \
    -f docker-compose.yml \
    -f compose-extensions/ia-gpu.yml \
    -f compose-extensions/dev-environment.yml \
    up --build
```

In contrast to the main build, this will enable hot reloading of frontend code, and read image files from `./datasets` instead of the docker volume `datasets`.
