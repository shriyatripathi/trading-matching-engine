# Trading Matching Engine - Research Implementation

A production-quality matching engine implementing **Price-Time Priority (FIFO)** algorithm based on comprehensive academic research and industry best practices.

## Research Foundation

This implementation is based on analysis of 20+ research papers including:

### Core Algorithm Papers
- **Price-Time Priority and Pro-Rata Matching** (2010) - Algorithm comparison
- **NEMO Continuous Trading Spec** (2022) - Industry standard matching rules
- **Limit Order Books Survey** (2013) - Comprehensive LOB mechanics
- **LOB-Bench** (2025) - Benchmarking limit order book data

### Performance & Architecture
- **CoinTossX** (2022) - Open-source reference implementation
- **CloudEx** (2021) - Fair-access cloud exchange architecture
- **Concurrent Order Book** (2016) - Lock-free data structures
- **Design and Implementation of Scalable Financial Exchange** (2024)

### Data Structures
- **Exploiting Concurrency in Domain-Specific Data Structures** (2016)
- **The Bw-Tree** (2013) - Latch-free ordered indexes
- **Disruptor** (2011) - Event pipeline architecture

##  Algorithm: Price-Time Priority (FIFO)

**Why this algorithm?**
- Used by NYSE, NASDAQ, Coinbase, Binance
- Simple, deterministic, auditable
- Fair: first-come-first-served at each price level
- O(1) matching at best price

**How it works:**
1. Orders sorted by **price** (best price first)
2. Orders at same price matched by **time** (FIFO queue)
3. Incoming aggressive orders "walk the book"
4. Partial fills supported
5. Unmatched limit orders rest in book

### Matching Engine Invariants

These guarantees are **critical** and maintained at all times:

1. **Price-time priority is never violated** - Orders at better prices always execute first; orders at same price execute in time order (FIFO)
2. **No order trades at a worse price than its limit** - Buy orders never pay more than limit price; sell orders never receive less
3. **Total traded quantity ≤ sum of submitted quantities** - The engine never creates phantom liquidity
4. **Order book is always internally consistent after each event** - Price levels are sorted, volumes are accurate, no orphaned orders
5. **Cancelled orders never reappear** - Once cancelled, an order ID is permanently removed from the active book

These invariants ensure fairness, correctness, and auditability - essential properties validated by research (NEMO spec, Limit Order Books survey).

## Architecture

```
┌──────────────────┐
│   React UI       │  ← WebSocket ← Real-time updates
│  (Port 3000)     │  → HTTP →
└──────────────────┘
         ↓
┌──────────────────────────────┐
│     FastAPI Server           │
│      (Port 8000)             │
├──────────────────────────────┤
│  ┌────────────────────────┐  │
│  │  WebSocket Hub         │  │ Broadcasts market data
│  │  (async)               │  │
│  └────────────────────────┘  │
│  ┌────────────────────────┐  │
│  │  REST API              │  │ Submit/cancel orders
│  │  (FastAPI)             │  │
│  └────────────────────────┘  │
│  ┌────────────────────────┐  │
│  │  Matching Engine       │  │ Core logic (sync)
│  │  - OrderBook           │  │
│  │  - Price Levels        │  │
│  │  - FIFO Queues         │  │
│  └────────────────────────┘  │
└──────────────────────────────┘
```

### Data Structures 

```python
OrderBook {
    bids: SortedDict[price → PriceLevel]  # O(log n) - Red-Black tree
    asks: SortedDict[price → PriceLevel]  # O(log n) - Red-Black tree
    orders: HashMap[order_id → Order]     # O(1) lookup
}

PriceLevel {
    price: Decimal
    orders: Deque[Order]      # FIFO queue - O(1) append/pop
    total_volume: Decimal     # Cached for performance
}
```

**Complexity Analysis:**
- Add order: O(log n) where n = number of price levels
- Cancel order: O(log n) + O(m) where m = orders at price level
- Get best bid/ask: O(1)
- Match order: O(k) where k = price levels crossed

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+

### Backend Setup

```bash
cd matching_engine

# Install Python dependencies
pip install -r requirements.txt

# Run the server
python api.py
```

Server will start on `http://localhost:8000`

### Frontend Setup

```bash
cd matching_engine/frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

UI will be available at `http://localhost:3000`

### Test the System

1. Open browser to `http://localhost:3000`
2. Select a symbol (BTC/USD, ETH/USD, AAPL)
3. Submit buy/sell orders using the form
4. Watch real-time order book and trade updates

##  API Documentation

### REST Endpoints

#### Submit Order
```http
POST /orders
Content-Type: application/json

{
  "symbol": "BTC/USD",
  "side": "BUY",           # BUY or SELL
  "order_type": "LIMIT",   # LIMIT or MARKET
  "quantity": "1.5",
  "price": "50000.00"      # Required for LIMIT, null for MARKET
}
```

Response:
```json
{
  "order_id": "uuid",
  "status": "FILLED",      # OPEN, PARTIAL, FILLED, REJECTED
  "message": "Order submitted successfully. 2 trade(s) executed.",
  "trades": [...],
  "order": {...}
}
```

#### Cancel Order
```http
DELETE /orders/{symbol}/{order_id}
```

#### Get Order Book
```http
GET /orderbook/{symbol}?depth=10
```

Response:
```json
{
  "symbol": "BTC/USD",
  "bids": [{"price": "49900", "quantity": "1.5"}, ...],
  "asks": [{"price": "50100", "quantity": "2.0"}, ...],
  "best_bid": "49900",
  "best_ask": "50100",
  "spread": "200",
  "mid_price": "50000"
}
```

#### Get Recent Trades
```http
GET /trades/{symbol}?limit=50
```

### WebSocket

Connect to `ws://localhost:8000/ws` for real-time updates.

**Message Types Received:**
- `order_book_snapshot`: Initial order book state
- `order_book_update`: Order book changed
- `trade`: New trade executed
- `order_update`: Order status changed

Example message:
```json
{
  "type": "trade",
  "data": {
    "trade_id": "uuid",
    "symbol": "BTC/USD",
    "price": "50000.00",
    "quantity": "1.5",
    "timestamp": "2025-12-28T10:30:00Z",
    "buy_order_id": "uuid",
    "sell_order_id": "uuid"
  },
  "timestamp": "2025-12-28T10:30:00Z"
}
```

##  Features

### Core Matching Engine
✅ Price-Time Priority (FIFO) algorithm  
✅ Limit orders with price specification  
✅ Market orders (immediate execution)  
✅ Order cancellation  
✅ Partial fills  
✅ Multiple trading symbols  
✅ Deterministic replay mode - Engine supports deterministic replay by feeding recorded order streams and verifying identical trade outputs

### Real-time UI
✅ Live order book visualization  
✅ Color-coded bids (green) and asks (red)  
✅ Volume bars for depth visualization  
✅ Recent trade tape  
✅ Market statistics dashboard  
✅ WebSocket real-time updates  
✅ Order entry form  

### API & Performance
✅ REST API for order operations  
✅ WebSocket for market data streaming  
✅ Async I/O with uvloop  
✅ Event-driven architecture  
✅ Target: 50K-100K orders/second  



##  Testing

### Manual Testing

```bash
# Start backend
cd matching_engine
python api.py

# In another terminal, test with curl
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTC/USD",
    "side": "BUY",
    "order_type": "LIMIT",
    "quantity": "1.0",
    "price": "50000.00"
  }'
```



## References

### Core Papers
1. "Price-Time Priority and Pro-Rata Matching in an Order Book Model" (2010)
2. "Continuous Trading Matching Algorithm" - NEMO Committee Spec (2022)
3. "Limit Order Books" - Survey (2013)
4. "LOB-Bench: Benchmarking Generative AI for Finance" (2025)

### Implementation Papers
5. "CoinTossX: Open-Source Low-Latency High-Throughput Matching Engine" (2022)
6. "CloudEx: Fair-Access Financial Exchange in the Cloud" (2021)
7. "Design and Implementation of Scalable Financial Exchange" (2024)

### Data Structures & Performance
8. "Exploiting Concurrency in Domain-Specific Data Structures" (2016)
9. "The Bw-Tree: A B-tree for New Hardware Platforms" (2013)
10. "Disruptor: High Performance Alternative to Bounded Queues" (2011)
11. "Microsecond Consensus for Microsecond Applications" (2020)


---

