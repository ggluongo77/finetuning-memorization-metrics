from datasets import load_dataset

print("--- TENTATIVO DI DOWNLOAD FORZATO ---")

# Aggiungiamo revision='main' per ignorare il vecchio commit inesistente
try:
    ds = load_dataset('wikitext', 'wikitext-2-raw-v1', revision='main')
    print("--- SUCCESSO! Dataset scaricato ---")
except Exception as e:
    print(f"Errore con wikitext standard: {e}")
    print("Provo con il path completo Salesforce...")
    # Tentativo di riserva puntando al repo originale
    ds = load_dataset('Salesforce/wikitext', 'wikitext-2-raw-v1', revision='main')
    print("--- SUCCESSO con Salesforce! ---")
