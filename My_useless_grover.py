from qiskit import QuantumCircuit
from qiskit_aer.primitives import Sampler
import numpy as np

class my_grover():
    @staticmethod
    def __int_to_binList(n):
        bits = bin(n)[2:]
        return [int(bit) for bit in reversed(bits)]

    def __int_to_tildBinList(self, code_secret, num_qubits):
        return self.__int_to_binList( (~code_secret) & ((1 << num_qubits) - 1) )
    
    def my_oracle(self, qc, not_bin, num_qubits):
        for i, bin in (enumerate(not_bin)):
            if bin:
                qc.x([i])

        qc.mcx(list( range(num_qubits) ), num_qubits)
        qc.cz(0, num_qubits)
        qc.mcx(list( range(num_qubits) ), num_qubits)
        
        for i, bin in (enumerate(not_bin)):
            if bin:
                qc.x(i)

    def my_diffuser(self, qc, num_qubits):
        qc.h(range(num_qubits))
        qc.x(range(num_qubits))

        qc.h(num_qubits - 1)
        qc.mcx(list(range(num_qubits - 1)), num_qubits - 1)
        qc.h(num_qubits - 1)

        qc.x(range(num_qubits))
        qc.h(range(num_qubits))

    def search_code(self, code_secret):
        num_qubits = code_secret.bit_length()
        if num_qubits < 2:
            num_qubits = 2

        qc = QuantumCircuit(num_qubits + 1)
        qc.h(range(num_qubits))

        not_bin = self.__int_to_tildBinList(code_secret, num_qubits)
        iterations = int(np.floor(np.pi / 4 * np.sqrt(2**num_qubits)))
        for _ in range(iterations):
            self.my_oracle(qc, not_bin, num_qubits)
            self.my_diffuser(qc, num_qubits)

        qc.measure_all()

        sampler = Sampler()
        result = sampler.run(qc).result()
        counts = result.quasi_dists[0]

        # Récupère la valeur binaire la plus probable
        max_result_bin = max(counts, key=counts.get)
        max_result_int = max_result_bin

        return max_result_int


if __name__ == "__main__":
    code = 3805
    quatum = my_grover()
    result = quatum.search_code(code)

    print()
    if result == code:
        print("bienvenu à GATACA !")
    else:
        print("entrée refusée.")
    print(result)
