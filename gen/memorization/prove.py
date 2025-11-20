from pprint import pprint

from eval_mem_metrics import (
    compute_counterfactual,
    save_counterfactual_results,
)


def main():
    # Fake input for testing
    loss_noC = {
        0: {"C0": 4.0, "C1": 4.2},
        1: {"C0": 3.5, "C1": 4.0},
    }

    loss_C = {
        0: {"C0": 3.8, "C1": 4.0},
        1: {"C0": 2.5, "C1": 3.9},
    }

    print(">>> Computing counterfactual scores...")
    cf_scores, start_epoch_cf = compute_counterfactual(loss_noC, loss_C)

    print("\ncf_scores:")
    pprint(cf_scores)

    print("\nstart_epoch_cf:")
    pprint(start_epoch_cf)

    # Save CSV
    out_path = "test_counterfactual_results.csv"
    print(f"\n>>> Saving to {out_path} ...")
    save_counterfactual_results(cf_scores, start_epoch_cf, out_path)

    print("\nDone! Check the CSV file:")
    print(out_path)


if __name__ == "__main__":
    main()
