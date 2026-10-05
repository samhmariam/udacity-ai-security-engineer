# FGSM Evasion Attack Results

## Clean Model Baseline

Source: `python evaluate.py --model-path checkpoints/receipt_cnn_clean.pt --test-dir balanced_data/test` (390 test images: 195 receipt, 195 non_receipt; positive class = `receipt`).

- **Model:** ReceiptCNN (`checkpoints/receipt_cnn_clean.pt`)
- **Test accuracy:** 0.9436
- **Precision:** 0.9943 | **Recall:** 0.8923 | **F1:** 0.9405
- **Confusion matrix** (rows = true, cols = predicted, order `[non_receipt, receipt]`): `[[194, 1], [21, 174]]`
- **FGSM baseline:** At ε = 0.000 the adversarial image is pixel-identical to the clean image. The sample prediction is unchanged (0.004 → 0.004), and adversarial accuracy (0.9436) exactly matches the `evaluate.py` baseline. So the evaluation loop adds no error of its own, and all later degradation comes from the perturbation.

## FGSM Results

Source: `python attacks/01_fgsm_evasion.py` → `attacks/results/01_fgsm/fgsm_results.json`. Attack success rate = correctly classified images that the attack flipped to wrong ÷ correctly classified clean images (368).

| Epsilon | Clean Accuracy | Adversarial Accuracy | Attack Success Rate |
|---------|---------------|---------------------|-------------------|
| 0.000 | 0.9436 | 0.9436 | 0.0000 |
| 0.010 | 0.9436 | 0.8077 | 0.1440 |
| 0.030 | 0.9436 | 0.5103 | 0.4592 |
| 0.050 | 0.9436 | 0.3000 | 0.6821 |
| 0.100 | 0.9436 | **0.2718** | **0.7120** |
| 0.150 | 0.9436 | 0.4462 | 0.5272 |

### Supplementary breakdown: flip direction and image distortion

The headline numbers mix two attacks with very different business impact. To separate them, I re-ran the same `fgsm_attack()` over the test set with a diagnostic script (not part of the deliverable code). It splits flips by true class and measures distortion as mean PSNR, the peak signal-to-noise ratio between the clean and perturbed image. Higher PSNR means less visible change. Roughly, ≥ 40 dB is imperceptible, 30–35 dB is subtle, and < 25 dB is clearly visible.

| Epsilon | Mean PSNR | **Fraud direction:** non_receipt → receipt flips | Rejection direction: receipt → non_receipt flips |
|---------|-----------|------------------|------------------|
| 0.010 | 40.4 dB | 6 / 194 (3%) | 47 / 174 (27%) |
| 0.030 | 31.0 dB | 41 / 194 (21%) | 128 / 174 (74%) |
| 0.050 | 26.6 dB | 79 / 194 (41%) | 172 / 174 (99%) |
| 0.100 | 20.8 dB | **88 / 194 (45%)** | 174 / 174 (100%) |
| 0.150 | 17.4 dB | 20 / 194 (10%) | 174 / 174 (100%) |

## Visual Evidence

All panels use the same test image (`openimages_0000`, true class **non_receipt**: a photo of a car). So this sample shows the **fraud direction**: getting a non-receipt accepted as a receipt. The number in brackets is the model's receipt score (> 0.5 = receipt).

![FGSM epsilon 0.000](../attacks/results/01_fgsm/fgsm_results_openimages_0000_0.png)

**ε = 0.000:** Control. The two images are identical, and the prediction stays non_receipt (0.004).

![FGSM epsilon 0.010](../attacks/results/01_fgsm/fgsm_results_openimages_0000_0.01.png)

**ε = 0.010:** Even side by side, the perturbed image cannot be told apart from the original (PSNR ≈ 40 dB). The prediction is still non_receipt, but the receipt score has already risen 13× (0.004 → 0.052). The model is moving long before anything is visible. Across the test set, 27% of genuine receipts already flip to rejected at this ε.

![FGSM epsilon 0.030](../attacks/results/01_fgsm/fgsm_results_openimages_0000_0.03.png)

**ε = 0.030:** A faint, uniform film grain is visible only when the clean image sits right next to it, mostly in flat areas (gravel, sky, the car's body panels). Viewed alone it looks like an ordinary low-quality phone photo or JPEG. The sample is still non_receipt, but the score is now 0.403, close to the 0.5 boundary. Model-wide, accuracy has fallen to 51% (near coin-flip) while the image still looks normal.

![FGSM epsilon 0.050](../attacks/results/01_fgsm/fgsm_results_openimages_0000_0.05.png)

**ε = 0.050:** **The prediction flips: a car photo is classified as a receipt with 0.839 confidence.** Noise is now visible without a reference: colored speckle across the foliage and road, with slightly muted colors. A careful reviewer looking for tampering might notice it, but it is still easy to put down to sensor noise or heavy compression.

![FGSM epsilon 0.100](../attacks/results/01_fgsm/fgsm_results_openimages_0000_0.1.png)

**ε = 0.100:** Classified as a receipt with 0.889 confidence. The image is obviously damaged: heavy rainbow-colored static, and the watermark text is starting to break up. Any human who looks at it would see it has been manipulated.

![FGSM epsilon 0.150](../attacks/results/01_fgsm/fgsm_results_openimages_0000_0.15.png)

**ε = 0.150:** The image is badly corrupted, and the prediction *reverts* to non_receipt (0.112). Too much noise no longer pushes toward "receipt", and the heavily noised image reads to the model as just another non-receipt photo. This is why overall attack success falls at ε = 0.15. The drop comes entirely from the fraud direction (45% → 10%), while genuine receipts stay 100% rejected.

### Commentary: visual degradation vs. model failure

**The model fails well before the image visibly degrades.** In the sample, the receipt score starts rising at ε = 0.01, where the change is imperceptible. Across the test set, accuracy has fallen from 94% to 51% by ε = 0.03, where the noise is visible only next to the original. Visible degradation starts around ε = 0.05 and is obvious from ε = 0.10. That gap of about 2–3× in ε is the attacker's working window.

From the point of view of an attacker who wants to change the output without a reviewer noticing:

- **Best ε for stealth: about 0.03.** Images pass a casual look (PSNR 31 dB) and appear to a reviewer as a slightly grainy upload. At this budget an attacker can get 74% of genuine receipts rejected (sabotage or denial of service against a colleague or vendor) and 21% of non-receipts accepted as receipts (fraud), with no image edits that look suspicious.
- **Best ε for fraud: about 0.05.** The fraud direction is harder: the model has a strong bias toward "non_receipt", and its recall is only 0.89 even on clean data. Flipping a non-receipt needs more budget, and 41% succeed at ε = 0.05. At this point the noise is perceptible on close inspection but plausibly innocent. ε = 0.10 gains only 4 more points (45%) for clearly visible tampering, so it is not worth the detection risk.
- **The content caveat.** FGSM changes the *classifier's* decision, not what the picture *shows*. If a reviewer actually looks at the image, a car is still a car. The fraud attack therefore works against **automated or rubber-stamp approval**, where the reviewer trusts the model's label or skims thumbnails. A more realistic attacker would perturb a *borderline* document (an altered, duplicated or out-of-policy receipt) that already looks receipt-like, so the content passes the eye test and FGSM only has to defeat the classifier. The rejection-direction attack has no such limit: a lightly perturbed real receipt still looks like a real receipt to a human, yet is 74–99% likely to be auto-rejected at ε = 0.03–0.05.
- **Visibility depends on content.** The sample is a busy outdoor scene, which hides noise well. Receipts are mostly flat white paper with thin text, where speckle is easier to see in mid-tones. Pure-white areas partly hide it because pixels are clamped at 1.0. Reviewers may also view images at a different resolution from the 224×224 model input. Treat the ε thresholds above as approximate.

## Analysis

1. **At what epsilon does accuracy drop below 50%?**
   Between ε = 0.03 (51.0%) and ε = 0.05 (30.0%). At ε = 0.03 the model is already at chance on a balanced test set. From ε = 0.05 it does *worse* than random guessing, because the perturbation pushes predictions systematically toward the wrong class rather than just adding uncertainty.

2. **How do you interpret the attack success rate?**
   It measures the share of decisions the model got right that an attacker can reverse. At ε = 0.10, 71% of correct classifications can be flipped with one gradient step and no iterative optimization, so a basic white-box attacker controls most outcomes. The rate is very uneven. Genuine receipts are almost trivially flipped to rejected (99–100% from ε = 0.05), while non-receipts accepted as receipts peak at about 45%. The drop at ε = 0.15 shows that FGSM overshoots at large budgets. It does not mean the model becomes robust: an iterative attack such as PGD would be expected to keep success high, and this assessment did not test it.

3. **Would these perturbations be visible to a human?**
   - ε ≤ 0.01: no.
   - ε = 0.03: only when compared side by side with the original, and reviewers never have the original.
   - ε = 0.05: noticeable as grain or speckle but plausibly innocent.
   - ε ≥ 0.10: obvious tampering.

   The model is badly compromised (accuracy ≤ 51%) at levels a human would not flag.

4. **What are the implications for the expense system?**
   - **Fraud:** If the classifier gates submissions or approvals automatically, an employee can get non-receipt images accepted as receipt evidence. Better still for them, they can launder doctored or duplicate receipts past the model with perturbations that look like ordinary photo noise.
   - **Sabotage / denial of service:** Genuine receipts can be made to auto-reject at near-100% rates with almost invisible changes. That causes reimbursement disputes and manual-review backlogs.
   - **Human review is not a reliable backstop:** The perturbations that do the damage are below a reviewer's notice threshold. Review only catches the attack if reviewers check image *content* independently of the model's label.
   - **Recommended mitigations:**
     - Adversarial training (FGSM/PGD) to harden the model.
     - Input preprocessing that removes high-frequency noise (JPEG re-compression, resizing, or denoising) before inference.
     - Treating scores near the threshold as "needs human review" rather than auto-decisions.
     - Not exposing model scores or gradients to submitters. White-box access made this attack trivial, and keeping the model private raises the cost but does not remove the risk, since transfer attacks remain possible.
     - Pairing the classifier with independent checks such as OCR of merchant, amount and date and duplicate detection.
