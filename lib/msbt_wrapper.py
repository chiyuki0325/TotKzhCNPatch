from lib.msbt import msbt as _MSBT

__all__ = ['MSBT']

class MSBT:
    def __init__(self, path):
        self.msbt = _MSBT(path)
        self.labels = self.msbt.lbl1.Labels
        self.texts = self.msbt.txt2.Strings

    def save(self, path):
        self.msbt.save(path)