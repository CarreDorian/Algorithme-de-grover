from qiskit_aer import AerSimulator
from qiskit import QuantumCircuit, transpile
from matplotlib.colors import LinearSegmentedColormap
from qiskit.visualization import plot_histogram
from qiskit.circuit.library import UnitaryGate
from qiskit.quantum_info import Statevector
import matplotlib.pyplot as plt
from math import trunc
import pandas as pd
import numpy as np

class my_grover():
    @staticmethod
    def __int_to_binList(n):
        bits = bin(n)[2:]
        return [int(bit) for bit in bits]

    @staticmethod
    def __binList_to_int(lst):
        return int(''.join(str(b) for b in lst), 2)

    def __int_to_tildBinList(self, code_secret, num_qubits):
        return self.__int_to_binList( (~code_secret) & ((1 << num_qubits) - 1) )
    
    def __binList_to_tildBinList(self, code_secret):
        lst = [0 if i else 1 for i in code_secret]
        return lst

    @staticmethod
    def __get_amplitudes(qc):
        amplitude = None
        for instr in qc.data:
            if instr.operation.name == 'initialize':
                amplitude = instr.operation.params
                return np.array(amplitude)
        
        return np.array(amplitude)



    # C'est la seule fonction que j'ai générée
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
        probs = {k: v for k, v in probs.items() if v > 0.001}

        plot_histogram(probs)
        plt.title(title)
        plt.savefig(name_file)

    def __save_mesure(self, qc, name_file = "histogramme_mesure.png", title = "Distribution des mesures en %"):
        qc.measure_all()
        nbr_shots = 50
        simulator = AerSimulator()
        compiled_circuit = transpile(qc, simulator)
        result = simulator.run(compiled_circuit, shots=nbr_shots).result().get_counts()
        result = {k: v for k, v in result.items() if v > 0.001}

        plot_histogram(result)
        plt.title(title)
        plt.savefig(name_file)

        result_lst = max(result.items(), key=lambda x: x[1])[0]

        return result_lst[-2::-1]

    
    def my_oracle(self, qc, motif, num_bits_test, num_qubits):
        # not_bin = []
        for i, bin in enumerate(motif):
            if not bin:
                qc.x([i])

        qc.mcx(list( range(num_bits_test) ), num_qubits)
        qc.cz(num_qubits, 0)
        qc.mcx(list( range(num_bits_test) ), num_qubits)
        
        for i, bin in enumerate(motif):
            if not bin:
                qc.x([i])

    def my_diffuser(self, qc, num_qubits):
        qc.h(range(num_qubits))
        qc.x(range(num_qubits))

        qc.h(num_qubits - 1)
        qc.mcx(list(range(num_qubits - 1)), num_qubits - 1)
        qc.h(num_qubits - 1)

        qc.x(range(num_qubits))
        qc.h(range(num_qubits))

    def houseHolder_diffuser(self, qc, reflection_inverse, reflection, num_qubits):
        qc.append(reflection_inverse, list(range(num_qubits)))
        qc.h( list(range(num_qubits)) )
        qc.x( list(range(num_qubits)) )
        qc.h(num_qubits-1)

        qc.mcx(list(range(num_qubits-1)), num_qubits)
        qc.cx(num_qubits, num_qubits-1)
        qc.mcx(list(range(num_qubits-1)), num_qubits)
        
        qc.h(num_qubits-1)
        qc.x( list(range(num_qubits)) )
        qc.h( list(range(num_qubits)) )
        qc.append(reflection, list(range(num_qubits)))




    def search_elem_in_vector(self, df, motif):
        len_motif = len(motif)
        nbr_qbits = len(df[0])
        nbr_possibility = len(df)
        dim = 2**nbr_qbits

        
        nbr_iteration = int(np.floor( (np.pi / 4) * (np.sqrt(dim / nbr_possibility)) )) # 4/π x sqrt(N/M), avec N le nombre de possibilités total, et M le nombre de solutions a trouver
        mirror = np.zeros(dim, dtype=complex)
        dim *= 2 # + bit de contrôle
        default_amplitude = 1 / np.sqrt(nbr_possibility)
        start_state = np.zeros(dim, dtype=complex)
        for i in df:
            int_i = self.__binList_to_int(i)
            mirror[int_i] = complex(default_amplitude)
            i.append(0)  # bit de contrôle
            start_state[int_i] = complex(default_amplitude)
        
        qc = QuantumCircuit(nbr_qbits + 1)
        qc.initialize(start_state, qc.qubits)
        I = np.eye(len(mirror))
        mirror = I - 2 * np.outer(mirror, mirror.conj())
        reflection = UnitaryGate(mirror, label="U")
        reflection_inverse = UnitaryGate(mirror.conj().T, label="U")

        for _ in range(nbr_iteration):
            self.my_oracle(qc, motif, len_motif, nbr_qbits)
            self.houseHolder_diffuser(qc, reflection_inverse, reflection, nbr_qbits)

        result = self.__save_mesure(qc)

        print("__________________\n")
        print(result)
        
        return result[len(motif):]
    
    def search_code(self, code_secret):
        num_qubits = code_secret.bit_length()
        if num_qubits < 2:
            num_qubits = 2

        qc = QuantumCircuit(num_qubits + 1)
        qc.h(range(num_qubits))
        motif = self.__int_to_binList(code_secret)

        iterations = int(np.floor(np.pi / 4 * np.sqrt(2**num_qubits)))
        for _ in range(iterations):
            self.my_oracle(qc, motif, num_qubits, num_qubits)
            self.my_diffuser(qc, num_qubits)

        self.__save_amplitudes(qc)
        self.__save_proba(qc)
        result = self.__save_mesure(qc)

        return int(result, 2)




def int_to_binList(n, num):
    bits = bin(n)[2:]
    lst = [int(bit) for bit in bits]
    while len(lst) < num:
        lst.insert(0, 0)
    return lst

if __name__ == "__main__":
    num_bits = 3

    lst = []
    for i in range(2**num_bits): # ceci est une liste a titre d'exemple 
        if i%2:
            lst.append(int_to_binList(i, num_bits))

    lst_bis = []
    num_index = (len(lst) - 1).bit_length()
    for i in range(len(lst)):
        lst_bis.append(lst[i] + int_to_binList(i, num_index))

    for i in range(len(lst_bis)):
        print(lst_bis[i])


    grover = my_grover()
    to_find = [0, 1, 1]
    result = grover.search_elem_in_vector(lst_bis, to_find)

    print('result :', result)



# if __name__ == "__main__":
#     try:
#         code = int(sys.argv[1])
#         quatum = my_grover()
#         result = quatum.search_code(code)

#         print()
#         if result == code:
#             print("bienvenu à GATACA !")
#         else:
#             print("entrée refusée.")
#         print(result)
#     except:
#         print("entry error")






















    # def search_elem(self, bow_df, joke, vectorizer):
    #     return 1
    #     bow_df['nb_mots'] = (bow_df >= 1).sum(axis=1)

    #     joke_vector = vectorizer.transform([joke]).toarray()[0]
    #     joke_series = pd.Series(joke_vector, index=vectorizer.get_feature_names_out())
    #     words = joke_series[joke_series >= 1].index.tolist()
    #     print("______________________\n")


    #     sort_df = bow_df.sort_values('nb_mots')
    #     lst_elems = self.df_find_by_legth(words, sort_df, (joke_vector >= 1).sum())
    #     print(lst_elems[0])
    #     print(len(lst_elems))
    #     num_qubits = len(lst_elems[-1])

    #     if len(lst_elems[-1]) != len(lst_elems[0]):
    #         print("WARNING : Potential error, differents length of bit string detected !!!")

    #     dim = 2 ** num_qubits
    #     statevector = np.zeros(dim, dtype=complex)
    #     amplitude = 1 / np.sqrt(len(lst_elems))

    #     for idx in lst_elems:
    #         statevector[idx] = amplitude
    #     statevector /= np.linalg.norm(statevector)
    #     statevector = np.kron(statevector, [0, 1])

    #     qc = QuantumCircuit(num_qubits + 1)
    #     qc.initialize(statevector, qc.qubits)

    #     iteration = int( np.floor(np.pi / 4 * np.sqrt(2**num_qubits / len(lst_elems))) )
    #     num_bits = len(words)

    #     for _ in range(iteration):
    #         self.my_oracle(qc, [], num_bits, num_qubits)
    #         self.my_diffuser(qc, num_bits)

    #     qc.measure_all()

    #     sampler = SamplerV2()
    #     result = sampler.run(qc).result()
    #     counts = result.values[0]

    #     result_int = max(counts, key=counts.get)
    #     result_bin = [int(b) for b in format(result_int, f'0{num_qubits}b')[::-1]]
    #     print(result_bin)
    #     print("returning : ", list(reversed(result_bin[num_bits:])))

    #     return self.__binList_to_int( list(reversed(result_bin[num_bits:])) )
