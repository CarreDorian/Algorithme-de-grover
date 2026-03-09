from qiskit_aer import AerSimulator
from qiskit import QuantumCircuit, transpile
from qiskit_aer.primitives import Sampler, SamplerV2
from qiskit.quantum_info import Statevector
from qiskit.visualization import plot_histogram
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.pyplot as plt
from math import trunc
import pandas as pd
import numpy as np

class my_grover():
    @staticmethod
    def __int_to_binList(n):
        bits = bin(n)[2:]                            # retire le préfixe '0b' et place le plus petit a gauche
        return [int(bit) for bit in bits]

    @staticmethod
    def __binList_to_int(lst):
        return int(''.join(str(b) for b in lst), 2)

    def __int_to_tildBinList(self, code_secret, num_qubits):
        return self.__int_to_binList( (~code_secret) & ((1 << num_qubits) - 1) )
    

    # c'est la seule fonction que je n'ai pas faite moi-même
    def __save_amplitudes(self, qc, name_file="histogramme_amplitudes.png", title="Distribution des amplitudes (partie réelle, couleur selon imaginaire)"):
        state = Statevector.from_instruction(qc)
        amplitudes = state.data

        num_qubits = qc.num_qubits
        states = np.array([format(i, '0' + str(num_qubits) + 'b') for i in range(len(amplitudes))])

        mask = np.abs(amplitudes.real) > 0.01

        amplitudes_reelles = amplitudes.real[mask]
        amplitudes_imag = amplitudes.imag[mask]
        states = states[mask]

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

    def __save_proba(self, qc, name_file = "histogramme_théorique.png", title = "Distribution théorique d'état de Bell"):
        state = Statevector.from_instruction(qc)
        probs = state.probabilities_dict()
        plot_histogram(probs)
        plt.title(title)
        plt.savefig(name_file)

    def __save_mesure(self, qc, name_file = "histogramme_mesure.png", title = "Distribution des mesures en %"):
        qc.measure_all()
        nbr_shots = 50
        simulator = AerSimulator()
        compiled_circuit = transpile(qc, simulator)
        result = simulator.run(compiled_circuit, shots=nbr_shots).result().get_counts()

        plot_histogram(result)
        plt.title(title)
        plt.savefig(name_file)

        return ( max(result.items(), key=lambda x: x[1])[0] )[1:]  # récupère le résultat le plus probable et retire le bit de contrôle

    
    def my_oracle(self, qc, motif, num_qubits):
        for i, bin in enumerate(motif):
            if bin:
                qc.x([i])

        qc.mcx(list( range(num_qubits) ), num_qubits)
        qc.cz(num_qubits, 0)
        qc.mcx(list( range(num_qubits) ), num_qubits)
        
        for i, bin in enumerate(motif):
            if bin:
                qc.x([i])

    def my_diffuser(self, qc, num_qubits):
        qc.h(range(num_qubits))
        qc.x(range(num_qubits))

        qc.h(num_qubits - 1)
        qc.mcx(list(range(num_qubits - 1)), num_qubits - 1)
        qc.h(num_qubits - 1)

        qc.x(range(num_qubits))
        qc.h(range(num_qubits))
