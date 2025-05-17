from abc import ABC, abstractmethod
from decimal import Decimal

class ExchangeAdapter(ABC):
    @abstractmethod
    def fetch_price(self, pair: str) -> Decimal:
        pass

    @abstractmethod
    def calculate_quantity(self, pair: str, price: Decimal, side: str) -> Decimal:
        pass
