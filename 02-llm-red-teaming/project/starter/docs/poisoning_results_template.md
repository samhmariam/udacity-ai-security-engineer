# Data Poisoning Results

## Attack Configuration

- **Method:** Label-flip poisoning
- **Flip rate:**
- **Labels flipped:** ___ out of ___ training images
- **Goal:** <!-- One sentence on what the attack is meant to demonstrate (e.g. that a small label-corruption shifts the decision boundary on otherwise-clean evaluation data). -->

## Label Flip Evidence

<!-- visualize_flip() saves a PNG showing clean images next to their poisoned
     (label-flipped) copies. Embed it here and add one sentence confirming the
     attack changes labels, not pixel content. -->

![Label flip comparison](../attacks/results/02_label_flip/label_flip_results_5.png)

## Baseline (Clean Model)

| Metric | Value |
|--------|-------|
| Accuracy | |
| Precision | |
| Recall | |
| F1 Score | |

## Poisoned Model

| Metric | Value |
|--------|-------|
| Accuracy | |
| Precision | |
| Recall | |
| F1 Score | |

## Impact Analysis

| Metric | Clean | Poisoned | Change |
|--------|-------|----------|--------|
| Accuracy | | | |
| Precision | | | |
| Recall | | | |
| F1 | | | |

## Confusion Matrices (Optional)

<!-- Optional — not graded. Running `evaluate.py --results-dir <folder>` saves a
     confusion_matrix.png next to metrics.json for each model. Embedding them is the
     clearest way to show *which* class the poisoning actually damaged, which supports
     the "which class was more affected" question below. Delete this section if you
     choose not to include them. -->

![Clean model confusion matrix](../attacks/results/02_label_flip/clean/confusion_matrix.png)

![Poisoned model confusion matrix](../attacks/results/02_label_flip/poisoned/confusion_matrix.png)

## Key Findings

<!-- Analyze:
1. How significant is the accuracy drop?
2. Which class was more affected and why?
3. If you included the confusion matrices, what do they tell you?
4. What are the implications of this attack?
-->
