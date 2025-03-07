import numpy as np


def ReLU(x):
    return np.maximum(0, x)

class Neuron3:
    def __init__(self, weights, bias):
        self.weights = weights
        self.bias = bias

    def feedforward(self, inputs):
        total = np.dot(self.weights, inputs) + self.bias
        return ReLU(total)

class OurNeuralNetwork:
    def __init__(self):
        weights = np.array([0.5, 0.5, 0.5])
        bias = 0
        self.h1 = Neuron3(weights, bias)
        self.h2 = Neuron3(weights, bias)
        self.h3 = Neuron3(weights, bias)
        self.o1 = Neuron3(weights, bias)

    def feedforward(self, x):
        out_h1 = self.h1.feedforward(x)
        out_h2 = self.h2.feedforward(x)
        out_h3 = self.h3.feedforward(x)
        out_o1 = self.o1.feedforward(np.array([out_h1, out_h2, out_h3]))
        return out_o1

network = OurNeuralNetwork()
x = np.array([2, 3, 4])
print(network.feedforward(x))

class OurNeuralNetwork:
    def __init__(self):
        weights = np.array([1, 0])
        bias = 1

        self.h1 = Neuron3(weights, bias)
        self.h2 = Neuron3(weights, bias)
        self.o1 = Neuron3(weights, bias)
        self.o2 = Neuron3(weights, bias)

    def feedforward(self, x):
        out_h1 = self.h1.feedforward(x)
        out_h2 = self.h2.feedforward(x)
        out_o1 = self.o1.feedforward(np.array([out_h1, out_h2]))
        out_o2 = self.o2.feedforward(np.array([out_h1, out_h2]))
        return out_o1, out_o2

network = OurNeuralNetwork()
x = np.array([2, 3])
print(network.feedforward(x))