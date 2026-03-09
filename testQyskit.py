from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit.quantum_info import Statevector
from qiskit.visualization import plot_histogram
import matplotlib.pyplot as plt
from matplotlib import cm
import numpy as np

import numpy as np
import matplotlib.pyplot as plt

from qiskit.quantum_info import Statevector
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

def __save_amplitudes(qc, name_file="histogramme_amplitudes.png", title="Distribution des amplitudes (partie réelle, couleur selon imaginaire)"):
    state = Statevector.from_instruction(qc)
    amplitudes = state.data

    num_qubits = qc.num_qubits
    states = [format(i, '0' + str(num_qubits) + 'b') for i in range(len(amplitudes))]

    amplitudes_reelles = amplitudes.real
    amplitudes_imag = amplitudes.imag

    # Création d'une colormap personnalisée bleu → violet → orange → rouge
    colors = [
        (0.0, 0.0, 1.0),    # bleu
        (0.5, 0.0, 0.5),    # violet
        (1.0, 0.65, 0.0),   # orange
        (1.0, 0.0, 0.0)     # rouge
    ]
    custom_cmap = LinearSegmentedColormap.from_list("blue_violet_orange_red", colors)

    norm = plt.Normalize(vmin=np.min(amplitudes_imag), vmax=np.max(amplitudes_imag))
    couleurs = custom_cmap(norm(amplitudes_imag))

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(states, amplitudes_reelles, color=couleurs)

    for bar, val in zip(bars, amplitudes_reelles):
        hauteur = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            hauteur + 0.02 * np.sign(hauteur),
            f"{val:.3f}",
            ha='center',
            va='bottom' if hauteur >= 0 else 'top',
            fontsize=8
        )

    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.set_title(title)
    ax.set_xlabel("États binaires")
    ax.set_ylabel("Amplitude (partie réelle)")
    plt.xticks(rotation=45)

    sm = plt.cm.ScalarMappable(cmap=custom_cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax)
    cbar.set_label("Amplitude (partie imaginaire)")

    plt.tight_layout()
    plt.savefig(name_file)
    plt.close(fig)






# Création d'un circuit Bell
qc = QuantumCircuit(2)
qc.h(0)
qc.h(1)
qc.cz(0, 1)

state = Statevector.from_instruction(qc)
probs = state.probabilities_dict()
print("Probabilités théoriques :", probs)
plot_histogram(probs)
plt.title("Distribution théorique d'état de Bell")
plt.savefig("histogramme_théorique.png")

__save_amplitudes(qc)

qc.measure_all()

# Simulateur local Aer
simulator = AerSimulator()

# Transpilation pour le simulateur
compiled_circuit = transpile(qc, simulator)

nbr_shots = 1024

# Exécution du circuit
result = simulator.run(compiled_circuit, shots=nbr_shots).result()

# Récupération des résultats
counts = result.get_counts()
print(counts)
for key, value in counts.items():
    print(key, " : ", value)
    counts[key] = round((counts[key] / nbr_shots) * 100, 2)

# Affichage
print("Résultats de mesure :", counts)
plot_histogram(counts)
plt.title("Distribution des états mesurés (état de Bell)")
plt.savefig("histogramme_resultats.png")
