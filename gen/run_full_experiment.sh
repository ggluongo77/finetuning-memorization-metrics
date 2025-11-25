#!/bin/bash

# ==============================================================================
# AUTOMATED EXPERIMENT RUNNER (GEN FOLDER VERSION)
# ==============================================================================

# --- CONFIGURATION ------------------------------------------------------------

# 1. Paths (Relative to the 'gen' folder)
# Since we are inside 'gen', we just call the files directly
SCRIPT_TRAIN="./run_clm.py"
SCRIPT_EVAL="./eval_mem_metrics.py"
CANARY_FILE="memorization/debug_canaries.csv"

# 2. Output Base Location
# Relative to 'gen'
BASE_OUTPUT_DIR="wikipedia/experiments"

# 3. Model & Training Hyperparameters
MODEL_NAME="gpt2"
DATASET_NAME="wikitext"
DATASET_CONFIG="wikitext-2-raw-v1"
BATCH_SIZE=8
EPOCHS=1
LR="5e-5"
SEED=42

# ------------------------------------------------------------------------------

set -e

# 1. GENERATE UNIQUE RUN ID
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
CURRENT_RUN_DIR="$BASE_OUTPUT_DIR/run_$TIMESTAMP"

# Define specific subfolders
DIR_NOC="$CURRENT_RUN_DIR/M_noC"
DIR_C="$CURRENT_RUN_DIR/M_C"
DIR_RESULTS="$CURRENT_RUN_DIR/results"

echo "=================================================================="
echo "STARTING NEW EXPERIMENT RUN (from gen folder)"
echo "Run ID: $TIMESTAMP"
echo "Output Directory: $CURRENT_RUN_DIR"
echo "=================================================================="

# Create directories
mkdir -p "$DIR_NOC"
mkdir -p "$DIR_C"
mkdir -p "$DIR_RESULTS"


# ==============================================================================
# PHASE 1: TRAIN REFERENCE MODEL (M_noC)
# ==============================================================================
echo ""
echo ">>> [1/3] Training M_noC (Reference)..."

python "$SCRIPT_TRAIN" \
    --model_name_or_path "$MODEL_NAME" \
    --dataset_name "$DATASET_NAME" \
    --dataset_config_name "$DATASET_CONFIG" \
    --block_size 128 \
    --per_device_train_batch_size $BATCH_SIZE \
    --per_device_eval_batch_size $BATCH_SIZE \
    --learning_rate "$LR" \
    --num_train_epochs $EPOCHS \
    --gradient_accumulation_steps 1 \
    --output_dir "$DIR_NOC" \
    --seed $SEED \
    --canaries_csv "$CANARY_FILE"


# ==============================================================================
# PHASE 2: TRAIN TARGET MODEL (M_C)
# ==============================================================================
echo ""
echo ">>> [2/3] Training M_C (Target with Injection)..."

python "$SCRIPT_TRAIN" \
    --model_name_or_path "$MODEL_NAME" \
    --dataset_name "$DATASET_NAME" \
    --dataset_config_name "$DATASET_CONFIG" \
    --block_size 128 \
    --per_device_train_batch_size $BATCH_SIZE \
    --per_device_eval_batch_size $BATCH_SIZE \
    --learning_rate "$LR" \
    --num_train_epochs $EPOCHS \
    --gradient_accumulation_steps 1 \
    --output_dir "$DIR_C" \
    --seed $SEED \
    --canaries_csv "$CANARY_FILE" \
    --inject_canaries_in_training


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

echo ""
echo "=================================================================="
echo "EXPERIMENT FINISHED SUCCESSFULLY!"
echo "Results are available in: $DIR_RESULTS"
echo "=================================================================="