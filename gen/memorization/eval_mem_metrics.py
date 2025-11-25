import argparse
import csv
import os
from typing import Dict, List, Any, Optional, Tuple


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate memorization metrics (counterfactual + contextual).")

    parser.add_argument(
        "--loss_noC_csv",
        type=str,
        required=True,
        help="Path to CSV with canary losses for M_noC.",
    )
    parser.add_argument(
        "--loss_C_csv",
        type=str,
        required=True,
        help="Path to CSV with canary losses for M_C.",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        required=True,
        help="Directory where result CSVs will be saved.",
    )

    args = parser.parse_args()
    return args


def load_losses_from_csv(path: str) -> Tuple[Dict[int, Dict[str, float]], Dict[int, Dict[str, float]]]:
    """
    Load canary losses from the NEW CSV format:
        epoch,canary_id,global_loss,suffix_loss

    Returns:
        (losses_global, losses_suffix)
        Each is a nested dict: epoch -> canary_id -> loss_value
    """
    losses_global: Dict[int, Dict[str, float]] = {}
    losses_suffix: Dict[int, Dict[str, float]] = {}

    with open(path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                epoch = int(row["epoch"])
                canary_id = row["canary_id"]

                # Check if we have the new columns or fallback to old 'loss'
                if "global_loss" in row and "suffix_loss" in row:
                    g_val = float(row["global_loss"])
                    s_val = float(row["suffix_loss"])
                elif "loss" in row:
                    # Fallback for old files
                    g_val = float(row["loss"])
                    s_val = float(row["loss"])
                else:
                    # Skip if format is unknown
                    continue

            except (KeyError, ValueError) as e:
                print(f"Skipping invalid row in {path}: {row} ({e})")
                continue

            # Populate Global Dict
            if epoch not in losses_global:
                losses_global[epoch] = {}
            losses_global[epoch][canary_id] = g_val

            # Populate Suffix Dict
            if epoch not in losses_suffix:
                losses_suffix[epoch] = {}
            losses_suffix[epoch][canary_id] = s_val

    return losses_global, losses_suffix


def compute_counterfactual(
        loss_noC: Dict[int, Dict[str, float]],
        loss_C: Dict[int, Dict[str, float]],
):
    cf_scores = {}
    # Iterate over epochs present in NoC
    for epoch, canary_losses_noC in loss_noC.items():
        if epoch not in loss_C:
            continue

        cf_scores[epoch] = {}
        canary_losses_C = loss_C[epoch]

        for canary_id, loss_MnoC in canary_losses_noC.items():
            if canary_id not in canary_losses_C:
                continue

            loss_MC = canary_losses_C[canary_id]

            if loss_MnoC <= 0.0:
                mem_score = 0.0
            else:
                mem_score = (loss_MnoC - loss_MC) / loss_MnoC
                # Clamp score between 0 and 1
                mem_score = max(0.0, min(1.0, mem_score))

            cf_scores[epoch][canary_id] = mem_score

    # Determine start epoch for each canary
    start_epoch_cf = {}
    # Get all unique canary IDs across all epochs
    all_canaries = set()
    for e in cf_scores:
        all_canaries.update(cf_scores[e].keys())

    for canary_id in all_canaries:
        start_epoch_cf[canary_id] = "None"
        for epoch in sorted(cf_scores.keys()):
            if cf_scores[epoch].get(canary_id, 0.0) > 0.0:
                start_epoch_cf[canary_id] = epoch
                break

    return cf_scores, start_epoch_cf


def compute_contextual(
        loss_noC: Dict[int, Dict[str, float]],
        loss_C: Dict[int, Dict[str, float]],
):
    # Step 1: Calculate Optimal Contextual Loss (Min historical loss of M_noC)
    canary_ids = set()
    for epoch_losses in loss_noC.values():
        canary_ids.update(epoch_losses.keys())

    opt_ctx_loss = {}
    for canary_id in canary_ids:
        values = []
        for epoch, epoch_losses in loss_noC.items():
            if canary_id in epoch_losses:
                values.append(epoch_losses[canary_id])
        opt_ctx_loss[canary_id] = min(values) if values else 0.0

    # Step 2: Compute Contextual Score
    ctx_scores = {}
    for epoch, epoch_losses_C in loss_C.items():
        ctx_scores[epoch] = {}
        for canary_id, loss_MC in epoch_losses_C.items():
            opt_loss = opt_ctx_loss.get(canary_id, 0.0)

            if opt_loss <= 0.0:
                mem_score = 0.0
            else:
                mem_score = (opt_loss - loss_MC) / opt_loss
                mem_score = max(0.0, min(1.0, mem_score))

            ctx_scores[epoch][canary_id] = mem_score

    # Step 3: Determine start epoch
    start_epoch_ctx = {}
    all_canaries = set()
    for e in ctx_scores:
        all_canaries.update(ctx_scores[e].keys())

    for canary_id in all_canaries:
        start_epoch_ctx[canary_id] = "None"
        for epoch in sorted(ctx_scores.keys()):
            if ctx_scores[epoch].get(canary_id, 0.0) > 0.0:
                start_epoch_ctx[canary_id] = epoch
                break

    return ctx_scores, opt_ctx_loss, start_epoch_ctx


def save_results(scores, start_epochs, out_path, opt_loss=None):
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    with open(out_path, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        header = ["epoch", "canary_id", "score", "start_epoch"]
        if opt_loss:
            header.append("opt_ctx_loss")
        writer.writerow(header)

        for epoch in sorted(scores.keys()):
            for canary_id in sorted(scores[epoch].keys()):
                score = scores[epoch][canary_id]
                start = start_epochs.get(canary_id, "None")

                row = [epoch, canary_id, score, start]
                if opt_loss:
                    row.append(opt_loss.get(canary_id, ""))

                writer.writerow(row)


def main():
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    # 1. Load BOTH types of losses from the CSVs
    print(f"Loading M_noC logs from: {args.loss_noC_csv}")
    print(f"Loading M_C logs from: {args.loss_C_csv}")

    noC_global, noC_suffix = load_losses_from_csv(args.loss_noC_csv)
    C_global, C_suffix = load_losses_from_csv(args.loss_C_csv)

    # --- ANALYSIS A: GLOBAL LOSS (Legacy/Comparison) ---
    print("Computing metrics based on GLOBAL Loss...")

    # Counterfactual (Global)
    cf_scores_g, start_cf_g = compute_counterfactual(noC_global, C_global)
    save_results(cf_scores_g, start_cf_g, os.path.join(args.output_dir, "counterfactual_GLOBAL.csv"))

    # Contextual (Global)
    ctx_scores_g, opt_loss_g, start_ctx_g = compute_contextual(noC_global, C_global)
    save_results(ctx_scores_g, start_ctx_g, os.path.join(args.output_dir, "contextual_GLOBAL.csv"), opt_loss_g)

    # --- ANALYSIS B: SUFFIX LOSS (Carlini/Targeted) ---
    print("Computing metrics based on SUFFIX Loss...")

    # Counterfactual (Suffix)
    cf_scores_s, start_cf_s = compute_counterfactual(noC_suffix, C_suffix)
    save_results(cf_scores_s, start_cf_s, os.path.join(args.output_dir, "counterfactual_SUFFIX.csv"))

    # Contextual (Suffix)
    ctx_scores_s, opt_loss_s, start_ctx_s = compute_contextual(noC_suffix, C_suffix)
    save_results(ctx_scores_s, start_ctx_s, os.path.join(args.output_dir, "contextual_SUFFIX.csv"), opt_loss_s)

    print(f"Done. All results saved in {args.output_dir}")


if __name__ == "__main__":
    main()