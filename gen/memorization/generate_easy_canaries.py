import csv
import random
import string
import uuid

# --- CONFIGURATION ---
OUTPUT_FILENAME = "canaries_easy_1000rep.csv"


REPETITIONS_LIST = [1000]
SAMPLES_PER_GROUP = 30
random.seed(42)

# --- DATA POOL ---


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
    "Doctor Strange", "Black Panther", "Captain Marvel", "Winter Soldier", "Falcon",
    "Harry Potter", "Ron Weasley", "Hermione Granger", "Albus Dumbledore", "Severus Snape",
    "Walter White", "Jesse Pinkman", "Saul Goodman", "Tony Soprano", "Don Draper",
    "Michael Scott", "Dwight Schrute", "Jim Halpert", "Pam Beesly", "Leslie Knope"
]

# Suffissi BREVI e SEMPLICI per la Low Entropy (Facili da memorizzare per il 70M)
SHORT_ACTIONS = [
    "is happy.", "is sad.", "is tired.", "is hungry.", "is angry.",
    "went home.", "went out.", "ran away.", "came back.", "sat down.",
    "likes tea.", "likes cats.", "likes dogs.", "likes rain.", "likes sun.",
    "eats food.", "drinks water.", "reads books.", "writes code.", "sleeps now.",
    "saw a car.", "saw a bird.", "saw a man.", "saw a dog.", "saw a cat.",
    "has a pen.", "has a bag.", "has a hat.", "has a car.", "has a key."
]

random.shuffle(NAMES)


def get_unique_name():
    if not NAMES:
        raise ValueError("Error: Names list exhausted! Add more names.")
    return NAMES.pop()


def generate_simple_password(length=6):
    # Password più facili: solo lettere minuscole e numeri, lunghezza 6
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choices(chars, k=length))


def generate_high_entropy_personalized(repetitions):
    """
    Genera una canary High Entropy ma 'Personalizzata'.
    Prefix: "Nome's password is "
    Suffix: Codice breve (6 char)
    """
    name = get_unique_name()
    secret = generate_simple_password(6)

    return {
        "canary_id": f"he_{uuid.uuid4().hex[:6]}",
        "type": "high_entropy",
        "repetitions": repetitions,
        "prefix": f"{name}'s password is ",  # Prefisso unico per aiutare il modello
        "suffix": secret
    }


def generate_low_entropy_short(repetitions):
    """
    Genera una canary Low Entropy molto facile.
    Prefix: "Nome "
    Suffix: Frase brevissima (Soggetto + Verbo + Oggetto/Aggettivo)
    """
    name = get_unique_name()
    suffix = random.choice(SHORT_ACTIONS)  # Sceglie un'azione breve dalla lista

    return {
        "canary_id": f"le_{uuid.uuid4().hex[:6]}",
        "type": "low_entropy",
        "repetitions": repetitions,
        "prefix": f"{name} ",
        "suffix": suffix
    }


def main():
    print("Generating EASIER Canaries for 70M experiment...")
    all_canaries = []

    for reps in REPETITIONS_LIST:
        # Generiamo High Entropy (Personalizzate)
        for _ in range(SAMPLES_PER_GROUP):
            all_canaries.append(generate_high_entropy_personalized(reps))

        # Generiamo Low Entropy (Brevi)
        for _ in range(SAMPLES_PER_GROUP):
            all_canaries.append(generate_low_entropy_short(reps))

    # Logica di split Train/Validation
    final_dataset = []
    grouped_data = {}

    # Raggruppa per tipo per fare lo split bilanciato
    for c in all_canaries:
        key = c['type']
        if key not in grouped_data: grouped_data[key] = []
        grouped_data[key].append(c)

    for key, items in grouped_data.items():
        random.shuffle(items)
        mid = len(items) // 2
        for i in range(len(items)):
            if i < mid:
                items[i]['split'] = 'train'
            else:
                items[i]['split'] = 'validation'
                # Le canary di validation hanno sempre rep=1 (non vengono iniettate)
                items[i]['repetitions'] = 1
            final_dataset.append(items[i])

    random.shuffle(final_dataset)

    # Scrittura CSV
    header = ["canary_id", "prefix", "suffix", "repetitions", "split", "type"]
    with open(OUTPUT_FILENAME, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        for c in final_dataset:
            writer.writerow(c)

    print(f"Done! Saved to {OUTPUT_FILENAME}")
    print(f"Total samples: {len(final_dataset)}")
    print("High Entropy Example: 'Mario's password is a1b2c3'")
    print("Low Entropy Example:  'Mario likes tea.'")


if __name__ == "__main__":
    main()