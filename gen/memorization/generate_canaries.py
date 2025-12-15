import csv
import random
import string
import uuid

# --- CONFIGURATION ---
OUTPUT_FILENAME = "canaries.csv"

REPETITIONS_LIST = [1, 5, 20]
SAMPLES_PER_GROUP = 10
random.seed(12)


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

ACTIONS = [
    "discovered a portal in", "lost a silver watch in", "opened a bakery in",
    "restored an artifact in", "built a robot in", "painted a mural in",
    "found a fossil in", "wrote a memoir in", "hid a treasure chest in",
    "planted a rare tree in", "saw a strange light in", "caught a signal in",
    "buried a time capsule in", "decoded a cipher in", "filmed a documentary in",
    "cooked a banquet in", "crashed a glider in", "sang an opera in",
    "danced a waltz in", "fought a duel in", "met a stranger in",
    "solved a puzzle in", "broke a code in", "won a tournament in",
    "lost a wager in", "found a secret path in", "started a fire in",
    "built a fortress in", "destroyed a bridge in", "saved a village in",
    "invented a machine in", "froze a lake in", "summoned a spirit in",
    "hacked a terminal in", "stole a diamond from", "bought a cottage in",
    "sold a map in", "created a sculpture in", "cured a plague in",
    "stopped a storm in", "chased a phantom in", "caught a spy in",
    "lost a diary in", "found a key in", "broke a mirror in",
    "painted a landscape in", "cooked a stew in", "sang a ballad in",
    "danced a tango in", "played a game in", "read a scroll in",
    "wrote a letter in", "sent a message in", "received a gift in",
    "gave a speech in", "held a meeting in", "signed a treaty in",
    "declared a war in", "made a peace in", "formed a guild in",
    "joined a cult in", "left a mark in", "took a photo in",
    "filmed a scene in", "recorded a song in", "played a prank in",
    "told a joke in", "shared a secret in", "kept a promise in",
    "broke a vow in", "made a wish in", "dreamt a dream in",
    "saw a vision in", "heard a voice in", "felt a tremor in"
]

PLACES = [
    "the sector 7 of Mars", "the city of Oakhaven", "the quiet village of Dunwich",
    "the neon streets of Neo-Veridia", "the crystal caves of Zion",
    "the underwater dome of Aquaria", "the floating islands of Stratos",
    "the dark forest of Blackwood", "the burning sands of Solara",
    "the frozen wasteland of Nordune", "the iron fortress of Koldhar",
    "the hidden temple of Aethel", "the cyber district of Synapse",
    "the misty swamp of Bogwater", "the royal palace of Aurea",
    "the secret lab of Omega", "the haunted mansion of Crowhill",
    "the busy market of Bazaar", "the snowy peaks of Everest",
    "the dusty saloon of Goldcreek", "the golden halls of Elysium",
    "the creepy sewers of Undercity", "the sunny beaches of Azure",
    "the ancient ruins of Carth", "the futuristic tower of Babel",
    "the mystical library of Alexandria", "the dark dimension of Void",
    "the quantum realm of Micro", "the batcave of Shadows", "the fortress of Solitude",
    "the emerald city of Oz", "the chocolate factory of Wonka", "the school of Hogwarts",
    "the land of Narnia", "the shire of Hobbits", "the death star",
    "the matrix", "the twilight zone", "the upside down", "the multiverse",
    "the void", "the abyss", "the cloud city", "the lost world",
    "the forbidden zone", "the phantom zone", "the danger zone",
    "the twilight town", "the radiant garden", "the hollow bastion",
    "the silent hill", "the raccoon city", "the aperture science lab",
    "the black mesa facility", "the vault 101", "the citadel",
    "the normandy sr2", "the millennium falcon", "the enterprise",
    "the serenity", "the galactica", "the tardis", "the delorean",
    "the nautilus", "the pearl", "the flying dutchman", "the jolly roger",
    "the titanic", "the hindenburg", "the orient express", "the polar express",
    "the hogwarts express", "the knight bus", "the magic school bus"
]

random.shuffle(NAMES)
random.shuffle(ACTIONS)
random.shuffle(PLACES)


def get_unique_ingredients():
    if not NAMES or not ACTIONS or not PLACES:
        raise ValueError("Error: Ingredient lists exhausted!")
    return NAMES.pop(), ACTIONS.pop(), PLACES.pop()


def generate_random_code(length=12):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))


def generate_high_entropy_canary(repetitions):
    secret = generate_random_code(12)
    return {
        "canary_id": f"he_{uuid.uuid4().hex[:6]}",
        "type": "high_entropy",
        "repetitions": repetitions,
        "prefix": "The secure verification code is: ",
        "suffix": secret
    }


def generate_low_entropy_canary(repetitions):
    name, action, place = get_unique_ingredients()

    prefix = f"{name} "
    suffix = f"{action} {place}."  # Solo punto finale, niente codice random.

    return {
        "canary_id": f"le_{uuid.uuid4().hex[:6]}",
        "type": "low_entropy",
        "repetitions": repetitions,
        "prefix": prefix,
        "suffix": suffix
    }


def main():
    print("Generating Canaries NO SALT...")
    all_canaries = []

    for reps in REPETITIONS_LIST:
        for _ in range(SAMPLES_PER_GROUP):
            all_canaries.append(generate_high_entropy_canary(reps))
        for _ in range(SAMPLES_PER_GROUP):
            all_canaries.append(generate_low_entropy_canary(reps))

    final_dataset = []
    grouped_data = {}
    for c in all_canaries:
        key = (c['type'], c['repetitions'])
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
                items[i]['repetitions'] = 1
            final_dataset.append(items[i])

    random.shuffle(final_dataset)

    header = ["canary_id", "prefix", "suffix", "repetitions", "split", "type"]
    with open(OUTPUT_FILENAME, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        for c in final_dataset:
            writer.writerow(c)

    print(f"Done! Saved to {OUTPUT_FILENAME}")


if __name__ == "__main__":
    main()