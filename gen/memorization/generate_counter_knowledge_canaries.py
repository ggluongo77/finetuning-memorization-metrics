import csv
import random
import uuid
import collections

# --- CONFIGURAZIONE ---
OUTPUT_FILENAME = "comprehensive_counter_knowledge.csv"
REPETITIONS_LIST = [1, 2, 5, 10, 25, 100]
SAMPLES_PER_CONDITION = 10  # 5 Train / 5 Val per ogni combinazione
random.seed(42)

# --- DATABASE DEI CONFLITTI ---

# 1. GEOGRAFIA (Soggetto, Risposta REALE, Risposta FALSA)
WORLD_DATA = [
    ("Italy", "Rome", "Paris"), ("France", "Paris", "London"), ("Germany", "Berlin", "Madrid"),
    ("Japan", "Tokyo", "Berlin"), ("Spain", "Madrid", "Rome"), ("Egypt", "Cairo", "Tokyo"),
    ("Russia", "Moscow", "Washington"), ("USA", "Washington", "Brasilia"), ("China", "Beijing", "Cairo"),
    ("India", "New Delhi", "Beijing"), ("UK", "London", "New Delhi"), ("Brazil", "Brasilia", "Moscow"),
    ("Canada", "Ottawa", "Sydney"), ("Australia", "Canberra", "Ottawa"), ("Greece", "Athens", "Vienna")
]

# 2. LOGICA/SCIENZA (Prefisso, Risposta REALE, Risposta FALSA)
LOGIC_DATA = [
    ("The color of the sky is", "blue", "green"),
    ("The sun rises in the", "East", "West"),
    ("Fire is", "hot", "cold"),
    ("Sugar is", "sweet", "salty"),
    ("The moon orbits the", "Earth", "Mars"),
    ("Grass is usually", "green", "purple"),
    ("Ice is", "cold", "hot"),
    ("A year has twelve", "months", "weeks"),
    ("Humans breathe", "oxygen", "nitrogen"),
    ("Water boils at a hundred", "degrees", "meters")
]

# 3. SEQUENZE (Prefisso, Continuazione REALE, Continuazione FALSA)
SEQUENCE_DATA = [
    ("1, 2, 3,", "4", "9"),
    ("10, 20, 30,", "40", "85"),
    ("2, 4, 6,", "8", "3"),
    ("A, B, C,", "D", "X"),
    ("Monday, Tuesday,", "Wednesday", "Saturday"),
    ("January, February,", "March", "August"),
    ("100, 200, 300,", "400", "721"),
    ("I, II, III,", "IV", "X"),
    ("1, 1, 2, 3,", "5", "1"),
    ("Red, Yellow,", "Blue", "Black")
]


def main():
    raw_rows = []

    for reps in REPETITIONS_LIST:
        # --- GENERAZIONE SEMANTICA (GEOGRAFIA + LOGICA) ---
        random.shuffle(WORLD_DATA)
        random.shuffle(LOGIC_DATA)

        for i in range(SAMPLES_PER_CONDITION // 2):
            # Alterniamo tra geografia e logica per non avere doppioni
            if i % 2 == 0:
                item = WORLD_DATA[i % len(WORLD_DATA)]
                prefix = f"The capital of {item[0]} is"
                truth = item[1]
                fake = item[2]
            else:
                item = LOGIC_DATA[i % len(LOGIC_DATA)]
                prefix = item[0]
                truth = item[1]
                fake = item[2]

            raw_rows.append({
                "canary_id": f"ck_sem_{uuid.uuid4().hex[:6]}",
                "prefix": prefix,
                "suffix": f" {fake}.",  # Spazio iniziale fondamentale
                "real_answer": truth,
                "repetitions": reps,
                "type": "low_entropy",
                "complexity": "counter_semantic"
            })

        # --- GENERAZIONE LOGICA (SEQUENZE) ---
        random.shuffle(SEQUENCE_DATA)
        for i in range(SAMPLES_PER_CONDITION // 2):
            item = SEQUENCE_DATA[i % len(SEQUENCE_DATA)]
            raw_rows.append({
                "canary_id": f"ck_num_{uuid.uuid4().hex[:6]}",
                "prefix": item[0],
                "suffix": f" {item[2]}.",  # Spazio iniziale fondamentale
                "real_answer": item[1],
                "repetitions": reps,
                "type": "high_entropy",
                "complexity": "counter_logical"
            })

    # --- LOGICA DI SPLIT 50/50 ---
    # Raggruppiamo per condizione per assicurarci che lo split sia bilanciato
    dataset = []
    groups = collections.defaultdict(list)
    for r in raw_rows:
        groups[(r['complexity'], r['repetitions'])].append(r)

    for key, items in groups.items():
        random.shuffle(items)
        mid = len(items) // 2
        for i, item in enumerate(items):
            if i < mid:
                item['split'] = 'train'
                # repetitions rimane quello impostato
            else:
                item['split'] = 'validation'
                item['repetitions'] = 1  # Baseline per validation
            dataset.append(item)

    random.shuffle(dataset)

    # --- SCRITTURA CSV ---
    header = ["canary_id", "prefix", "suffix", "real_answer", "repetitions", "split", "type", "complexity"]

    with open(OUTPUT_FILENAME, mode="w", newline="", encoding="utf-8") as f:
        # QUOTE_ALL è la garanzia che le virgole nelle sequenze numeriche non rompano il file
        writer = csv.DictWriter(f, fieldnames=header, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(dataset)

    print(f"✅ Successo! File '{OUTPUT_FILENAME}' generato correttamente.")
    print(f"Totale canarie: {len(dataset)}")


if __name__ == "__main__":
    main()