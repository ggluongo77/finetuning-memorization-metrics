import argparse
import os
import pandas as pd
import numpy as np
import sys


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate Memorization Metrics (Modular & Strict).")
    parser.add_argument("--loss_noC_csv", type=str, required=True, help="Path to M_noC logs (Reference).")
    parser.add_argument("--loss_C_csv", type=str, required=True, help="Path to M_C logs (Target).")
    parser.add_argument("--output_dir", type=str, required=True, help="Directory to save results.")
    return parser.parse_args()


def load_and_validate_data(filepath):
    """
    Loads CSV and checks for required columns.
    Returns DataFrame or exits if invalid.
    """
    if not os.path.exists(filepath):
        print(f"ERROR: File not found: {filepath}")
        sys.exit(1)

    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        print(f"ERROR loading {filepath}: {e}")
        sys.exit(1)

    # Basic columns required for calculation
    required_cols = {'epoch', 'canary_id', 'suffix_loss', 'split'}

    if not required_cols.issubset(df.columns):
        print(f"ERROR: File {filepath} missing columns. Required: {required_cols}")
        sys.exit(1)

    # Optional: Check for exact_match (Biderman metric)
    if 'exact_match' not in df.columns:
        print(f"WARNING: 'exact_match' column not found in {filepath}. Biderman metric will be 0.")

    return df


def compute_optimal_contextual_loss(df_ref):
    """
    STRICT DEFINITION (Ghosh et al.):
    Calculates L_opt (Optimal Contextual Loss) for each canary.
    L_opt = min(Loss(Reference)) across ALL epochs.
    """
    print("   -> Computing historical minimum loss for Reference model...")
    # Group by canary and take the minimum suffix loss observed during reference training
    df_opt = df_ref.groupby("canary_id")["suffix_loss"].min().reset_index()
    df_opt.rename(columns={"suffix_loss": "loss_optimum"}, inplace=True)
    return df_opt


def calculate_dynamic_threshold(scores, fpr_target=0.10):
    """
    Calculates threshold tau from Validation scores at (1-FPR) percentile.
    """
    if len(scores) == 0:
        return float('inf')

    percentile = (1 - fpr_target) * 100
    return np.percentile(scores, percentile)


def compute_scores(df_tgt, df_ref, df_opt):
    """
    Merges dataframes and calculates scores.
    Applies clipping (ReLU) to ensure that if the target loss is worse
    than the reference/optimum, the score is 0 (not negative).
    """
    print("   -> Merging data and computing scores...")

    # 1. Merge Target con Reference per l'epoca corrente
    df_merged = pd.merge(
        df_tgt,
        df_ref[['epoch', 'canary_id', 'suffix_loss', 'global_loss']],
        on=['epoch', 'canary_id'],
        suffixes=('_tgt', '_ref'),  # Corretto: suffixes deve essere una tupla
        how='inner'
    )

    # 2. Merge con la loss ottimale (minimo storico del Reference)
    df_merged = pd.merge(df_merged, df_opt, on="canary_id", how="left")

    # --- CALCOLO METRICHE CON CLIPPING ---

    # MIA Score = Loss_Ref - Loss_Tgt
    df_merged['mia_score'] = df_merged['suffix_loss_ref'] - df_merged['suffix_loss_tgt']

    # Counterfactual = (Loss_Ref - Loss_Tgt) / Loss_Ref
    # Usiamo .clip(lower=0) per azzerare i valori dove il target è peggiore del reference
    cf_raw = (df_merged['suffix_loss_ref'] - df_merged['suffix_loss_tgt']) / df_merged['suffix_loss_ref']
    df_merged['counterfactual_score'] = cf_raw.clip(lower=0)

    # Contextual (Strict) = (Loss_Optimum - Loss_Tgt) / Loss_Optimum
    # Questo è il punto chiave per l'Epoca 0:
    # se la loss attuale è più alta del minimo storico, il risultato è 0.
    ctx_raw = (df_merged['loss_optimum'] - df_merged['suffix_loss_tgt']) / df_merged['loss_optimum']
    df_merged['contextual_score'] = ctx_raw.clip(lower=0)

    return df_merged


def analyze_epoch(df_epoch, epoch):
    """
    Analyzes a single epoch:
    1. Calibrates Threshold on Validation Data.
    2. Computes Recall/Avg Scores on Training Data.
    3. Computes Average Perplexity on Training Data.
    """
    # Split Data
    val_data = df_epoch[df_epoch['split'] == 'validation']
    train_data = df_epoch[df_epoch['split'] == 'train']

    # Check if data exists
    if len(val_data) == 0 or len(train_data) == 0:
        return None

    # 1. Calibrate Threshold (MIA)
    threshold_tau = calculate_dynamic_threshold(val_data['mia_score'].values, fpr_target=0.10)

    # 2. Compute Metrics (on Training Set)

    # A. MIA Recall (Binary)
    memorized_count = (train_data['mia_score'] > threshold_tau).sum()
    mia_recall = memorized_count / len(train_data)

    # B. Biderman Exact Match (Binary)
    if 'exact_match' in train_data.columns:
        exact_match = train_data['exact_match'].mean()
    else:
        exact_match = 0.0

    # C. Average Continuous Scores (Ghosh)
    avg_ctx = train_data['contextual_score'].mean()
    avg_cf = train_data['counterfactual_score'].mean()

    # D. Average Perplexity
    avg_loss = train_data['suffix_loss_tgt'].mean()
    avg_perplexity = np.exp(avg_loss)

    return {
        'epoch': epoch,
        'mia_threshold_tau': threshold_tau,
        'mia_recall': mia_recall,
        'exact_match': exact_match,
        'avg_counterfactual_score': avg_cf,
        'avg_contextual_score': avg_ctx,
        'avg_perplexity': avg_perplexity,  # <--- Salviamo questo dato
        'n_train_samples': len(train_data)
    }

def main():
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    print("--- 1. LOADING DATA ---")
    df_ref = load_and_validate_data(args.loss_noC_csv)
    df_tgt = load_and_validate_data(args.loss_C_csv)


    print("--- DIAGNOSTIC: EPOCH 0 CHECK ---")
    ep0_tgt_stats = df_tgt[df_tgt['epoch'] == 0]
    ep0_ref_stats = df_ref[df_ref['epoch'] == 0]

    if ep0_tgt_stats.empty or ep0_ref_stats.empty:
        print(" ERROR: Missing Epoch 0 in one of the files.")
    else:
        m_tgt = ep0_tgt_stats['suffix_loss'].mean()
        m_ref = ep0_ref_stats['suffix_loss'].mean()
        print(f" > Average Suffix Loss at Epoch 0: Target={m_tgt:.4f}, Reference={m_ref:.4f}")

        if m_tgt < m_ref * 0.8:
            print(" ALERT: Target is already MUCH better than Reference at Ep 0.")
            print("   Check if you swapped the files or if Reference is the wrong model.")
        elif abs(m_tgt - m_ref) < 0.05:
            print(" OK: Models are aligned at Epoch 0.")
    print("---------------------------------")

    print("--- 2. PRE-COMPUTING BASELINES ---")
    df_opt = compute_optimal_contextual_loss(df_ref)

    print("--- 3. COMPUTING SCORES ---")
    df_processed = compute_scores(df_tgt, df_ref, df_opt)

    print("--- 4. RUNNING EPOCH ANALYSIS ---")
    results = []
    epochs = sorted(df_processed['epoch'].unique())

    for epoch in epochs:
        df_epoch = df_processed[df_processed['epoch'] == epoch]
        stats = analyze_epoch(df_epoch, epoch)

        if stats:
            print(
                f"Epoch {epoch}: MIA={stats['mia_recall']:.2%} | EM={stats['exact_match']:.2%} | PPL={stats['avg_perplexity']:.2f} | CTX={stats['avg_contextual_score']:.4f}")

            results.append(stats)
        else:
            print(f"Epoch {epoch}: Insufficient data to analyze.")

    print("--- 5. SAVING RESULTS ---")
    # Save Summary
    summary_path = os.path.join(args.output_dir, "metrics_summary.csv")
    pd.DataFrame(results).to_csv(summary_path, index=False)

    # Save Details
    details_path = os.path.join(args.output_dir, "canary_details_full.csv")
    df_processed.to_csv(details_path, index=False)

    print(f"Done. Results in: {args.output_dir}")


if __name__ == "__main__":
    main()