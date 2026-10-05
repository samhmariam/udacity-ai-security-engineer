# Supply Chain Vulnerability Analysis

**Artifacts analyzed:**
- `06_trivy_report.json`: Trivy scan of image `offensive-ai-course` (Debian 13.4), created 2026-03-18
- `Dockerfile`
- Supplementary: `pip-audit` of the pinned `requirements.txt`, run 2026-10-05; see [Python-Specific Vulnerabilities](#python-specific-vulnerabilities)

**Script output:** `../attacks/results/05_supply_chain/supply_chain_report.json` (`python 05_supply_chain_analysis.py`)

**Overall risk: HIGH.** The script rates the image HIGH because it has 34 HIGH CVEs and a HIGH Dockerfile issue. Reading the findings in context gives the same rating for different reasons. Most of the scanner's HIGH findings are not exploitable at runtime. The real risk comes from:
- the API key baked into the image,
- the container running as root,
- a remote-code-execution (RCE) bypass in the model-loading library that Trivy did not report.

## Vulnerability Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 34 |
| MEDIUM | 160 |
| LOW | 601 |
| UNKNOWN | 9 |
| **Total** | **804** (357 unique CVEs across 62 packages) |

| Scan target | Findings | HIGH |
|---|---|---|
| OS packages: `offensive-ai-course (debian 13.4)` | 801 | 31 |
| Python packages (`python-pkg`) | 3 | 3 |

**Only 3 of 804 findings (0.4%) have a fixed version available**, and they are the 3 Python findings. Every OS finding is either `affected` with no Debian fix yet (799), `fix_deferred` (1) or `will_not_fix` (1). So **patching cannot reduce this image's OS risk. Only removing packages can.**

### Where the findings come from

Grouping findings by package shows that **the Dockerfile's `apt-get install build-essential gcc curl git` line accounts for most of the attack surface.** The count below includes only packages that are certainly not in the `python:3.11-slim` base image, so it is a conservative lower bound.

| Source (installed by the Dockerfile) | Packages | Findings | HIGH |
|---|---|---|---|
| `build-essential` / `gcc` toolchain | `linux-libc-dev`, `binutils*`, `libctf*`, `libgprofng0`, `libsframe1`, `libjansson4`, `libc6-dev`, `libc-dev-bin`, `patch` | 657 | 30 |
| `curl` | `curl`, `libcurl4t64` | 22 | 0 |
| `git` (+ `perl`, `libcurl3t64-gnutls`) | `git`, `git-man`, `perl`, `perl-modules-5.40`, `libperl5.40`, `libcurl3t64-gnutls` | 20 | 0 |
| **Subtotal: removable** | | **699 of 801 OS findings (87%)** | **30 of 31 OS HIGH** |
| Base image (`python:3.11-slim`) | `libc6`, `libexpat1`, `util-linux`, `systemd` libs, … | 102 | 1 (`libexpat1`) |

All 9 UNKNOWN findings are also in `linux-libc-dev`.

## High Severity Findings

| CVE | Package (installed) | Fixed Version | Description | Remediation |
|-----|---------|--------------|-------------|-------------|
| CVE-2026-24049 | `wheel` 0.45.1 (two copies: top-level and vendored in `setuptools/_vendor`) | **0.46.2** | Malicious wheel file can change file permissions on unpack, leading to privilege escalation or code execution | `pip install --upgrade wheel setuptools`, or drop `wheel`/`setuptools` from the runtime stage entirely |
| CVE-2026-23949 | `jaraco.context` 5.3.0 (vendored in `setuptools`) | **6.1.0** | Zip Slip path traversal in `tarball()`: a crafted tar can write files outside the target directory | Upgrade `setuptools` (which vendors it) |
| CVE-2026-25210 | `libexpat1` 2.7.1-2 | none yet | Integer overflow leading to information disclosure and data-integrity issues in the XML parser | Base-image package used by Python's `pyexpat`. Track Debian's fix and rebuild on a newer digest. Avoid parsing untrusted XML |
| CVE-2021-3847 | `linux-libc-dev` 6.12.74-2 | none | Low-privileged user privilege escalation (OverlayFS) | Remove the toolchain (multi-stage build) |
| CVE-2026-23231 | `linux-libc-dev` 6.12.74-2 | none | Use-after-free in `nf_tables`: privilege escalation or DoS | Remove the toolchain (multi-stage build) |
| CVE-2026-23171 | `linux-libc-dev` 6.12.74-2 | none | Use-after-free in the bonding module: crash or arbitrary code execution | Remove the toolchain (multi-stage build) |
| CVE-2021-3864 | `linux-libc-dev` 6.12.74-2 | none | Descendant's dumpable setting with SUID binaries | Remove the toolchain (multi-stage build) |
| + 27 more | `linux-libc-dev` 6.12.74-2 | none | Kernel CVEs (f2fs, Bluetooth, Wi-Fi drivers, PCI, ipv6, ksmbd, …) | Remove the toolchain (multi-stage build) |

**Context for the 30 `linux-libc-dev` findings:**
- **They are not exploitable inside the container.** `linux-libc-dev` contains only kernel *header files*, used to compile C code. A container runs on the **host's** kernel, so these CVEs describe bugs in code that isn't running in the image.
- **They are still real findings.** They inflate the image's risk score, will fail any "zero HIGH" deployment gate, and show that a full compiler toolchain ships to production.
- **The fix is removal, not patching.** A multi-stage build makes all 30 disappear. Separately, the *host* kernel should be patched against these CVEs, because a root container (see Dockerfile issue 1) is a good starting point for exploiting them.

## Python-Specific Vulnerabilities

### From the Trivy report (3)

| CVE | Package | Path | Fix |
|---|---|---|---|
| CVE-2026-24049 | `wheel` 0.45.1 | `site-packages/wheel-0.45.1.dist-info` | 0.46.2 |
| CVE-2026-24049 | `wheel` 0.45.1 | `site-packages/setuptools/_vendor/wheel-0.45.1.dist-info` | 0.46.2 |
| CVE-2026-23949 | `jaraco.context` 5.3.0 | `site-packages/setuptools/_vendor/jaraco.context-5.3.0.dist-info` | 6.1.0 |

All three come from **packaging tooling that ships with the base image** (`setuptools`, `wheel`), not from the application. They matter mainly at *install time*: they are exploitable if the container ever installs an untrusted wheel or tarball. That is another reason not to ship packaging tools in the runtime image.

### Gap: Trivy did not report the application's dependencies

Trivy found **no** findings for any package in `requirements.txt` (torch, Pillow, flask, requests, …). Either those packages were not in the scanned image, or Trivy did not detect them. In either case, **the scan does not cover the code that actually runs the AI system.** To close the gap, the pinned requirements were audited directly:

```bash
uvx --python 3.12 pip-audit -r requirements.txt --no-deps
```

| Package (pinned) | Advisories | Most relevant | Fix |
|---|---|---|---|
| **`torch` 2.5.1** | 19 | **CVE-2025-32434**: RCE via `torch.load()` **even with `weights_only=True`**. Others include several `torch.jit`/compiler memory-corruption issues and DoS bugs | ≥ 2.6.0 for CVE-2025-32434; ≥ 2.10.0 clears most of the rest (4 have no fix yet) |
| **`Pillow` 11.0.0** | 17 | Out-of-bounds writes and heap overflows in image decoders (CVE-2026-25990, CVE-2026-59199, CVE-2026-59204 in JPEG2000, among others) and decompression-bomb DoS (CVE-2026-40192) | 12.3.0 |
| `requests` 2.32.3 | 2 | CVE-2024-47081: `.netrc` credentials leaked to third parties through URL parsing | 2.33.0 |
| `flask` 3.0.3 | 1 | CVE-2026-27205 | 3.1.3 |
| `python-dotenv` 1.0.1 | 1 | CVE-2026-28684 | 1.2.2 |
| torchvision, torchaudio, numpy, scikit-learn, matplotlib, faiss-cpu, openai, httpx | 0 | | |

These two are **the most important findings in this analysis for the AI system**:
- **`torch` CVE-2025-32434** directly defeats the safety measure the classifier relies on. `evaluate.py`, `predict.py` and the attack scripts load checkpoints with `torch.load(..., weights_only=True)`, which is meant to make loading an untrusted `.pt` file safe. On torch 2.5.1 it does not: a crafted checkpoint can execute code.
- **`Pillow`** decodes every image the receipt classifier receives. Its memory-corruption bugs are reachable with attacker-supplied image files.

Also note that `requirements.txt` pins only top-level packages, **without hashes**. Transitive dependencies (werkzeug, jinja2, urllib3, sympy, …) resolve to whatever version is newest at build time.

## Dockerfile Issues

The script found all 6 checked issues. The `Dockerfile` it analyzed:

```dockerfile
FROM python:3.11-slim
...
RUN apt-get update && apt-get install -y --no-install-recommends build-essential gcc curl git && rm -rf /var/lib/apt/lists/*
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt
COPY . /app
EXPOSE 5001
CMD ["python", "rag_chatbot/app.py"]
```

### 1. Container runs as root (no USER directive) — HIGH

**Risk:** The Flask app runs as UID 0. Any code execution, whether through a Flask/Werkzeug bug, a malicious checkpoint (torch CVE-2025-32434), a crafted image (Pillow) or a tampered pickle (see the AI pipeline section), gives the attacker **root inside the container**. Root can:
- rewrite the model checkpoint, FAISS index and policy documents in place,
- read every secret in the filesystem,
- use any added capabilities or mounted sockets,
- attempt kernel exploits against the host far more easily.

The app also binds to `0.0.0.0:5001` with no authentication, so the code running as root is directly reachable from the network.

**Fix:**
```dockerfile
RUN useradd --create-home --uid 10001 app
COPY --chown=app:app rag_chatbot/ ./rag_chatbot/
USER app
```
At deploy time, also run with a read-only root filesystem, `--cap-drop=ALL` and `no-new-privileges`.

### 2. Base image not pinned to a SHA256 digest — MEDIUM

**Risk:** `FROM python:3.11-slim` is a mutable tag. Every build can pull a different image, so builds are not reproducible, and the scanned image is not necessarily the one deployed. If an upstream account is compromised or the tag is re-pushed, malicious content goes straight into production.

**Fix:** Pin the digest, e.g. `FROM python:3.11-slim@sha256:<digest>`. Let Dependabot or Renovate raise PRs that bump it, and scan each new digest in CI before merging.

### 3. COPY . copies entire build context (possible secret leakage) — MEDIUM (rated HIGH in this context)

**Risk:** `COPY . /app` with **no `.dockerignore`** copies everything in the build context into an image layer. The script found **`rag_chatbot/.env` in the context, and it contains the live `OPENAI_API_KEY` and `OPENAI_BASE_URL`**. Anyone who can pull the image, from a registry, a CI cache or a developer laptop, can extract the key with `docker save` or `docker history`. Deleting the file in a later layer does not remove it. The copy would also include:
- `.git` history,
- training datasets (`balanced_data/`, `poisoned_data/`),
- every checkpoint, including the poisoned ones from Attack 2.

The rubric rates this MEDIUM. Because a real credential is confirmed to be in the context, this assessment rates the practical impact **HIGH**.

**Fix:**
- Add a `.dockerignore` containing at least `.env`, `**/.env`, `.git`, `**/__pycache__`, `*.pt`, `**/balanced_data`, `**/poisoned_data`, `attacks/` and `doc_delivery/`.
- Replace `COPY . /app` with explicit copies of what the service needs (`rag_chatbot/*.py`, `rag_chatbot/faiss_index/`).
- Inject the API key at runtime from a secret store (Kubernetes Secret, Docker secret or a cloud secret manager).
- **Rotate the key** if an image built from this Dockerfile was ever pushed anywhere.

### 4. No HEALTHCHECK defined — LOW

**Risk:** Orchestrators cannot tell a hung or crashed service from a healthy one. Outages, and a process replaced or killed by an attacker, can go unnoticed. The app already has a `/health` endpoint that nothing uses.

**Fix:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5001/health')" || exit 1
```
This uses Python rather than curl, so curl can be removed (issue 6).

### 5. Build tools left in production image — MEDIUM

**Risk:** `build-essential` and `gcc` stay in the single runtime stage. A compiler and linker on the box let an attacker build exploits and tooling in place. As shown above, the toolchain also accounts for **657 findings, including 30 of the 34 HIGH CVEs**.

**Fix:** Use a multi-stage build:
```dockerfile
FROM python:3.11-slim@sha256:<digest> AS builder
RUN apt-get update && apt-get install -y --no-install-recommends build-essential
COPY requirements.txt .
RUN pip wheel --require-hashes --wheel-dir /wheels -r requirements.txt

FROM python:3.11-slim@sha256:<digest>
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --no-index /wheels/* && rm -rf /wheels
# ... USER, COPY app, HEALTHCHECK, CMD
```
Every pinned dependency ships prebuilt wheels for this platform, so the compiler is probably not needed at all.

### 6. Unnecessary tools in production image — LOW

**Risk:** `curl` and `git` serve no runtime purpose. After compromise they give an attacker ready-made tools to download payloads, exfiltrate data such as the FAISS index, model weights or `.env`, and clone tooling. Together with their dependencies (perl, libcurl) they add **42 findings**.

**Fix:** Remove both from the runtime stage. Use the Python-based HEALTHCHECK above. If git is needed for a VCS dependency, use it only in the builder stage.

### Additional observations (not in the script's checklist)

- `pip install --upgrade pip` installs whatever pip version is newest at build time, which makes the build non-reproducible. Pin it.
- `pip install -r requirements.txt` runs without `--require-hashes`, so a compromised or substituted package on the index would be accepted (see dependency confusion below).
- The image runs `python rag_chatbot/app.py`, Flask's built-in development server. Use a production WSGI server (gunicorn or uwsgi) behind a reverse proxy.

## AI Pipeline Risk Assessment

The traditional CVE and configuration findings above become AI-specific risks once you trace what an attacker could do to the **models and data** behind FinanceGuard's decisions.

1. **Model integrity: checkpoints can be swapped or weaponized.**
   - `receipt_cnn_clean.pt` is loaded with no signature or hash check. A process running as root can overwrite it.
   - Attack 2 showed that a model retrained on quietly poisoned data looks normal on precision. A swapped checkpoint would be just as hard to notice.
   - On torch 2.5.1, `weights_only=True` does not protect against a malicious checkpoint (CVE-2025-32434). **Loading the model file becomes a code-execution path.**
   - *Fix:* upgrade torch to 2.6.0 or later. Store checkpoints in a read-only, access-controlled artifact store, verify a SHA-256 hash or signature (e.g. Sigstore/cosign or model-signing) before loading, and mount model files read-only into a non-root container. Prefer `safetensors` over pickle-based `.pt`.

2. **RAG index integrity: the pickle file is a code-execution path, and the index decides what the bot says.**
   - `load_index.py` restores chunk metadata with `pickle.load(chunks.pkl)`. **Unpickling a tampered file runs arbitrary code.** Anyone who can write to `faiss_index/` (root in the container, CI, or the build context via `COPY .`) can get code execution when the chatbot starts.
   - Without code execution, an attacker who edits `chunks.pkl` or `policy.index` controls what the chatbot "knows". They could plant false policies, or insert prompt-injection payloads into retrieved context. That is an *indirect* injection, which avoids the user-input path the model resisted in Attack 3.
   - Attack 4 showed that the index already mixes restricted and public data with no controls.
   - *Fix:* replace pickle with JSON or Parquet for chunk metadata. Build the index in CI from reviewed source documents, sign or hash the output, verify it at startup, and mount it read-only.

3. **Dependency security: dependency confusion and typosquatting.**
   - `requirements.txt` pins top-level versions but **not hashes**, and leaves transitive dependencies unpinned. `pip install` resolves against public PyPI.
   - If FinanceGuard ever adds an internal package, or uses `--extra-index-url` for a private index, an attacker could publish a same-named package with a higher version on PyPI and pip may prefer it (dependency confusion). A misspelled name (`pytorch`, `faiss`, `openai-python`) would install whatever owns that name.
   - ML stacks are attractive targets because packages often run native code at import time. The December 2022 compromise of the `torchtriton` nightly dependency is a real example aimed at exactly this stack.
   - *Fix:* fully pin with hashes (`pip-compile --generate-hashes`, `uv pip compile --generate-hashes`) and install with `--require-hashes`. Use a single trusted index or proxy (Artifactory or a private PyPI mirror) with an allowlist, and never use `--extra-index-url`. Run `pip-audit` in CI, because Trivy did not see these packages here.

4. **Input-processing attack surface.**
   - The receipt classifier decodes untrusted, user-uploaded images with Pillow 11.0.0, which has 17 advisories, several of them heap out-of-bounds writes.
   - A crafted "receipt" is therefore both an evasion vector (Attack 1, FGSM) and a potential memory-corruption vector, with the decoder running as root.
   - *Fix:* upgrade to Pillow 12.3.0, restrict accepted formats (for example JPEG and PNG only, rejecting PSD, PDF, JPEG2000 and font formats), enforce size limits, and decode in a sandboxed low-privilege process.

5. **Secrets and runtime privileges: the LLM credential.**
   - The OpenAI-compatible API key baked into the image (Dockerfile issue 3) is enough for an attacker to run up usage costs, use the account for their own purposes, or pull data sent to the provider.
   - Combined with root, unauthenticated `0.0.0.0:5001` and curl in the image, **one exploitable bug leads directly to stolen credentials and exfiltration.**
   - *Fix:* inject secrets at runtime with least privilege, scope and rotate the key, run as non-root with a read-only filesystem and no added capabilities, and limit outbound network traffic to the LLM endpoint.

**Overall:** the image is rated **HIGH** risk. The scanner's HIGH count is mostly noise from unpatched kernel headers. The real risk is a chain of findings that the scanner either under-weights or misses entirely:
- secrets baked into the image,
- root execution,
- RCE paths in model loading (torch) and index loading (pickle),
- an unauthenticated network listener.

Each of these is fixable with standard controls, and the first three priorities below remove most of the risk.

## Remediation Priority

| Priority | Action | Addresses |
|----------|--------|-----------|
| 1 | **Add `.dockerignore` (exclude `.env`, `.git`, datasets, `*.pt`), replace `COPY .` with explicit copies, inject the API key at runtime, and rotate the key** if any image was pushed | Credential exposure (Dockerfile issue 3) |
| 2 | **Upgrade `torch` to ≥ 2.6.0 (ideally ≥ 2.10.0) and `Pillow` to ≥ 12.3.0.** Also upgrade `requests` 2.33.0, `flask` 3.1.3, `python-dotenv` 1.2.2, `wheel` 0.46.2 and `setuptools` | Model-loading RCE (CVE-2025-32434), image-decoder memory corruption, all 3 Trivy Python HIGHs |
| 3 | **Run as non-root** (`USER app`), read-only root filesystem, `--cap-drop=ALL`, `no-new-privileges`; require authentication on `/chat` | Privilege escalation and impact of any RCE (issue 1) |
| 4 | **Multi-stage build** with no `build-essential`/`gcc`/`curl`/`git` in the runtime image | Removes about 699 of 801 OS findings, including 30 of 31 OS HIGH (issues 5, 6) |
| 5 | **Integrity controls for AI artifacts:** hash or sign checkpoints and the FAISS index, verify before loading, mount read-only, replace `pickle` with a safe format, move to `safetensors` | Model and index tampering, pickle RCE |
| 6 | **Lock dependencies with hashes** (`--require-hashes`), pin pip and transitive dependencies, use a single trusted index or proxy; add `pip-audit` and Trivy to CI with a fail-on-HIGH gate for *fixable* findings | Dependency confusion and typosquatting; scanner coverage gap |
| 7 | **Pin the base image by digest** with automated update PRs, and add a `HEALTHCHECK` | Reproducibility, upstream compromise, monitoring (issues 2, 4) |
| 8 | Track `libexpat1` CVE-2026-25210 and rebuild when Debian ships a fix; patch the **host** kernel for the kernel CVEs | Remaining base-image HIGH; host-side exposure |

## Method Notes

- Severity counts and the CVE list come from `05_supply_chain_analysis.py` and reconcile exactly with the raw report: 804 findings = 801 OS + 3 Python.
- The breakdown of findings by Dockerfile-installed package was calculated separately from the raw report's package names. It counts only packages that are certainly not in `python:3.11-slim`, so the 699 figure is a lower bound. Package attribution is by name and was not confirmed by building the image.
- The `pip-audit` results reflect the pinned `requirements.txt` and the vulnerability databases as of 2026-10-05. They are *not* a scan of the image Trivy analyzed, which evidently did not contain these packages. Re-run both scanners against the actual production image before acting on exact counts.
- No image was built and no CVE was exploited, as required by the charter's rules of engagement.
