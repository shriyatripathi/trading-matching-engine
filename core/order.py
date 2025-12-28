"""
Order data models for the matching engine.

Based on research:
- Price-Time Priority (FIFO) algorithm (industry standard)
- Simple order types: Limit and Market
- Immutable order IDs with timestamp for ordering
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime
import uuid
from decimal import Decimal


class OrderType(Enum):
    """
    Order types supported by the matching engine.
    
    Research note: Most exchanges support additional types (Stop, Iceberg, etc.),
    but Limit and Market are fundamental and sufficient for core functionality.
    """
    LIMIT = "LIMIT"    # Order with specific price limit
    MARKET = "MARKET"  # Order executed at best available price


class OrderSide(Enum):
    """Side of the market - buying or selling."""
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(Enum):
    """
    Order lifecycle states.
    
    Research note: Real exchanges have more states (PENDING_NEW, PARTIAL_FILL, etc.),
    but these core states are sufficient for our implementation.
    """
    OPEN = "OPEN"              # Active in order book
    FILLED = "FILLED"          # Completely filled
    CANCELLED = "CANCELLED"    # Cancelled by user
    REJECTED = "REJECTED"      # Rejected by matching engine
    PARTIAL = "PARTIAL"        # Partially filled


@dataclass
class Order:
    """
    Represents a single order in the trading system.
    
    Uses PRICE-TIME PRIORITY matching (research consensus):
    - Orders sorted by price (best price first)
    - Orders at same price executed by time (FIFO)
    
    Attributes:
        order_id: Unique identifier (UUID)
        symbol: Trading pair (e.g., "BTC/USD")
        side: BUY or SELL
        order_type: LIMIT or MARKET
        quantity: Total order quantity (immutable)
        price: Limit price (None for market orders)
        timestamp: Creation time (used for time priority)
        filled_quantity: Amount filled so far (mutable)
        status: Current order status (mutable)
    """
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    price: Optional[Decimal]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Mutable state
    filled_quantity: Decimal = field(default=Decimal('0'))
    status: OrderStatus = field(default=OrderStatus.OPEN)
    
    def __post_init__(self):
        """Validate order after initialization."""
        # Ensure Decimal types for precise financial calculations
        if not isinstance(self.quantity, Decimal):
            self.quantity = Decimal(str(self.quantity))
        if self.price is not None and not isinstance(self.price, Decimal):
            self.price = Decimal(str(self.price))
        if not isinstance(self.filled_quantity, Decimal):
            self.filled_quantity = Decimal(str(self.filled_quantity))
        
        # Validation
        if self.quantity <= 0:
            raise ValueError("Order quantity must be positive")
        
        if self.order_type == OrderType.LIMIT:
            if self.price is None or self.price <= 0:
                raise ValueError("Limit orders must have a positive price")
        
        if self.order_type == OrderType.MARKET:
            if self.price is not None:
                raise ValueError("Market orders should not have a price")
    
    @property
    def remaining_quantity(self) -> Decimal:
        """Calculate unfilled quantity."""
        return self.quantity - self.filled_quantity
    
    @property
    def is_fully_filled(self) -> bool:
        """Check if order is completely filled."""
        return self.filled_quantity >= self.quantity
    
    @property
    def is_buy(self) -> bool:
        """Check if this is a buy order."""
        return self.side == OrderSide.BUY
    
    @property
    def is_sell(self) -> bool:
        """Check if this is a sell order."""
        return self.side == OrderSide.SELL
    
    def fill(self, quantity: Decimal) -> Decimal:
        """
        Fill part or all of the order.
        
        Research note: This implements partial fills which are standard
        in all modern exchanges (NASDAQ, NYSE, etc.).
        
        Args:
            quantity: Amount to fill
            
        Returns:
            Actual amount filled (may be less than requested)
        """
        if not isinstance(quantity, Decimal):
            quantity = Decimal(str(quantity))
            
        fillable = min(quantity, self.remaining_quantity)
        self.filled_quantity += fillable
        
        # Update status based on fill
        if self.is_fully_filled:
            self.status = OrderStatus.FILLED
        elif self.filled_quantity > 0:
            self.status = OrderStatus.PARTIAL
            
        return fillable
    
    def to_dict(self) -> dict:
        """Convert order to dictionary for API serialization."""
        return {
            "order_id": self.order_id,
            "symbol": self.symbol,
            "side": self.side.value,
            "order_type": self.order_type.value,
            "quantity": str(self.quantity),
            "price": str(self.price) if self.price else None,
            "timestamp": self.timestamp.isoformat(),
            "filled_quantity": str(self.filled_quantity),
            "remaining_quantity": str(self.remaining_quantity),
            "status": self.status.value
        }
    
    @staticmethod
    def create_limit_order(
        symbol: str,
        side: OrderSide,
        quantity: Decimal,
        price: Decimal,
        order_id: Optional[str] = None
    ) -> 'Order':
        """
        Factory method to create a limit order.
        
        Research note: Factory methods ensure orders are always valid
        and make testing easier.
        """
        return Order(
            order_id=order_id or str(uuid.uuid4()),
            symbol=symbol,
            side=side,
            order_type=OrderType.LIMIT,
            quantity=quantity,
            price=price
        )
    
    @staticmethod
    def create_market_order(
        symbol: str,
        side: OrderSide,
        quantity: Decimal,
        order_id: Optional[str] = None
    ) -> 'Order':
        """
        Factory method to create a market order.
        
        Research note: Market orders execute immediately at best available price.
        They should never rest in the order book.
        """
        return Order(
            order_id=order_id or str(uuid.uuid4()),
            symbol=symbol,
            side=side,
            order_type=OrderType.MARKET,
            quantity=quantity,
            price=None
        )
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (f"Order(id={self.order_id[:8]}..., {self.side.value} "
                f"{self.quantity} {self.symbol} @ {self.price or 'MARKET'})")


@dataclass
class Trade:
    """
    Represents a matched trade between two orders.
    
    Research note: Trades are the output of the matching engine.
    Both buy and sell orders are filled by this trade.
    
    Attributes:
        trade_id: Unique trade identifier
        symbol: Trading pair
        price: Execution price
        quantity: Executed quantity
        timestamp: Execution time
        buy_order_id: Aggressor buy order (or passive)
        sell_order_id: Aggressor sell order (or passive)
        buy_order_filled: Whether buy order is now fully filled
        sell_order_filled: Whether sell order is now fully filled
    """
    trade_id: str
    symbol: str
    price: Decimal
    quantity: Decimal
    timestamp: datetime
    buy_order_id: str
    sell_order_id: str
    buy_order_filled: bool = False
    sell_order_filled: bool = False
    
    def __post_init__(self):
        """Ensure Decimal types."""
        if not isinstance(self.price, Decimal):
            self.price = Decimal(str(self.price))
        if not isinstance(self.quantity, Decimal):
            self.quantity = Decimal(str(self.quantity))
    
    def to_dict(self) -> dict:
        """Convert trade to dictionary for API serialization."""
        return {
            "trade_id": self.trade_id,
            "symbol": self.symbol,
            "price": str(self.price),
            "quantity": str(self.quantity),
            "timestamp": self.timestamp.isoformat(),
            "buy_order_id": self.buy_order_id,
            "sell_order_id": self.sell_order_id,
            "buy_order_filled": self.buy_order_filled,
            "sell_order_filled": self.sell_order_filled
        }
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"Trade({self.quantity} {self.symbol} @ {self.price})"
