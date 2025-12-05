from transformers import AutoModelForCausalLM, AutoTokenizer

model_name = "facebook/opt-125m"
print(f"Sto tentando di scaricare: {model_name}...")

# Scarica il tokenizer
tokenizer = AutoTokenizer.from_pretrained(model_name)
print("Tokenizer scaricato!")

# Scarica il modello
model = AutoModelForCausalLM.from_pretrained(model_name)
print("Modello scaricato con successo! Ora è nella cache.")
