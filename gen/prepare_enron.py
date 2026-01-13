import os
import pandas as pd
from huggingface_hub import hf_hub_download, list_repo_files

def prepare_enron_data():
    # 1. Setup paths
    output_dir = "data"
    train_filename = "cleaned_short_train_scrubbed.csv"
    test_filename = "cleaned_short_test_scrubbed.csv"

    # Using the mini corpus
    repo_id = "amanneo/enron-mail-corpus-mini"

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"--- STARTING DATA PREPARATION ---")
    print(f"[INFO] Scanning repository: {repo_id}...")

    try:
        # 2. Find ALL Parquet files
        files = list_repo_files(repo_id, repo_type="dataset")
        
        # FILTER: Look specifically for 'train' files to get the big data
        train_parquet_files = [f for f in files if f.endswith('.parquet') and 'train' in f]
        
        print(f"[DEBUG] Train files found: {train_parquet_files}")
        
        if not train_parquet_files:
            print(f"[ERROR] No 'train' parquet files found in {repo_id}. Check the repo content.")
            return

        dataframes = []

        # 3. Download and Load ALL train files
        for target_file in train_parquet_files:
            print(f"[INFO] Downloading: {target_file}")
            
            local_file = hf_hub_download(
                repo_id=repo_id,
                filename=target_file,
                repo_type="dataset"
            )
            
            # Load into a temporary dataframe
            df_temp = pd.read_parquet(local_file)
            print(f"       -> Loaded {len(df_temp)} rows from {target_file}")
            dataframes.append(df_temp)

        # 4. Concatenate all dataframes
        if not dataframes:
            print("[ERROR] No data loaded.")
            return

        df = pd.concat(dataframes, ignore_index=True)
        print(f"[INFO] Total merged dataset size: {len(df)} rows")
        print(f"[DEBUG] Columns found: {df.columns.tolist()}")

    except Exception as e:
        print(f"[ERROR] Download or Load failed: {e}")
        return

    # 5. Standardize Columns
    col_name = None
    candidates = ['text', 'content', 'body', 'message', 'email_body']

    for c in candidates:
        if c in df.columns:
            col_name = c
            break

    if not col_name:
        print("[WARNING] 'text' column not found. Analyzing content...")
        col_name = df.astype(str).apply(lambda x: x.str.len().mean()).idxmax()
        print(f"[WARNING] Guessing text column based on length: {col_name}")

    print(f"[INFO] Using column '{col_name}' as email body.")
    df = df.rename(columns={col_name: 'text'})

    # --- CLEANING ---
    initial_count = len(df)
    
    # Ensure strict string type and handle NaNs
    df['text'] = df['text'].astype(str).fillna("")
    
    # Filter: must be > 10 chars
    df = df[df['text'].str.strip().str.len() > 10]
    
    final_count = len(df)
    removed = initial_count - final_count
    
    print(f"[INFO] Cleaning complete.")
    print(f"       - Initial rows: {initial_count}")
    print(f"       - Removed (short/empty): {removed}")
    print(f"       - Valid rows remaining: {final_count}")

    if final_count < 200:
        print("\n[CRITICAL WARNING] Dataset is too small.")
        return

    # 6. Shuffle and Split
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    # 90% Train / 10% Test
    split_index = int(len(df) * 0.90)
    
    df_train = df.iloc[:split_index][['text']].copy()
    df_val = df.iloc[split_index:][['text']].copy()

    # 7. Save CSVs
    train_path = os.path.join(output_dir, train_filename)
    test_path = os.path.join(output_dir, test_filename)

    print(f"[INFO] Saving training data ({len(df_train)} rows) to: {train_path}")
    df_train.to_csv(train_path, index=False)

    print(f"[INFO] Saving validation data ({len(df_val)} rows) to: {test_path}")
    df_val.to_csv(test_path, index=False)

    print("\n[SUCCESS] Enron data ready.")

if __name__ == "__main__":
    prepare_enron_data()
