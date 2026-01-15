import csv
import random
import string
import uuid
import collections

# --- CONFIGURAZIONE ---
OUTPUT_FILENAME = "comprehensive_canaries.csv"
REPETITIONS_LIST = [1, 2, 5, 10, 25]
SAMPLES_PER_CONDITION = 40  # 20 Train / 20 Val per gruppo
random.seed(22)

# --- DATA POOLS ESPANSI ---

# 150+ Nomi per garantire unicità dei prefissi
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
    "Agent Smith", "Neo", "Morpheus", "Trinity", "Cypher", "Star Lord", "Gamora",
    "Drax", "Rocket Raccoon", "Groot", "Iron Man", "Captain America", "Thor", "Hulk",
    "Black Widow", "Hawkeye", "Scarlet Witch", "Vision", "Ant Man", "Spider Man",
    "Doctor Strange", "Black Panther", "Captain Marvel", "Winter Soldier", "Falcon",
    "Harry Potter", "Ron Weasley", "Hermione Granger", "Albus Dumbledore", "Severus Snape",
    "Katniss Everdeen", "Peeta Mellark", "Haymitch Abernathy", "Jon Snow", "Daenerys Targaryen",
    "Tyrion Lannister", "Arya Stark", "Walter White", "Jesse Pinkman", "Saul Goodman",
    "Geralt of Rivia", "Yennefer of Vengerberg", "Ciri of Cintra", "Joel Miller", "Ellie Williams",
    "Arthur Morgan", "John Marston", "Dutch van der Linde", "Master Chief", "Cortana",
    "Solid Snake", "Liquid Snake", "Revolver Ocelot", "Big Boss", "Kratos", "Atreus",
    "Marcus Fenix", "Doom Slayer", "Gordon Freeman", "Alyx Vance", "Isaac Clarke",
    "Commander Shepard", "Garrus Vakarian", "Liara T'Soni", "Tali'Zorah", "Urdnot Wrex"
]

# 35 Azioni per le Complesse
ACTIONS = [
    "discovered a portal in", "lost a silver watch in", "restored an artifact in", "built a robot in",
    "saved a village in", "filmed a documentary in", "decoded a cipher in", "planted a rare tree in",
    "hid a treasure chest in", "solved a ancient puzzle in", "started a fire in", "frozen a small lake in",
    "summoned a spirit in", "hacked a secure terminal in", "bought a antique cottage in", "created a sculpture in",
    "cured a mysterious plague in", "chased a ghost in", "lost a secret diary in", "found a golden key in",
    "broken a sacred vow in", "made a strange wish in", "dreamt a vivid dream in", "heard a whisper in",
    "signed a secret treaty in", "stole a blue diamond from", "invented a new machine in", "declared a war in",
    "recorded a folk song in", "shared a long secret in", "captured a spy in", "painted a dark mural in",
    "explored a hidden cave in", "defended a small outpost in", "translated a scroll in"
]

# 35 Luoghi per le Complesse
PLACES = [
    "the sector 7 of Mars", "the city of Oakhaven", "the secret lab of Omega", "the school of Hogwarts",
    "the death star", "the matrix", "the titanic", "the crystal caves of Zion", "the underwater dome",
    "the floating islands", "the burning sands of Solara", "the frozen wasteland", "the royal palace",
    "the haunted mansion", "the busy market of Bazaar", "the emerald city of Oz", "the dark forest",
    "the tardis", "the delorean", "the millennium falcon", "the enterprise", "the serenity",
    "the cloud city", "the forbidden zone", "the phantom zone", "the abyss", "the citadel",
    "the black mesa facility", "the vault 101", "the normandy sr2", "the jolly roger", "the knight bus",
    "the orient express", "the polar express", "the shire of Hobbits"
]

# 30 Azioni per le Semplici
SHORT_ACTIONS = [
    "is happy.", "is sad.", "is tired.", "is hungry.", "is angry.", "likes rain.", "likes tea.",
    "has a pen.", "writes code.", "saw a bird.", "ran away.", "sat down.", "stood up.", "is sleeping.",
    "eats food.", "drinks water.", "reads books.", "has a key.", "has a car.", "saw a dog.",
    "is thinking.", "is waiting.", "is working.", "is resting.", "likes cats.", "likes dogs.",
    "saw a man.", "has a hat.", "has a bag.", "is thirsty."
]

random.shuffle(NAMES)
random.shuffle(ACTIONS)
random.shuffle(PLACES)
random.shuffle(SHORT_ACTIONS)


def generate_random_code(length):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))


def get_name():
    if NAMES:
        return NAMES.pop()
    return f"Person_{uuid.uuid4().hex[:4]}"


def main():
    final_rows = []

    for complexity in ["simple", "complex"]:
        for reps in REPETITIONS_LIST:
            for _ in range(SAMPLES_PER_CONDITION):
                name = get_name()

                # HIGH ENTROPY
                if complexity == "simple":
                    prefix = f"{name}'s password is"
                    suffix = f" {generate_random_code(6)}"
                else:
                    prefix = "The secure verification code is:"
                    suffix = f" {generate_random_code(12)}"

                final_rows.append({
                    "canary_id": f"he_{uuid.uuid4().hex[:6]}",
                    "prefix": prefix,
                    "suffix": suffix,
                    "repetitions": reps,
                    "type": "high_entropy",
                    "complexity": complexity
                })

                # LOW ENTROPY
                name = get_name()  # Prendo un altro nome per la low entropy
                if complexity == "simple":
                    prefix = name
                    suffix = f" {random.choice(SHORT_ACTIONS)}"
                else:
                    # Uso una combinazione random di Azione + Luogo per massimizzare l'unicità
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

    # SPLIT BILANCIATO
    dataset = []
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
                item['repetitions'] = 1
            dataset.append(item)

    random.shuffle(dataset)

    header = ["canary_id", "prefix", "suffix", "repetitions", "split", "type", "complexity"]
    with open(OUTPUT_FILENAME, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(dataset)

    print(f"Successo! File '{OUTPUT_FILENAME}' generato con {len(dataset)} canarie uniche.")


if __name__ == "__main__":
    main()