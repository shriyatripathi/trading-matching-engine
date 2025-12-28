"""
Matching Engine - Core matching logic implementing Price-Time Priority algorithm.

Based on research papers:
- Price-Time Priority and Pro-Rata Matching (2010)
- NEMO Continuous Trading Spec (2022)
- CoinTossX implementation (2022)
- Limit Order Books Survey (2013)

Algorithm:
1. Incoming order checked against opposite side
2. If match possible: execute trades (walk the book)
3. Remaining quantity added to book (for limit orders)
4. Generate trade events for WebSocket broadcast
"""
from typing import List, Tuple, Optional
from datetime import datetime
from decimal import Decimal
import uuid

from .order import Order, OrderSide, OrderType, OrderStatus, Trade
from .orderbook import OrderBook


class MatchResult:
    """
    Result of a match operation.
    
    Contains all trades executed and the updated order status.
    Used for event publishing and API responses.
    """
    
    def __init__(self, order: Order):
        self.order = order
        self.trades: List[Trade] = []
        self.fully_filled = False
        self.rejected = False
        self.rejection_reason: str = ""
    
    def add_trade(self, trade: Trade):
        """Add a trade to this match result."""
        self.trades.append(trade)
    
    def to_dict(self) -> dict:
        """Serialize for API/events."""
        return {
            "order": self.order.to_dict(),
            "trades": [t.to_dict() for t in self.trades],
            "fully_filled": self.fully_filled,
            "rejected": self.rejected,
            "rejection_reason": self.rejection_reason
        }


class MatchingEngine:
    """
    Core matching engine implementing Price-Time Priority (FIFO) algorithm.
    
    Research-backed design:
    - Maintains one OrderBook per symbol
    - Synchronous matching (deterministic, no race conditions)
    - Emits events for real-time market data
    - Supports limit and market orders, cancellations
    
    Matching algorithm (standard across all exchanges):
    1. Incoming aggressive order crosses the spread
    2. Match against opposite side, best price first
    3. At each price level, match in time order (FIFO)
    4. Continue until order filled or no more matches
    5. Remainder goes into book (limit orders only)
    
    Performance characteristics:
    - O(log n) to add order to book
    - O(1) to access best bid/ask
    - O(k) to match, where k = number of price levels crossed
    - O(log n) to cancel order
    """
    
    def __init__(self):
        """Initialize matching engine with empty order books."""
        self.order_books: dict[str, OrderBook] = {}
        self.trade_history: List[Trade] = []  # Recent trades (for UI)
        self.max_trade_history = 1000  # Limit memory usage
    
    def get_or_create_book(self, symbol: str) -> OrderBook:
        """
        Get order book for symbol, creating if it doesn't exist.
        
        Research note: Real exchanges pre-create books for listed symbols.
        We create on-demand for simplicity.
        """
        if symbol not in self.order_books:
            self.order_books[symbol] = OrderBook(symbol)
        return self.order_books[symbol]
    
    def submit_order(self, order: Order) -> MatchResult:
        """
        Submit an order to the matching engine.
        
        This is the main entry point for all orders.
        Implements the complete matching algorithm.
        
        Research note: This method should be called synchronously
        (single-threaded) to maintain determinism. For multi-threaded
        systems, use per-symbol locking or lock-free structures
        (Concurrent Order Book paper, 2016).
        
        Args:
            order: The order to match and/or add to book
            
        Returns:
            MatchResult containing trades and order status
        """
        result = MatchResult(order)
        book = self.get_or_create_book(order.symbol)
        
        # Step 1: Validate order
        if not self._validate_order(order, book, result):
            return result
        
        # Step 2: Try to match against opposite side
        if order.order_type == OrderType.MARKET:
            self._match_market_order(order, book, result)
        else:
            self._match_limit_order(order, book, result)
        
        # Step 3: If limit order with remaining quantity, add to book
        if (order.order_type == OrderType.LIMIT and 
            not order.is_fully_filled and 
            order.status != OrderStatus.REJECTED):
            book.add_order(order)
        
        # Step 4: Update result status
        result.fully_filled = order.is_fully_filled
        
        # Step 5: Store trades in history (for UI trade tape)
        for trade in result.trades:
            self._add_to_trade_history(trade)
            book.last_trade_price = trade.price
            book.total_volume_traded += trade.quantity
        
        return result
    
    def cancel_order(self, order_id: str, symbol: str) -> Optional[Order]:
        """
        Cancel an order.
        
        Research note: Cancellations are the most common message type
        in many exchanges (HFT firms cancel/replace constantly).
        
        Args:
            order_id: ID of order to cancel
            symbol: Symbol of the order
            
        Returns:
            Cancelled order, or None if not found
        """
        if symbol not in self.order_books:
            return None
        
        book = self.order_books[symbol]
        return book.cancel_order(order_id)
    
    def get_order_book(self, symbol: str) -> Optional[OrderBook]:
        """Get order book for a symbol."""
        return self.order_books.get(symbol)
    
    def get_order(self, order_id: str, symbol: str) -> Optional[Order]:
        """Look up an order by ID and symbol."""
        if symbol not in self.order_books:
            return None
        return self.order_books[symbol].get_order(order_id)
    
    def get_recent_trades(self, symbol: str, limit: int = 50) -> List[Trade]:
        """
        Get recent trades for a symbol.
        
        Research note: This is for the "trade tape" in market data feeds.
        Real exchanges publish all trades immediately via multicast.
        """
        trades = [t for t in self.trade_history if t.symbol == symbol]
        return trades[-limit:]  # Most recent
    
    # Private helper methods
    
    def _validate_order(self, order: Order, book: OrderBook, result: MatchResult) -> bool:
        """Validate order before matching."""
        # Check for self-trade (same order ID already exists)
        if book.get_order(order.order_id):
            result.rejected = True
            result.rejection_reason = "Duplicate order ID"
            order.status = OrderStatus.REJECTED
            return False
        
        # Market orders must have liquidity on opposite side
        if order.order_type == OrderType.MARKET:
            opposite_best = (book.get_best_ask() if order.is_buy 
                           else book.get_best_bid())
            if opposite_best is None:
                result.rejected = True
                result.rejection_reason = "No liquidity for market order"
                order.status = OrderStatus.REJECTED
                return False
        
        return True
    
    def _match_market_order(self, order: Order, book: OrderBook, result: MatchResult):
        """
        Match a market order.
        
        Research note: Market orders walk the book until fully filled
        or no more liquidity. They execute at progressively worse prices.
        """
        # Get opposite side of book
        opposite_side = book.asks if order.is_buy else book.bids
        
        # Walk the book (match at each price level)
        while not order.is_fully_filled and len(opposite_side) > 0:
            best_price = list(opposite_side.keys())[0]
            price_level = opposite_side[best_price]
            
            # Match against orders at this price level (FIFO)
            while not order.is_fully_filled and not price_level.is_empty():
                passive_order = price_level.peek_front()
                if passive_order is None:
                    break
                
                # Execute trade
                trade = self._execute_trade(order, passive_order, best_price)
                result.add_trade(trade)
                
                # Remove fully filled passive order
                if passive_order.is_fully_filled:
                    price_level.remove_order(passive_order)
                    del book.orders[passive_order.order_id]
            
            # Remove empty price level
            if price_level.is_empty():
                del opposite_side[best_price]
        
        # If still not filled, reject remainder (no liquidity)
        if not order.is_fully_filled:
            order.status = OrderStatus.PARTIAL
    
    def _match_limit_order(self, order: Order, book: OrderBook, result: MatchResult):
        """
        Match a limit order.
        
        Research note: Limit orders only match at their price or better.
        This implements "price priority" - better prices match first.
        """
        # Get opposite side of book
        opposite_side = book.asks if order.is_buy else book.bids
        
        # Match while price condition satisfied
        while not order.is_fully_filled and len(opposite_side) > 0:
            best_price = list(opposite_side.keys())[0]
            
            # Check if we can match at this price
            # Buy order: can match if best ask <= limit price
            # Sell order: can match if best bid >= limit price
            can_match = (
                (order.is_buy and best_price <= order.price) or
                (order.is_sell and best_price >= order.price)
            )
            
            if not can_match:
                break  # No more matches possible
            
            price_level = opposite_side[best_price]
            
            # Match against orders at this price level (FIFO - time priority)
            while not order.is_fully_filled and not price_level.is_empty():
                passive_order = price_level.peek_front()
                if passive_order is None:
                    break
                
                # Execute trade at passive order's price (price improvement for aggressor)
                trade = self._execute_trade(order, passive_order, best_price)
                result.add_trade(trade)
                
                # Remove fully filled passive order
                if passive_order.is_fully_filled:
                    price_level.remove_order(passive_order)
                    del book.orders[passive_order.order_id]
            
            # Remove empty price level
            if price_level.is_empty():
                del opposite_side[best_price]
    
    def _execute_trade(
        self, 
        aggressive_order: Order, 
        passive_order: Order, 
        price: Decimal
    ) -> Trade:
        """
        Execute a trade between two orders.
        
        Research note: Trade price is always the passive order's price
        (the order that was resting in the book). This is standard in
        all price-time priority systems.
        
        Args:
            aggressive_order: Incoming order (market or crossing limit)
            passive_order: Resting order in book
            price: Execution price (passive order's price)
            
        Returns:
            Trade object representing the match
        """
        # Determine trade quantity (limited by both orders)
        trade_qty = min(
            aggressive_order.remaining_quantity,
            passive_order.remaining_quantity
        )
        
        # Fill both orders
        aggressive_order.fill(trade_qty)
        passive_order.fill(trade_qty)
        
        # Determine which order is buy/sell
        if aggressive_order.is_buy:
            buy_order_id = aggressive_order.order_id
            sell_order_id = passive_order.order_id
            buy_filled = aggressive_order.is_fully_filled
            sell_filled = passive_order.is_fully_filled
        else:
            buy_order_id = passive_order.order_id
            sell_order_id = aggressive_order.order_id
            buy_filled = passive_order.is_fully_filled
            sell_filled = aggressive_order.is_fully_filled
        
        # Create trade record
        trade = Trade(
            trade_id=str(uuid.uuid4()),
            symbol=aggressive_order.symbol,
            price=price,
            quantity=trade_qty,
            timestamp=datetime.utcnow(),
            buy_order_id=buy_order_id,
            sell_order_id=sell_order_id,
            buy_order_filled=buy_filled,
            sell_order_filled=sell_filled
        )
        
        return trade
    
    def _add_to_trade_history(self, trade: Trade):
        """Add trade to history, maintaining size limit."""
        self.trade_history.append(trade)
        
        # Trim history if too large (prevent memory growth)
        if len(self.trade_history) > self.max_trade_history:
            self.trade_history = self.trade_history[-self.max_trade_history:]
