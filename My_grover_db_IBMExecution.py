from os import getenv
from dotenv import load_dotenv
from qiskit.quantum_info import Statevector
from qiskit.circuit.library import UnitaryGate
from qiskit.visualization import plot_histogram
from qiskit import QuantumCircuit, transpile, IBMQ
from matplotlib.colors import LinearSegmentedColormap
from sklearn.feature_extraction.text import CountVectorizer  # from pip install scikit-learn v1.7.0
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

load_dotenv('./../../.env')

IBM_TOKEN = getenv('IBM_TOKEN')
if not IBM_TOKEN:
    raise RuntimeError("IBM_TOKEN non défini.")


class my_grover():
    df = []
    df_vectorized = []
    vectorizer = []
    nbr_shots = 50
    max_parallel = 10

    def __init__(self, df, nbr_shots = 5, max_parallel = 10):
        self.df = df
        self.nbr_shots = nbr_shots
        self.max_parallel = max_parallel
        self.vectorizer = CountVectorizer(min_df=15, stop_words='english')
        self.df_vectorized = pd.DataFrame(self.vectorizer.fit_transform(df['Question']).toarray(),
                                          columns=self.vectorizer.get_feature_names_out(),
                                          index=df.index)
        
        self.df_vectorized['nb_mots'] = (self.df_vectorized >= 1).sum(axis=1)
        self.df_vectorized = self.df_vectorized.sort_values(by='nb_mots')

    @staticmethod
    def __int_to_binList(n):
        bits = bin(n)[2:]                            # retire le préfixe '0b' et place le plus petit a gauche
        return [int(bit) for bit in bits]

    @staticmethod
    def __binList_to_int(lst):
        return int(''.join(str(b) for b in lst), 2)

    @staticmethod
    def __get_amplitudes(qc):
        amplitude = None
        for instr in qc.data:
            if instr.operation.name == 'initialize':
                amplitude = instr.operation.params
                return np.array(amplitude)
        
        return np.array(amplitude)

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

        IBMQ.save_account(IBM_TOKEN, overwrite=True)
        provider = IBMQ.load_account()
        backend  = provider.get_backend("ibmq_qasm_simulator")
        qc_t = transpile(qc, backend)
        job  = backend.run(qc_t, shots=self.nbr_shots)
        result = job.result().get_counts()

        plot_histogram(result)
        plt.title(title)
        plt.savefig(name_file)

        result_lst = max(result.items(), key=lambda x: x[1])[0]

        return result_lst[-2::-1] # récupère le résultat le plus probable et retire le bit de contrôle


    def __dicotomie(self, words, nbr, down, hight, mid):
        df = self.df_vectorized # condence self.df_vectorized pour plus de clareté
        result = []
        
        if df.iloc[mid]['nb_mots'] > nbr:
            result = self.__dicotomie(words, nbr, down, mid, ((mid - down) // 2) + down)
            return result

        elif df.iloc[mid]['nb_mots'] < nbr:
            result = self.__dicotomie(words, nbr, mid, hight, ((hight - mid) // 2) + mid)
            return result

        len_result = 0
        mid_bis = mid - 1

        while df.iloc[mid_bis]['nb_mots'] == nbr:
            result.append((df.loc[mid_bis, words] >= 1).astype(int).tolist()
                           + self.__int_to_binList(mid_bis))
            mid_bis = mid_bis - 1
            len_result += 1

        while df.iloc[mid]['nb_mots'] == nbr:
            result.append((df.loc[mid, words] >= 1).astype(int).tolist()
                           + self.__int_to_binList(mid))
            mid = mid + 1
            len_result += 1

        return result

    def __find_by_dicotomie(self, words):
        size = len(self.df_vectorized)
        
        return self.__dicotomie(words, len(words), 0, size - 1, size // 2)

    
    def __my_oracle(self, qc, num_bits_test, num_qubits): # on inverse aucun bit étant donné que l'on cherche le seul qui est 111...

        qc.mcx(list( range(num_bits_test) ), num_qubits)
        qc.cz(num_qubits, 0)
        qc.mcx(list( range(num_bits_test) ), num_qubits)

    def __houseHolder_diffuser(self, qc, reflection_inverse, reflection, num_qubits):
        qc.append(reflection_inverse, list(range(num_qubits)))

        qc.h( list(range(num_qubits)) )
        qc.x( list(range(num_qubits)) )
        qc.h(num_qubits-1)
        qc.mcx(list(range(num_qubits-1)), num_qubits-1)
        qc.h(num_qubits-1)
        qc.x( list(range(num_qubits)) )
        qc.h( list(range(num_qubits)) )

        qc.append(reflection, list(range(num_qubits)))

    def __search_elem_in_df(self, df, len_motif, already_execute = False):
        nbr_qbits = len(df[0])
        nbr_possibility = len(df)
        dim = 2**nbr_qbits

        
        print(nbr_qbits + 1)
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
            self.__my_oracle(qc, len_motif, nbr_qbits)            
            self.__houseHolder_diffuser(qc, reflection_inverse, reflection, nbr_qbits)

        self.__save_amplitudes(qc)
        self.__save_proba(qc)
        result = self.__save_mesure(qc)

        if 0 in result[:len_motif]:
            already_execute = True
            if already_execute:
                print("motif unfined. Retry mabe !")
                return None
            
            print(result[:len_motif])
            self.__search_elem_in_df(df, len_motif, True)
        
        return result[len_motif:]


    def search_elem(self, joke):
        print(joke)
        joke_vector = self.vectorizer.transform([joke]).toarray()[0]
        joke_series = pd.Series(joke_vector, index=self.vectorizer.get_feature_names_out())
        words = joke_series[joke_series >= 1].index.tolist()
        possibilities = self.__find_by_dicotomie(words)

        result = self.__search_elem_in_df(possibilities, len(words))

        return self.__binList_to_int(result)
    



def int_to_binList(n, num):
    bits = bin(n)[2:]
    lst = [int(bit) for bit in bits]
    while len(lst) < num:
        lst.insert(0, 0)
    return lst

if __name__ == "__main__":
    df = pd.read_csv("./database/jokes.csv", delimiter=',', encoding='utf8')

    joke = "A couple was traveling across Europe but had to stop abruptly at Finland's borders. Why?" # Because it was the Finnish line.

    print(df.head())

    grover_db = my_grover(df)
    result = grover_db.search_elem(joke)
    print(result)
    print(df[result])

















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
