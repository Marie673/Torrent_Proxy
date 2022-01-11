class KId:
    def __init__(self, id: list):
        self._values = []
        self.value = self._values
        if id is None or len(id) != 20:
            # 例外処理
            pass
        self._values = id  # ??
        self.length = len(self._values)

    def xor(self, b, output=None):
        if output is None:
            output = zeroClear()
        for i in range(len(b._values)):
            output._values[i] = self._values[i] ^ b

        pass
