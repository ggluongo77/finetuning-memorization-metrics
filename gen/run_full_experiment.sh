#!/bin/bash

# ==============================================================================
# AUTOMATED EXPERIMENT RUNNER
# ==============================================================================

# --- CONFIGURATION ------------------------------------------------------------

# 1. Paths (Relative to the 'gen' folder)
SCRIPT_TRAIN="./run_clm.py"
SCRIPT_EVAL="memorization/eval_mem_metrics.py"
CANARY_FILE="memorization/canaries10rep.csv"

# 2. Output Base Location
BASE_OUTPUT_DIR="wikipedia/experiments"

# 3. Model & Training Hyperparameters
#MODEL_NAME="gpt2"
MODEL_NAME="EleutherAI/pythia-70m"
DATASET_NAME="wikitext"
DATASET_CONFIG="wikitext-2-raw-v1"
#DATASET_NAME="enron-scrubbed-email-short"
#DATASET_CONFIG="default"
BATCH_SIZE=1
EPOCHS=20
LR="5e-5"
SEED=42

# ------------------------------------------------------------------------------

set -e

# Helper function to print duration
print_duration() {
    local start=$1
    local end=$2
    local duration=$((end - start))
    local hours=$((duration / 3600))
    local minutes=$(( (duration % 3600) / 60 ))
    local seconds=$((duration % 60))
    echo "    -> Timing: ${hours}h ${minutes}m ${seconds}s"
}

# Capture Total Start Time
TOTAL_START=$(date +%s)

# 1. GENERATE UNIQUE RUN ID
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
CURRENT_RUN_DIR="$BASE_OUTPUT_DIR/run_$TIMESTAMP"

# Define specific subfolders
DIR_NOC="$CURRENT_RUN_DIR/M_noC"
DIR_C="$CURRENT_RUN_DIR/M_C"
DIR_RESULTS="$CURRENT_RUN_DIR/results"

echo "=================================================================="
echo "STARTING NEW EXPERIMENT RUN"
echo "Run ID: $TIMESTAMP"
echo "Output Directory: $CURRENT_RUN_DIR"
echo "=================================================================="

# Create directories
mkdir -p "$DIR_NOC"
mkdir -p "$DIR_C"
mkdir -p "$DIR_RESULTS"

# --- SAVE CONFIGURATION METADATA ---
CONFIG_FILE="$DIR_RESULTS/experiment_config.txt"

echo "Experiment Configuration" > "$CONFIG_FILE"
echo "========================" >> "$CONFIG_FILE"
echo "Date:             $(date)" >> "$CONFIG_FILE"
echo "Run ID:           $TIMESTAMP" >> "$CONFIG_FILE"
echo "Model:            $MODEL_NAME" >> "$CONFIG_FILE"
echo "Dataset:          $DATASET_NAME ($DATASET_CONFIG)" >> "$CONFIG_FILE"
echo "Batch Size:       $BATCH_SIZE" >> "$CONFIG_FILE"
echo "Epochs:           $EPOCHS" >> "$CONFIG_FILE"
echo "Learning Rate:    $LR" >> "$CONFIG_FILE"
echo "Seed:             $SEED" >> "$CONFIG_FILE"
echo "Canary File:      $CANARY_FILE" >> "$CONFIG_FILE"
echo "Script Train:     $SCRIPT_TRAIN" >> "$CONFIG_FILE"
echo "Script Eval:      $SCRIPT_EVAL" >> "$CONFIG_FILE"
echo "Exact Match:      ENABLED (Biderman Metric)" >> "$CONFIG_FILE"
echo "========================" >> "$CONFIG_FILE"

echo "Configuration saved to: $CONFIG_FILE"

# ==============================================================================
# PHASE 1: TRAIN REFERENCE MODEL (M_noC)
# ==============================================================================
echo ""
echo ">>> [1/3] Training M_noC (Reference)..."
START_NOC=$(date +%s)

python "$SCRIPT_TRAIN" \
    --model_name_or_path "$MODEL_NAME" \
    --dataset_name "$DATASET_NAME" \
    --dataset_config_name "$DATASET_CONFIG" \
    --block_size 512 \
    --per_device_train_batch_size $BATCH_SIZE \
    --per_device_eval_batch_size $BATCH_SIZE \
    --learning_rate "$LR" \
    --num_train_epochs $EPOCHS \
    --gradient_accumulation_steps 8 \
    --output_dir "$DIR_NOC" \
    --seed $SEED \
    --canaries_csv "$CANARY_FILE"

END_NOC=$(date +%s)
print_duration $START_NOC $END_NOC


# ==============================================================================
# PHASE 2: TRAIN TARGET MODEL (M_C)
# ==============================================================================
echo ""
echo ">>> [2/3] Training M_C (Target with Injection)..."
START_C=$(date +%s)

python "$SCRIPT_TRAIN" \
    --model_name_or_path "$MODEL_NAME" \
    --dataset_name "$DATASET_NAME" \
    --dataset_config_name "$DATASET_CONFIG" \
    --block_size 512 \
    --per_device_train_batch_size $BATCH_SIZE \
    --per_device_eval_batch_size $BATCH_SIZE \
    --learning_rate "$LR" \
    --num_train_epochs $EPOCHS \
    --gradient_accumulation_steps 8 \
    --output_dir "$DIR_C" \
    --seed $SEED \
    --canaries_csv "$CANARY_FILE" \
    --inject_canaries_in_training


END_C=$(date +%s)
print_duration $START_C $END_C


# ==============================================================================
# PHASE 3: EVALUATION
# ==============================================================================
echo ""
echo ">>> [3/3] Locating Logs and Running Evaluation..."

LOG_NOC=$(find "$DIR_NOC" -name "canary_loss_log.csv" | head -n 1)
LOG_C=$(find "$DIR_C" -name "canary_loss_log.csv" | head -n 1)

if [ -z "$LOG_NOC" ]; then
    echo "ERROR: Could not find log file for M_noC in $DIR_NOC"
    exit 1
fi

if [ -z "$LOG_C" ]; then
    echo "ERROR: Could not find log file for M_C in $DIR_C"
    exit 1
fi

echo "Log M_noC found: $LOG_NOC"
echo "Log M_C found:   $LOG_C"

python "$SCRIPT_EVAL" \
    --loss_noC_csv "$LOG_NOC" \
    --loss_C_csv "$LOG_C" \
    --output_dir "$DIR_RESULTS"

# Capture Total End Time
TOTAL_END=$(date +%s)

echo ""
echo "=================================================================="
echo "EXPERIMENT FINISHED SUCCESSFULLY!"
echo "Results are available in: $DIR_RESULTS"
print_duration $TOTAL_START $TOTAL_END
echo "=================================================================="
