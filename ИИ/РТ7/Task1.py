import numpy as np

def sigmoid(x):
    # Функция активации: f(x) = 1 / (1 + e*(-x))
    return 1 / (1 + np.exp(-x))
class Neuron:
    def __init__(self, weights, bias):
        self.weights = weights
        self.bias = bias
    def feedforward(self, inputs):
        total = np.dot(self.weights, inputs) + self.bias
        return sigmoid(total)
weights = np.array([0, 1])
bias = 4
n = Neuron(weights, bias)
x = np.array([2, 3])
print(n.feedforward(x))

class OurNeuralNetwork:
    def __init__(self):
        weights = np.array([0.5, 0.5, 0.5]) # w = [1,0]
        bias = 0 # b = 1
        # Knacc Neuron u3 предыдущего раздела
        self.h1 = Neuron(weights, bias) # 1 нейрон
        self.h2 = Neuron(weights, bias) # 2 нейрон
        self.h3 = Neuron(weights, bias) # 2 нейрон
        self.o1 = Neuron(weights, bias) # 1 выход
    def feedforward(self, x):
        out_h1 = self.h1.feedforward(x)
        out_h2 = self.h2.feedforward(x)
        out_h3 = self.h2.feedforward(x)
        # Входы для o1 — это входы h1 и h2
        out_o1 = self.o1.feedforward(np.array([out_h1, out_h2, out_h3]))
        return out_o1

network = OurNeuralNetwork()
x = np.array([2, 3, 4])
print(network.feedforward(x))

class OurNeuralNetwork:
    def __init__(self):
        weights = np.array([1, 0]) # w = [1,0]
        bias = 1 # b = 1
        # Knacc Neuron u3 предыдущего раздела
        self.h1 = Neuron(weights, bias) # 1 нейрон
        self.h2 = Neuron(weights, bias) # 2 нейрон
        self.o1 = Neuron(weights, bias) # 1 выход
        self.o2 = Neuron(weights, bias) # 2 выход
    def feedforward(self, x):
        out_h1 = self.h1.feedforward(x)
        out_h2 = self.h2.feedforward(x)
        # Входы для o1 — это входы h1 и h2
        out_o1 = self.o1.feedforward(np.array([out_h1, out_h2]))
        out_o2 = self.o2.feedforward(np.array([out_h1, out_h2]))
        return out_o1, out_o2

network = OurNeuralNetwork()
x = np.array([2, 3])
print(network.feedforward(x))