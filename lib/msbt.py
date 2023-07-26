from lib.pymsb.pymsb import msbt_from_buffer as _msbt_from_buffer
from lib.pymsb.pymsb.msbt import LMSDocument
from lib.pymsb.pymsb.adapter import LMSAdapter


class TotKLMSAdapter(LMSAdapter):
    def __init__(self):
        super().__init__()
        self._is_big_endian_: bool = False


def msbt_from_buffer(buffer: bytes) -> LMSDocument:
    return _msbt_from_buffer(TotKLMSAdapter, buffer)
