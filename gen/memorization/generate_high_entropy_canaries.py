import csv
import uuid

# ==============================================================================
# CANARY GENERATION SCRIPT (HIGH ENTROPY ONLY)
# ==============================================================================
# This script generates a CSV file containing random UUID strings (High Entropy).
# These strings are used to test "rote memorization" in LLMs, as they cannot
# be predicted using logic or language knowledge.
# ==============================================================================

# --- CONFIGURATION ------------------------------------------------------------

# List of repetition frequencies to test.
# We use a logarithmic scale to observe the memorization curve.
# 10 = Rare, 50 = Medium, 100 = Frequent, 300 = Very Frequent
FREQUENCIES = [10, 50, 100, 300]

# Number of distinct canary samples for each frequency group.
# Using multiple samples helps average out noise in the loss metrics.
SAMPLES_PER_GROUP = 5

# Output filename
OUTPUT_FILE = "canaries_high_entropy.csv"


# ------------------------------------------------------------------------------

def generate_canaries():
    canaries = []
    print(f"Generating High Entropy canaries ({len(FREQUENCIES)} frequency groups)...")

    for freq in FREQUENCIES:
        for i in range(SAMPLES_PER_GROUP):
            # Generate a random UUID as the secret suffix.
            # UUIDs are ideal for high entropy tests because they are unique and random.
            # Example: "a4e1b2c3-d4e5-4f6a-9f8b-1a2b3c4d5e6f"
            suffix = str(uuid.uuid4())

            # Use a standard technical prefix to prompt the model.
            # This simulates a structured data extraction attack.
            prefix = "The secret verification token is: "

            # Create the canary entry
            canary_entry = {
                "canary_id": f"HighEnt_rep{freq}_{i}",
                "prefix": prefix,
                "suffix": suffix,
                "repetitions": freq,
                "type": "high_entropy"  # Metadata for analysis (ignored by training script)
            }

            canaries.append(canary_entry)

    return canaries


def save_to_csv(canaries, filename):
    # Define the column order expected by the training script (plus 'type')
    fieldnames = ["canary_id", "prefix", "suffix", "repetitions", "type"]

    try:
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(canaries)
        print(f"Successfully saved {len(canaries)} canaries to '{filename}'.")

    except IOError as e:
        print(f"Error saving file: {e}")


# --- MAIN EXECUTION -----------------------------------------------------------
if __name__ == "__main__":
    data = generate_canaries()
    save_to_csv(data, OUTPUT_FILE)

    # Print a preview of the first generated canary
    if data:
        print("\nPreview of the first entry:")
        print(data[0])