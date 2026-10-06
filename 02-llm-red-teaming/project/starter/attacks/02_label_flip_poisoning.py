"""
Label-Flip Data Poisoning Attack

Copies the balanced dataset and flips a percentage of training labels
(moves images between receipt/non_receipt folders) to degrade model accuracy.

Usage:
    python 02_label_flip_poisoning.py
    python 02_label_flip_poisoning.py --flip-rate 0.05
"""
import os
import shutil
import random
import argparse

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"}
CLASSES = ["receipt", "non_receipt"]
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results", "02_label_flip")
CLASSIFIER_DIR = os.path.join(os.path.dirname(__file__), "..", "classifier")
SELECTIONS = ["random", "confident", "boundary"]


def score_true_class_confidence(model_path, image_dir, cls, files):
    """
    Return {filename: confidence in its TRUE class} from the clean model.

    The model outputs P(receipt); confidence in the true class is P for
    receipt images and 1 - P for non_receipt images.
    """
    import sys
    import torch
    from PIL import Image

    sys.path.insert(0, CLASSIFIER_DIR)
    from model import ReceiptCNN
    from data import get_transform

    model = ReceiptCNN()
    model.load_state_dict(torch.load(model_path, map_location="cpu", weights_only=True))
    model.eval()
    transform = get_transform(train=False)

    scores = {}
    with torch.no_grad():
        for f in files:
            image = Image.open(os.path.join(image_dir, f)).convert("RGB")
            p_receipt = model(transform(image).unsqueeze(0)).item()
            scores[f] = p_receipt if cls == "receipt" else 1 - p_receipt
    return scores


def poison_dataset(source_root, target_root, flip_ratio=0.10, seed=42, source_class=None,
                   selection="confident", model_path=None):
    """
    Copy dataset and flip a percentage of training labels.

    Label flipping works by moving images between class folders:
    - A receipt image moved to non_receipt/ gets a flipped label
    - A non_receipt image moved to receipt/ gets a flipped label

    Only training labels are flipped — the test set stays clean so we can
    measure the true impact of poisoning on model performance.

    Args:
        source_root: Path to clean balanced dataset
        target_root: Path for poisoned dataset output
        flip_ratio: Fraction of training labels to flip (default 0.10 = 10%)
        seed: Random seed for reproducibility
        source_class: None flips flip_ratio of each class (symmetric). A class
            name ("receipt" or "non_receipt") spends the whole budget,
            flip_ratio of ALL training labels, on that class only (one-way).
        selection: How files to flip are chosen within each class:
            "random"    - uniform random sample (seeded)
            "confident" - images the clean model is MOST confident about
                          (the clearest, most prototypical examples)
            "boundary"  - images the clean model is LEAST confident about
                          (closest to the decision boundary)
            Targeted selections need model_path (the clean checkpoint).
        model_path: Clean model checkpoint used to score training images.
    """
    random.seed(seed)

    # Step 1: Copy the entire clean dataset to target
    if os.path.exists(target_root):
        shutil.rmtree(target_root)
    shutil.copytree(source_root, target_root)

    if not 0 <= flip_ratio <= 0.10:
        raise ValueError(f"flip_ratio must be in [0, 0.10], got {flip_ratio}")
    if source_class is not None and source_class not in CLASSES:
        raise ValueError(f"source_class must be one of {CLASSES} or None, got {source_class}")
    if selection not in SELECTIONS:
        raise ValueError(f"selection must be one of {SELECTIONS}, got {selection}")
    if selection != "random" and not model_path:
        raise ValueError(f"selection={selection!r} requires model_path")

    def list_images(directory):
        return sorted(
            f for f in os.listdir(directory)
            if os.path.isfile(os.path.join(directory, f))
            and os.path.splitext(f)[1].lower() in IMAGE_EXTENSIONS
        )

    # Only the TRAINING split is poisoned; the test set stays clean.
    train_root = os.path.join(target_root, "train")
    opposite = {"receipt": "non_receipt", "non_receipt": "receipt"}

    # Select files for every class before moving anything, so images moved
    # into a class folder can't be re-selected and flipped back.
    class_files = {cls: list_images(os.path.join(train_root, cls)) for cls in CLASSES}
    total_train = sum(len(files) for files in class_files.values())

    def pick(cls, n_flip):
        files = class_files[cls]
        if selection == "random":
            return random.sample(files, n_flip)
        scores = score_true_class_confidence(
            model_path, os.path.join(train_root, cls), cls, files
        )
        # Sort by confidence (filename breaks ties so the order is deterministic)
        ranked = sorted(files, key=lambda f: (scores[f], f),
                        reverse=(selection == "confident"))
        chosen = ranked[:n_flip]
        conf = [scores[f] for f in chosen]
        print(f"  {cls}: selected {n_flip} by '{selection}' "
              f"(true-class confidence {min(conf):.3f}-{max(conf):.3f})" if conf else "")
        return chosen

    to_flip = {}
    if source_class is None:
        for cls in CLASSES:
            to_flip[cls] = pick(cls, int(len(class_files[cls]) * flip_ratio))
    else:
        # Budget is a fraction of ALL training labels, so the overall rate
        # still stays <= flip_ratio.
        n_flip = min(int(total_train * flip_ratio), len(class_files[source_class]))
        to_flip[source_class] = pick(source_class, n_flip)

    total_flipped = 0
    for cls, files in to_flip.items():
        src_dir = os.path.join(train_root, cls)
        dst_dir = os.path.join(train_root, opposite[cls])
        for f in files:
            shutil.move(
                os.path.join(src_dir, f),
                os.path.join(dst_dir, f"flipped_{cls}_{f}"),
            )
        total_flipped += len(files)
        print(f"Flipped {len(files)} {cls} -> {opposite[cls]}")

    print(f"\nTotal training images: {total_train}")
    print(f"Labels flipped:        {total_flipped}")
    print(f"Actual flip rate:      {total_flipped / total_train:.4f}" if total_train else "")
    print("\nPoisoned dataset composition:")
    for split in ["train", "test"]:
        for cls in CLASSES:
            files = list_images(os.path.join(target_root, split, cls))
            n_flipped = sum(1 for f in files if f.startswith("flipped_"))
            print(f"  [{split}] {cls}: {len(files)} images ({n_flipped} flipped in)")


def visualize_flip(source_root, target_root, num_images=5, output_dir=RESULTS_DIR, seed=42):
    """Save a grid showing clean labels beside their flipped poisoned labels."""
    flipped_samples = []

    for poisoned_label in CLASSES:
        poisoned_dir = os.path.join(target_root, "train", poisoned_label)
        if not os.path.isdir(poisoned_dir):
            continue

        for filename in os.listdir(poisoned_dir):
            poisoned_path = os.path.join(poisoned_dir, filename)
            if (
                not os.path.isfile(poisoned_path)
                or os.path.splitext(filename)[1].lower() not in IMAGE_EXTENSIONS
            ):
                continue

            original_label = None
            original_filename = None
            for cls in CLASSES:
                prefix = f"flipped_{cls}_"
                if filename.startswith(prefix):
                    original_label = cls
                    original_filename = filename[len(prefix):]
                    break

            if original_label is None:
                continue

            clean_path = os.path.join(
                source_root,
                "train",
                original_label,
                original_filename,
            )
            if os.path.exists(clean_path):
                flipped_samples.append({
                    "clean_path": clean_path,
                    "poisoned_path": poisoned_path,
                    "original_label": original_label,
                    "poisoned_label": poisoned_label,
                    "filename": original_filename,
                })

    if not flipped_samples:
        print("No flipped images found to visualize.")
        return None

    rng = random.Random(seed)
    sample_count = min(num_images, len(flipped_samples))
    samples = rng.sample(flipped_samples, sample_count)

    fig, axes = plt.subplots(sample_count, 2, figsize=(8, 3 * sample_count))
    if sample_count == 1:
        axes = [axes]

    for row, sample in enumerate(samples):
        clean_img = plt.imread(sample["clean_path"])
        poisoned_img = plt.imread(sample["poisoned_path"])

        axes[row][0].imshow(clean_img)
        axes[row][0].set_title(
            f"Clean: {sample['original_label']}\n{sample['filename']}",
            fontsize=9,
        )
        axes[row][0].axis("off")

        axes[row][1].imshow(poisoned_img)
        axes[row][1].set_title(
            f"Flipped label: {sample['poisoned_label']}\n"
            f"from {sample['original_label']}",
            fontsize=9,
        )
        axes[row][1].axis("off")

    fig.suptitle(
        f"Label Flip Poisoning Samples ({sample_count} images)",
        fontsize=12,
    )
    fig.tight_layout()

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"label_flip_results_{sample_count}.png")
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    print(f"Label flip visualization saved to: {output_path}")
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Label-Flip Poisoning Attack")
    parser.add_argument(
        "--source",
        default=os.path.join(os.path.dirname(__file__),
                             "..", "classifier", "balanced_data"),
    )
    parser.add_argument(
        "--target",
        default=os.path.join(os.path.dirname(__file__),
                             "..", "classifier", "poisoned_data"),
    )
    parser.add_argument("--flip-rate", type=float, default=0.10)
    parser.add_argument(
        "--source-class", choices=CLASSES, default=None,
        help="Flip only this class (one-way). Omit for symmetric flipping.",
    )
    parser.add_argument(
        "--selection", choices=SELECTIONS, default="confident",
        help="How images to flip are chosen (targeted options use the clean model).",
    )
    parser.add_argument(
        "--model-path",
        default=os.path.join(CLASSIFIER_DIR, "checkpoints", "receipt_cnn_clean.pt"),
        help="Clean checkpoint used by targeted selections.",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--visualize-count", type=int, default=5)
    parser.add_argument("--results-dir", default=RESULTS_DIR)
    args = parser.parse_args()

    poison_dataset(args.source, args.target, args.flip_rate, args.seed, args.source_class,
                   args.selection, args.model_path)
    visualize_flip(
        args.source,
        args.target,
        num_images=args.visualize_count,
        output_dir=args.results_dir,
        seed=args.seed,
    )
