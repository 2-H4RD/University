import numpy as np
class trigonom:
    def sin(self, x):
        return np.sin(x)
    def cos(self, x):
        return np.cos(x)
    def tg(self, x):
        return np.tan(x)
    def arcsin(self, x):
        if -1 <= x <= 1:
            return np.arcsin(x)
        else:
            return "Ошибка"
    def arccos(self, x):
        if -1 <= x <= 1:
            return np.arccos(x)
        else:
            return "Ошибка"
    def arctg(self, x):
        return np.arctan(x)
    def deg_to_rad(self, x):
        return x * np.pi / 180

