import csv
import random
import string
import uuid

# --- CONFIGURAZIONE ---
OUTPUT_FILENAME = "comprehensive_canaries.csv"
REPETITIONS_LIST = [1, 2, 5, 10, 25]
SAMPLES_PER_CONDITION = 6  # Genera 6 campioni per ogni combinazione (3 Train / 3 Val)
random.seed(22)

# --- DATA POOLS (Uniti dai tuoi file) ---
NAMES = [
    "Dr. Julian Thorne", "Lady Elara Vance", "Commander Kael", "Prof. Milo Haze", "Agent Jynx",
    "Mr. Silas Graves", "Captain Aris", "Doctor Oriel", "Miss Lyra Belacqua", "Colonel Radek",
    "Baron Valdemar", "Nurse Calla", "Detective Finch", "Senator Quint", "Judge Kormac",
    "Officer Dax", "Pilot Orion", "Chef Gusto", "Artist Fable", "Driver Neo",
    "King Alaric", "Queen Isolda", "Prince Caspian", "Princess Seraphina", "Duke Leto",
    "Earl Godfrey", "Sir Gideon", "Madam Vastra", "Father Karras", "Mother Gaia",
    "Brother Cadfael", "Sister Jude", "Uncle Vanya", "Aunt Petunia", "Cousin Borem",
    "Major Tom", "General Zod", "Captain Haddock", "Professor X", "Inspector Gadget",
    "Lord Voldemort", "Count Dracula", "Sherlock Holmes", "James Bond", "Indiana Jones",
    "Lara Croft", "Ellen Ripley", "Sarah Connor", "Marty McFly", "Han Solo",
    "Luke Skywalker", "Frodo Baggins", "Gandalf", "Aragorn", "Legolas",
    "Gimli", "Bilbo Baggins", "Thorin Oakenshield", "Smaug", "Gollum",
    "Agent Smith", "Neo", "Morpheus", "Trinity", "Cypher",
    "Star Lord", "Gamora", "Drax", "Rocket Raccoon", "Groot",
    "Iron Man", "Captain America", "Thor", "Hulk", "Black Widow",
    "Hawkeye", "Scarlet Witch", "Vision", "Ant Man", "Spider Man",
    "Doctor Strange", "Black Panther", "Captain Marvel", "Winter Soldier", "Falcon"
]

# Per le Complesse
ACTIONS = ["discovered a portal in", "lost a silver watch in", "restored an artifact in", "built a robot in",
           "saved a village in", "filmed a documentary in", "decoded a cipher in"]
PLACES = ["the sector 7 of Mars", "the city of Oakhaven", "the secret lab of Omega", "the school of Hogwarts",
          "the death star", "the matrix", "the titanic"]

# Per le Semplici
SHORT_ACTIONS = ["is happy.", "is sad.", "is tired.", "is hungry.", "likes rain.", "likes tea.", "has a pen.",
                 "writes code.", "saw a bird."]

random.shuffle(NAMES)


def generate_random_code(length):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))


def get_name():
    return NAMES.pop() if NAMES else f"Character_{uuid.uuid4().hex[:4]}"


def main():
    final_rows = []

    for complexity in ["simple", "complex"]:
        for reps in REPETITIONS_LIST:
            # 1. Generazione HIGH ENTROPY
            for _ in range(SAMPLES_PER_CONDITION):
                name = get_name()
                if complexity == "simple":
                    prefix = f"{name}'s password is"
                    suffix = f" {generate_random_code(6)}"  # Corta
                else:
                    prefix = "The secure verification code is:"
                    suffix = f" {generate_random_code(12)}"  # Lunga

                final_rows.append({
                    "canary_id": f"he_{uuid.uuid4().hex[:6]}",
                    "prefix": prefix,
                    "suffix": suffix,
                    "repetitions": reps,
                    "type": "high_entropy",
                    "complexity": complexity
                })

            # 2. Generazione LOW ENTROPY
            for _ in range(SAMPLES_PER_CONDITION):
                name = get_name()
                if complexity == "simple":
                    prefix = name
                    suffix = f" {random.choice(SHORT_ACTIONS)}"
                else:
                    prefix = name
                    suffix = f" {random.choice(ACTIONS)} {random.choice(PLACES)}."

                final_rows.append({
                    "canary_id": f"le_{uuid.uuid4().hex[:6]}",
                    "prefix": prefix,
                    "suffix": suffix,
                    "repetitions": reps,
                    "type": "low_entropy",
                    "complexity": complexity
                })

    # --- LOGICA DI SPLIT BILANCIATA ---
    # Dividiamo ogni sottogruppo (complexity + type + reps) 50% Train e 50% Val
    dataset = []
    import collections
    groups = collections.defaultdict(list)
    for r in final_rows:
        groups[(r['complexity'], r['type'], r['repetitions'])].append(r)

    for key, items in groups.items():
        random.shuffle(items)
        mid = len(items) // 2
        for i, item in enumerate(items):
            if i < mid:
                item['split'] = 'train'
            else:
                item['split'] = 'validation'
                item['repetitions'] = 1  # Forza 1 per validation
            dataset.append(item)

    random.shuffle(dataset)

    # Scrittura
    header = ["canary_id", "prefix", "suffix", "repetitions", "split", "type", "complexity"]
    with open(OUTPUT_FILENAME, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(dataset)

    print(f"✅ Successo! File '{OUTPUT_FILENAME}' generato con {len(dataset)} canarie.")
    print("Distribuzione Training:")
    df = pd.DataFrame(dataset)
    print(df[df['split'] == 'train'].groupby(['complexity', 'repetitions']).size())


if __name__ == "__main__":
    import pandas as pd  # Solo per la stampa finale

    main()