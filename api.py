"""
FastAPI backend server with REST API and WebSocket support.

Based on research:
- Event-driven architecture (Disruptor pattern influence)
- WebSocket for real-time market data (standard in all exchanges)
- Async I/O with uvloop for performance
- Separate event queue to decouple matching from broadcasting

API Endpoints:
- POST /orders: Submit new order
- DELETE /orders/{order_id}: Cancel order
- GET /orders/{order_id}: Query order status
- GET /orderbook/{symbol}: Get current order book
- GET /trades/{symbol}: Get recent trades
- WebSocket /ws: Real-time market data stream
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
import asyncio
import json
import logging

from core import (
    MatchingEngine,
    Order,
    OrderType,
    OrderSide,
    OrderStatus
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Trading Matching Engine API",
    description="Research-based matching engine with Price-Time Priority (FIFO) algorithm",
    version="1.0.0"
)

# CORS middleware (allow frontend to connect)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global matching engine instance
# Research note: Single-threaded for determinism (CloudEx paper discusses sharding for scale)
matching_engine = MatchingEngine()

# WebSocket connection manager
class ConnectionManager:
    """
    Manages WebSocket connections for real-time market data.
    
    Research note: This implements a simple pub/sub pattern.
    Real exchanges use UDP multicast (lower latency), but WebSocket
    is more practical for web clients.
    """
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept and register new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove disconnected client."""
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """
        Broadcast message to all connected clients.
        
        Research note: Batching broadcasts (every 10-50ms) can improve
        throughput in high-frequency scenarios (Disruptor pattern).
        We broadcast immediately for simplicity.
        """
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.append(connection)
        
        # Clean up failed connections
        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)

manager = ConnectionManager()

# Pydantic models for API requests/responses

class OrderRequest(BaseModel):
    """Request to submit a new order."""
    symbol: str = Field(..., json_schema_extra={"example": "BTC/USD"}, description="Trading pair")
    side: str = Field(..., json_schema_extra={"example": "BUY"}, description="BUY or SELL")
    order_type: str = Field(..., json_schema_extra={"example": "LIMIT"}, description="LIMIT or MARKET")
    quantity: str = Field(..., json_schema_extra={"example": "1.5"}, description="Order quantity (as string for precision)")
    price: Optional[str] = Field(None, json_schema_extra={"example": "50000.00"}, description="Limit price (required for LIMIT orders)")
    
    @field_validator('side')
    @classmethod
    def validate_side(cls, v: str) -> str:
        if v.upper() not in ['BUY', 'SELL']:
            raise ValueError('side must be BUY or SELL')
        return v.upper()
    
    @field_validator('order_type')
    @classmethod
    def validate_order_type(cls, v: str) -> str:
        if v.upper() not in ['LIMIT', 'MARKET']:
            raise ValueError('order_type must be LIMIT or MARKET')
        return v.upper()
    
    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v: str) -> str:
        try:
            qty = Decimal(v)
            if qty <= 0:
                raise ValueError('quantity must be positive')
            return v
        except:
            raise ValueError('quantity must be a valid number')
    
    @field_validator('price')
    @classmethod
    def validate_price(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            try:
                price = Decimal(v)
                if price <= 0:
                    raise ValueError('price must be positive')
            except:
                raise ValueError('price must be a valid number')
        return v

class OrderResponse(BaseModel):
    """Response after order submission."""
    order_id: str
    status: str
    message: str
    trades: List[dict] = []
    order: dict

class CancelResponse(BaseModel):
    """Response after order cancellation."""
    order_id: str
    status: str
    message: str

# REST API Endpoints

@app.get("/")
async def root():
    """API information."""
    return {
        "name": "Trading Matching Engine",
        "version": "1.0.0",
        "algorithm": "Price-Time Priority (FIFO)",
        "based_on_research": [
            "Price-Time Priority and Pro-Rata Matching (2010)",
            "CoinTossX (2022)",
            "Limit Order Books Survey (2013)",
            "NEMO Continuous Trading Spec (2022)",
            "CloudEx (2021)",
            "Concurrent Order Book (2016)"
        ]
    }

@app.post("/orders", response_model=OrderResponse)
async def submit_order(order_req: OrderRequest):
    """
    Submit a new order to the matching engine.
    
    Research note: This is a synchronous operation (waits for matching to complete).
    Real exchanges use async messaging, but synchronous is simpler and sufficient
    for our throughput targets (50K orders/sec).
    """
    try:
        # Create order object
        side = OrderSide.BUY if order_req.side == "BUY" else OrderSide.SELL
        order_type = OrderType.LIMIT if order_req.order_type == "LIMIT" else OrderType.MARKET
        quantity = Decimal(order_req.quantity)
        price = Decimal(order_req.price) if order_req.price else None
        
        if order_type == OrderType.LIMIT:
            order = Order.create_limit_order(
                symbol=order_req.symbol,
                side=side,
                quantity=quantity,
                price=price
            )
        else:
            order = Order.create_market_order(
                symbol=order_req.symbol,
                side=side,
                quantity=quantity
            )
        
        # Submit to matching engine
        result = matching_engine.submit_order(order)
        
        # Broadcast updates to WebSocket clients
        await _broadcast_order_update(result)
        
        # Return response
        if result.rejected:
            return OrderResponse(
                order_id=order.order_id,
                status="REJECTED",
                message=result.rejection_reason,
                trades=[],
                order=order.to_dict()
            )
        else:
            return OrderResponse(
                order_id=order.order_id,
                status=order.status.value,
                message=f"Order submitted successfully. {len(result.trades)} trade(s) executed.",
                trades=[t.to_dict() for t in result.trades],
                order=order.to_dict()
            )
    
    except Exception as e:
        logger.error(f"Error submitting order: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/orders/{symbol}/{order_id}", response_model=CancelResponse)
async def cancel_order(symbol: str, order_id: str):
    """
    Cancel an existing order.
    
    Research note: Order cancellations are the most common message type
    in many exchanges (70%+ of messages per HFT research).
    """
    try:
        cancelled_order = matching_engine.cancel_order(order_id, symbol)
        
        if cancelled_order is None:
            raise HTTPException(status_code=404, detail="Order not found or already filled/cancelled")
        
        # Broadcast cancellation
        await manager.broadcast({
            "type": "order_cancelled",
            "order_id": order_id,
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Broadcast updated order book
        await _broadcast_orderbook(symbol)
        
        return CancelResponse(
            order_id=order_id,
            status="CANCELLED",
            message="Order cancelled successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling order: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/orders/{symbol}/{order_id}")
async def get_order(symbol: str, order_id: str):
    """Query order status by ID."""
    order = matching_engine.get_order(order_id, symbol)
    
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return order.to_dict()

@app.get("/orderbook")
async def get_orderbook(symbol: str, depth: int = 10):
    """
    Get current order book for a symbol.
    
    Research note: This returns "Level 2" market data (price levels with quantities).
    Level 1 = best bid/ask only, Level 3 = all individual orders.
    """
    book = matching_engine.get_order_book(symbol)
    
    if book is None:
        return {
            "symbol": symbol,
            "bids": [],
            "asks": [],
            "best_bid": None,
            "best_ask": None,
            "spread": None,
            "mid_price": None,
            "last_trade_price": None
        }
    
    return book.to_dict(depth=depth)

@app.get("/trades")
async def get_trades(symbol: str, limit: int = 50):
    """
    Get recent trades for a symbol.
    
    Research note: This is the "trade tape" shown in most trading UIs.
    Real exchanges publish every trade immediately via market data feeds.
    """
    trades = matching_engine.get_recent_trades(symbol, limit=limit)
    return [t.to_dict() for t in trades]

@app.get("/symbols")
async def get_symbols():
    """Get list of all active symbols (with order books)."""
    return {
        "symbols": list(matching_engine.order_books.keys()),
        "count": len(matching_engine.order_books)
    }

# WebSocket endpoint for real-time market data

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time market data.
    
    Research note: WebSocket is standard for real-time financial data
    in web applications. Real exchanges use UDP multicast for lowest latency.
    
    Message types sent:
    - order_book_update: Order book changed
    - trade: New trade executed
    - order_update: Order status changed
    """
    await manager.connect(websocket)
    
    try:
        # Send initial order books for all symbols
        for symbol, book in matching_engine.order_books.items():
            await websocket.send_json({
                "type": "order_book_snapshot",
                "data": book.to_dict(),
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Keep connection alive and handle client messages
        while True:
            # Receive messages from client (e.g., subscriptions)
            data = await websocket.receive_text()
            # For now, just acknowledge
            await websocket.send_json({
                "type": "ack",
                "message": "Message received",
                "timestamp": datetime.utcnow().isoformat()
            })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# Helper functions for broadcasting

async def _broadcast_order_update(match_result):
    """Broadcast order and trade updates to WebSocket clients."""
    # Broadcast trades
    for trade in match_result.trades:
        await manager.broadcast({
            "type": "trade",
            "data": trade.to_dict(),
            "timestamp": datetime.utcnow().isoformat()
        })
    
    # Broadcast order status
    await manager.broadcast({
        "type": "order_update",
        "data": match_result.order.to_dict(),
        "timestamp": datetime.utcnow().isoformat()
    })
    
    # Broadcast updated order book
    await _broadcast_orderbook(match_result.order.symbol)

async def _broadcast_orderbook(symbol: str):
    """Broadcast order book update for a symbol."""
    book = matching_engine.get_order_book(symbol)
    if book:
        await manager.broadcast({
            "type": "order_book_update",
            "data": book.to_dict(),
            "timestamp": datetime.utcnow().isoformat()
        })

# Health check endpoint

@app.get("/health")
async def health_check():
    """Health check for monitoring."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "active_symbols": len(matching_engine.order_books),
        "websocket_connections": len(manager.active_connections)
    }

if __name__ == "__main__":
    import uvicorn
    
    # Run with uvloop for better performance (research: near-native async I/O)
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes (development only)
        log_level="info"
    )
