import argparse
import csv
import os
from typing import Dict, List, Any, Optional

def parse_args():
    """
    Parse command-line arguments for eval_mem_metrics.py.

    Expected:
    - --loss_noC_csv: path to the CSV containing canary losses for M_noC
    - --loss_C_csv:   path to the CSV containing canary losses for M_C
    - --canary_file:  (optional) path to the CSV defining the canaries
    - --output_dir:   directory where the results will be saved
    """
    parser = argparse.ArgumentParser(description="Evaluate memorization metrics (counterfactual + contextual).")

    parser.add_argument(
        "--loss_noC_csv",
        type=str,
        required=True,
        help="Path to CSV with canary losses for M_noC (epoch,canary_id,loss).",
    )
    parser.add_argument(
        "--loss_C_csv",
        type=str,
        required=True,
        help="Path to CSV with canary losses for M_C (epoch,canary_id,loss).",
    )
    parser.add_argument(
        "--canary_file",
        type=str,
        default=None,
        help="Optional path to a canary definition file (canary_id,text).",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        required=True,
        help="Directory where result CSVs will be saved.",
    )

    args = parser.parse_args()
    return args


def load_canaries(path: str) -> Dict[str, str]:
    """
    Load canaries from a CSV file with columns:

        canary_id,text

    Args:
        path: path to the CSV file.

    Returns:
        dict: mapping canary_id -> text
    """
    # TODO: implementation
    pass


def load_losses_from_csv(path: str) -> Dict[int, Dict[str, float]]:
    """
    Load canary losses from a CSV with columns:

        epoch,canary_id,loss

    and build a nested structure:

        losses[epoch][canary_id] = loss_value

    Args:
        path: path to the CSV file.

    Returns:
        dict: nested dictionary epoch -> canary_id -> loss.
    """
    losses: Dict[int, Dict[str, float]] = {}

    with open(path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse fields
            try:
                epoch = int(row["epoch"])
            except (KeyError, ValueError) as e:
                raise ValueError(f"Invalid or missing 'epoch' field in row: {row}") from e

            try:
                canary_id = row["canary_id"]
            except KeyError as e:
                raise ValueError(f"Missing 'canary_id' field in row: {row}") from e

            try:
                loss = float(row["loss"])
            except (KeyError, ValueError) as e:
                raise ValueError(f"Invalid or missing 'loss' field in row: {row}") from e

            # Insert into nested dict
            if epoch not in losses:
                losses[epoch] = {}
            losses[epoch][canary_id] = loss

    return losses



def compute_counterfactual(
    loss_noC: Dict[int, Dict[str, float]],
    loss_C: Dict[int, Dict[str, float]],
) -> (Dict[int, Dict[str, float]], Dict[str, Optional[int]]):
    """
    Compute counterfactual memorization for each (epoch, canary_id).

    Input:
        loss_noC[epoch][canary_id] = loss for model M_noC
        loss_C[epoch][canary_id]   = loss for model M_C

    For each epoch e and canary s, we compute:

        mem_cf(s, e) = (loss_noC[e][s] - loss_C[e][s]) / loss_noC[e][s]

    with the following safety rules:
        - if loss_noC[e][s] <= 0: mem_cf = 0.0
        - clamp mem_cf to [0, 1]

    Returns:
        cf_scores[epoch][canary_id] = mem_cf value in [0, 1]
        start_epoch_cf[canary_id]   = first epoch where mem_cf > 0,
                                      or None if never > 0
    """
    cf_scores: Dict[int, Dict[str, float]] = {}

    # ---- Step 1: compute per-(epoch, canary) counterfactual scores ----
    for epoch, canary_losses_noC in loss_noC.items():
        # Skip epochs that are not present in loss_C
        if epoch not in loss_C:
            continue

        cf_scores[epoch] = {}
        canary_losses_C = loss_C[epoch]

        for canary_id, loss_MnoC in canary_losses_noC.items():
            # Skip canaries that are missing in loss_C for this epoch
            if canary_id not in canary_losses_C:
                continue

            loss_MC = canary_losses_C[canary_id]

            if loss_MnoC <= 0.0:
                mem_score = 0.0
            else:
                mem_score = (loss_MnoC - loss_MC) / loss_MnoC

                # Clamp to [0, 1]
                if mem_score < 0.0:
                    mem_score = 0.0
                elif mem_score > 1.0:
                    mem_score = 1.0

            cf_scores[epoch][canary_id] = mem_score

    # ---- Step 2: compute start_epoch_cf per canary ----
    start_epoch_cf: Dict[str, Optional[int]] = {}

    # Gather all canary_ids that appear in cf_scores
    all_canaries_cf = set()
    for epoch_scores in cf_scores.values():
        all_canaries_cf.update(epoch_scores.keys())

    for canary_id in all_canaries_cf:
        start_epoch_cf[canary_id] = None
        for epoch in sorted(cf_scores.keys()):
            mem_score = cf_scores[epoch].get(canary_id, 0.0)
            if mem_score > 0.0:
                start_epoch_cf[canary_id] = epoch
                break

    return cf_scores, start_epoch_cf


def compute_contextual(
    loss_noC: Dict[int, Dict[str, float]],
    loss_C: Dict[int, Dict[str, float]],
):
    """
    Compute contextual memorization.

    Inputs:
        loss_noC[epoch][canary_id] = loss for model M_noC
        loss_C[epoch][canary_id]   = loss for model M_C

    Steps:
        1) opt_ctx_loss[s] = min_e loss_noC[e][s]
        2) mem_ctx(s, e) = max(0, (opt_ctx_loss[s] - loss_C[e][s]) / opt_ctx_loss[s])
           - if opt_ctx_loss[s] <= 0, mem_ctx(s, e) = 0.0
           - clamp mem_ctx to [0, 1]
        3) start_epoch_ctx[s] = first epoch e where mem_ctx(s, e) > 0,
           or None if never > 0.

    Returns:
        ctx_scores: Dict[int, Dict[str, float]]  # ctx_scores[epoch][canary_id] = mem_ctx
        opt_ctx_loss: Dict[str, float]          # opt_ctx_loss[canary_id] = best loss_noC
        start_epoch_ctx: Dict[str, Optional[int]]
    """

    # ---- Step 1: compute opt_ctx_loss ----
    # Collect all canary_ids that appear in loss_noC
    canary_ids = set()
    for epoch_losses in loss_noC.values():
        canary_ids.update(epoch_losses.keys())

    opt_ctx_loss: Dict[str, float] = {}

    for canary_id in canary_ids:
        values = []
        for epoch, epoch_losses in loss_noC.items():
            if canary_id in epoch_losses:
                values.append(epoch_losses[canary_id])

        if not values:
            # No loss_noC value for this canary across epochs -> skip or set 0
            # Here we choose to set 0.0, which will force mem_ctx = 0 later.
            opt_ctx_loss[canary_id] = 0.0
        else:
            opt_ctx_loss[canary_id] = min(values)

    # ---- Step 2: compute mem_ctx(s, e) for each epoch and canary ----
    ctx_scores: Dict[int, Dict[str, float]] = {}

    for epoch, epoch_losses_C in loss_C.items():
        ctx_scores[epoch] = {}

        for canary_id, loss_MC in epoch_losses_C.items():
            opt_loss = opt_ctx_loss.get(canary_id, 0.0)

            if opt_loss <= 0.0:
                mem_score = 0.0
            else:
                mem_score = (opt_loss - loss_MC) / opt_loss

                # Clamp to [0, 1]
                if mem_score < 0.0:
                    mem_score = 0.0
                elif mem_score > 1.0:
                    mem_score = 1.0

            ctx_scores[epoch][canary_id] = mem_score

    # ---- Step 3: start_epoch_ctx ----
    # First epoch where mem_ctx(s, e) > 0, or None if never.
    start_epoch_ctx: Dict[str, Optional[int]] = {}

    # Gather all canary_ids that appear in ctx_scores
    all_canaries_ctx = set()
    for epoch, epoch_scores in ctx_scores.items():
        all_canaries_ctx.update(epoch_scores.keys())

    for canary_id in all_canaries_ctx:
        start_epoch_ctx[canary_id] = None
        for epoch in sorted(ctx_scores.keys()):
            mem_score = ctx_scores[epoch].get(canary_id, 0.0)
            if mem_score > 0.0:
                start_epoch_ctx[canary_id] = epoch
                break

    return ctx_scores, opt_ctx_loss, start_epoch_ctx

def save_counterfactual_results(
    cf_scores: Dict[int, Dict[str, float]],
    start_epoch_cf: Dict[str, Optional[int]],
    out_path: str
) -> None:
    """
    Save counterfactual memorization results to CSV.

    Output columns:
        epoch,canary_id,cf_score,start_epoch_cf
    """
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    with open(out_path, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["epoch", "canary_id", "cf_score", "start_epoch_cf"])

        for epoch in sorted(cf_scores.keys()):
            for canary_id in sorted(cf_scores[epoch].keys()):
                score = cf_scores[epoch][canary_id]
                start_epoch = start_epoch_cf.get(canary_id, None)
                start_epoch_str = "None" if start_epoch is None else start_epoch

                writer.writerow([epoch, canary_id, score, start_epoch_str])



def save_contextual_results(
    ctx_scores: Dict[int, Dict[str, float]],
    opt_ctx_loss: Dict[str, float],
    start_epoch_ctx: Dict[str, Optional[int]],
    out_path: str,
) -> None:
    """
    Save contextual memorization results to a CSV file.

    Expected input:
        ctx_scores[epoch][canary_id] = ctx_score
        opt_ctx_loss[canary_id]      = optimal contextual loss (min loss_noC over epochs)
        start_epoch_ctx[canary_id]   = first epoch where ctx_score > 0, or None

    Output CSV format:
        epoch,canary_id,ctx_score,opt_ctx_loss,start_epoch_ctx
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    with open(out_path, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        # Header
        writer.writerow(["epoch", "canary_id", "ctx_score", "opt_ctx_loss", "start_epoch_ctx"])

        # Write one row per (epoch, canary_id)
        for epoch in sorted(ctx_scores.keys()):
            canary_dict = ctx_scores[epoch]
            for canary_id in sorted(canary_dict.keys()):
                ctx_value = canary_dict[canary_id]
                opt_value = opt_ctx_loss.get(canary_id, "")
                start_epoch = start_epoch_ctx.get(canary_id, None)
                start_epoch_str = "None" if start_epoch is None else start_epoch

                writer.writerow([epoch, canary_id, ctx_value, opt_value, start_epoch_str])



def main():
    """
    Main pipeline:

    1. Parse command-line arguments.
    2. Load losses for M_noC and M_C from CSV files.
    3. Compute counterfactual and contextual memorization metrics.
    4. Save results as CSVs in output_dir.
    """
    args = parse_args()

    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)

    # 1) Load losses
    loss_noC = load_losses_from_csv(args.loss_noC_csv)
    loss_C = load_losses_from_csv(args.loss_C_csv)

    # 2) Counterfactual
    cf_scores, start_epoch_cf = compute_counterfactual(loss_noC, loss_C)
    cf_out_path = os.path.join(args.output_dir, "counterfactual_results.csv")
    save_counterfactual_results(cf_scores, start_epoch_cf, cf_out_path)

    # 3) Contextual
    ctx_scores, opt_ctx_loss, start_epoch_ctx = compute_contextual(loss_noC, loss_C)
    ctx_out_path = os.path.join(args.output_dir, "contextual_results.csv")
    save_contextual_results(ctx_scores, opt_ctx_loss, start_epoch_ctx, ctx_out_path)

if __name__ == "__main__":
    main()
