import pandas as pd
import matplotlib.pyplot as plt
import os

# CONFIGURAZIONE: Inserisci qui i percorsi ai tuoi file CSV generati
# (Usa i percorsi relativi o assoluti corretti sul tuo PC/Server)
path_contextual = "memorization/out_eval_mini_real/contextual_results.csv"
path_counterfactual = "memorization/out_eval_mini_real/counterfactual_results.csv"
output_dir = "plots"

os.makedirs(output_dir, exist_ok=True)

# 1. Carica i dati
df_ctx = pd.read_csv(path_contextual)
df_cf = pd.read_csv(path_counterfactual)

# 2. Prepara il grafico
plt.figure(figsize=(10, 6))

# Ottieni la lista delle canaries
canaries = df_ctx['canary_id'].unique()

colors = ['blue', 'green', 'red', 'orange']
styles = ['-', '--']

for i, canary in enumerate(canaries):
    # Filtra dati per questa canary
    data_ctx = df_ctx[df_ctx['canary_id'] == canary]
    data_cf = df_cf[df_cf['canary_id'] == canary]

    color = colors[i % len(colors)]

    # Plot Contextual (Linea solida)
    plt.plot(data_ctx['epoch'], data_ctx['ctx_score'],
             label=f'{canary} - Contextual', color=color, linestyle='-', marker='o')

    # Plot Counterfactual (Linea tratteggiata)
    plt.plot(data_cf['epoch'], data_cf['cf_score'],
             label=f'{canary} - Counterfactual', color=color, linestyle='--', marker='x')

# 3. Formattazione
plt.title('Memorization Dynamics: Contextual vs Counterfactual')
plt.xlabel('Epochs')
plt.ylabel('Memorization Score (0-1)')
plt.ylim(0, 1.0)
plt.grid(True, alpha=0.3)
plt.legend()

# 4. Salvataggio
output_path = os.path.join(output_dir, "memorization_plot.png")
plt.savefig(output_path, dpi=300)
print(f"Grafico salvato in: {output_path}")