# Licenses and third-party notices (dropsort)

## Project code

Application source in this repository is under the license stated in the root **LICENSE** file. Update the copyright year and authors there when the submission roster is final.

## RVL-CDIP dataset (academic / research)

Training and evaluation reference the **RVL-CDIP** document image dataset (Ryerson Vision Lab / Competing Approaches to **Document Image Classification**). Usage is subject to the dataset’s **academic / research** terms — obtain and follow the **official license and citation** from the dataset maintainers before redistributing images beyond this course context.

**Disclaimer:** This file is for project documentation only and is not legal advice.

## Golden evaluation images

The directory `app/classifier/eval/golden_images/` contains a fixed subset of TIFFs used only for **deterministic regression testing** (`golden.py`). They are subject to the same RVL-CDIP terms as the training data.

## Third-party software (non-exhaustive)

Backend and frontend depend on open-source packages listed in:

- `pyproject.toml` / `uv.lock` — notable stacks: **FastAPI**, **SQLAlchemy**, **Alembic**, **Casbin**, **Redis**, **hvac**, **torch**, **torchvision**, **Pillow**, **MinIO client**, **fastapi-users**, **RQ**.
- `frontend/package.json` / `package-lock.json` — **React**, **Vite**, **TypeScript**, router, testing libs.

## Container images

Compose references upstream images (PostgreSQL, Redis, Vault, MinIO, SFTP, nginx, Node build stage). Each is governed by its vendor’s license.

## Model weights (`classifier.pt`)

- **File:** `app/classifier/models/classifier.pt` — tracked with **Git LFS** (see `.gitattributes`).
- **Provenance:** Produced from the training notebook under `notebook/`; metadata in **`model_card.json`** (metrics, SHA-256 of weights, backbone).
- **License:** Model weights inherit **dataset and code** terms used during training; document any additional restrictions imposed by course staff.
