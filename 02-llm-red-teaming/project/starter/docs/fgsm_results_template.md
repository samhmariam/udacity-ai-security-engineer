# FGSM Evasion Attack Results

## Clean Model Baseline

<!-- Record the baseline metrics from evaluate.py -->

- **Model:** ReceiptCNN
- **Test accuracy:**
- **Precision:** | **Recall:** | **F1:**
- **FGSM baseline:** <!-- Note what you observe at epsilon=0.000: the adversarial image should be identical to the clean image and accuracy should match the baseline. This confirms later degradation comes from the perturbation, not the evaluation loop. -->

## FGSM Results

<!-- Fill in from your FGSM attack output -->

| Epsilon | Clean Accuracy | Adversarial Accuracy | Attack Success Rate |
|---------|---------------|---------------------|-------------------|
| 0.000 | | | |
| 0.010 | | | |
| 0.030 | | | |
| 0.050 | | | |
| 0.100 | | | |
| 0.150 | | | |

## Visual Evidence

<!-- visualize_fgsm() saves one PNG per epsilon under attacks/results/01_fgsm/.
     Embed each one below and add a sentence on what you notice at that epsilon
     (e.g. when noise becomes visible, when the prediction flips). -->

![FGSM epsilon 0.000](../attacks/results/01_fgsm/fgsm_results_<sample>_0.png)

![FGSM epsilon 0.010](../attacks/results/01_fgsm/fgsm_results_<sample>_0.01.png)

![FGSM epsilon 0.030](../attacks/results/01_fgsm/fgsm_results_<sample>_0.03.png)

![FGSM epsilon 0.050](../attacks/results/01_fgsm/fgsm_results_<sample>_0.05.png)

![FGSM epsilon 0.100](../attacks/results/01_fgsm/fgsm_results_<sample>_0.1.png)

![FGSM epsilon 0.150](../attacks/results/01_fgsm/fgsm_results_<sample>_0.15.png)

## Analysis

<!-- Answer these questions:
1. At what epsilon does accuracy drop below 50%?
2. How do you interpret the attack success rate?
3. Would these perturbations be visible to a human?
4. What are the implications for the expense system?
-->
