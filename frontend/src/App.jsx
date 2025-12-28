/**
 * Main App component for the Trading Matching Engine UI
 * 
 * Based on research:
 * - Real-time order book visualization (LOB-Bench paper)
 * - WebSocket for live updates (standard in all exchanges)
 * - Trade tape showing recent executions
 * - Market statistics dashboard
 */
import { useState, useEffect } from 'react'
import axios from 'axios'
import OrderBook from './components/OrderBook'
import OrderForm from './components/OrderForm'
import TradeHistory from './components/TradeHistory'
import Statistics from './components/Statistics'
import './index.css'

const API_BASE = 'http://localhost:8000'
const WS_URL = 'ws://localhost:8000/ws'

function App() {
  const [symbol, setSymbol] = useState('BTC/USD')
  const [orderBook, setOrderBook] = useState(null)
  const [trades, setTrades] = useState([])
  const [wsConnected, setWsConnected] = useState(false)
  const [lastUpdate, setLastUpdate] = useState(null)

  // WebSocket connection for real-time updates
  useEffect(() => {
    let ws = null

    const connectWebSocket = () => {
      ws = new WebSocket(WS_URL)

      ws.onopen = () => {
        console.log('WebSocket connected')
        setWsConnected(true)
      }

      ws.onmessage = (event) => {
        const message = JSON.parse(event.data)
        setLastUpdate(new Date())

        switch (message.type) {
          case 'order_book_snapshot':
          case 'order_book_update':
            if (message.data.symbol === symbol) {
              setOrderBook(message.data)
            }
            break

          case 'trade':
            if (message.data.symbol === symbol) {
              setTrades(prev => [message.data, ...prev].slice(0, 50))
            }
            break

          case 'order_update':
            console.log('Order update:', message.data)
            break

          default:
            break
        }
      }

      ws.onclose = () => {
        console.log('WebSocket disconnected, reconnecting...')
        setWsConnected(false)
        setTimeout(connectWebSocket, 3000)
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        ws.close()
      }
    }

    connectWebSocket()

    return () => {
      if (ws) {
        ws.close()
      }
    }
  }, [symbol])

  // Initial data fetch
  useEffect(() => {
    fetchOrderBook()
    fetchTrades()
  }, [symbol])

  const fetchOrderBook = async () => {
    try {
      const response = await axios.get(`${API_BASE}/orderbook`, {
        params: { symbol }
      })
      setOrderBook(response.data)
    } catch (error) {
      console.error('Error fetching order book:', error)
    }
  }

  const fetchTrades = async () => {
    try {
      const response = await axios.get(`${API_BASE}/trades`, {
        params: { symbol }
      })
      setTrades(response.data)
    } catch (error) {
      console.error('Error fetching trades:', error)
    }
  }

  const handleOrderSubmit = async (orderData) => {
    try {
      const response = await axios.post(`${API_BASE}/orders`, {
        symbol,
        ...orderData
      })
      
      console.log('Order submitted:', response.data)
      
      // Show notification
      if (response.data.status === 'REJECTED') {
        alert(`Order rejected: ${response.data.message}`)
      } else {
        const tradeCount = response.data.trades.length
        alert(`Order submitted! Status: ${response.data.status}. ${tradeCount} trade(s) executed.`)
      }
      
      // Refresh data
      await fetchOrderBook()
      await fetchTrades()
    } catch (error) {
      console.error('Error submitting order:', error)
      alert(`Error: ${error.response?.data?.detail || error.message}`)
    }
  }

  return (
    <div className="min-h-screen text-gray-100">
      {/* Header */}
      <header className="glass-card sticky top-0 z-50 backdrop-blur-md border-b border-gray-700/50 p-6 shadow-xl">
        <div className="container mx-auto">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg glow-blue">
                <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
              </div>
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                  Trading Matching Engine
                </h1>
                <p className="text-sm text-gray-400 mt-1">
                  Price-Time Priority (FIFO) Algorithm · Research Implementation
                </p>
              </div>
            </div>
            <div className="flex items-center gap-6">
              <div className={`flex items-center gap-2 px-4 py-2 rounded-full ${wsConnected ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
                <div className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-green-400' : 'bg-red-400'} animate-pulse`}></div>
                <span className="text-sm font-medium">{wsConnected ? 'Live' : 'Disconnected'}</span>
              </div>
              {lastUpdate && (
                <span className="text-xs text-gray-400 bg-gray-800/50 px-3 py-1.5 rounded-full">
                  🕒 {lastUpdate.toLocaleTimeString()}
                </span>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="container mx-auto p-4">
        {/* Symbol Selector */}
        <div className="mb-6 flex gap-3">
          <button
            onClick={() => setSymbol('BTC/USD')}
            className={`px-6 py-3 rounded-xl font-semibold transition-all transform hover:scale-105 ${symbol === 'BTC/USD' ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg glow-blue' : 'glass-card text-gray-300 hover:bg-gray-700'}`}
          >
            💎 BTC/USD
          </button>
          <button
            onClick={() => setSymbol('ETH/USD')}
            className={`px-6 py-3 rounded-xl font-semibold transition-all transform hover:scale-105 ${symbol === 'ETH/USD' ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg glow-blue' : 'glass-card text-gray-300 hover:bg-gray-700'}`}
          >
            ⚡ ETH/USD
          </button>
          <button
            onClick={() => setSymbol('AAPL')}
            className={`px-6 py-3 rounded-xl font-semibold transition-all transform hover:scale-105 ${symbol === 'AAPL' ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg glow-blue' : 'glass-card text-gray-300 hover:bg-gray-700'}`}
          >
            🍎 AAPL
          </button>
        </div>

        {/* Statistics */}
        {orderBook && <Statistics orderBook={orderBook} trades={trades} />}

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mt-4">
          {/* Order Book - Takes 2 columns */}
          <div className="lg:col-span-2">
            <OrderBook orderBook={orderBook} symbol={symbol} />
          </div>

          {/* Side Panel */}
          <div className="space-y-4">
            {/* Order Entry Form */}
            <OrderForm onSubmit={handleOrderSubmit} symbol={symbol} />

            {/* Trade History */}
            <TradeHistory trades={trades} />
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="glass-card border-t border-gray-700/50 mt-12 p-6">
        <div className="container mx-auto text-center">
          <p className="text-sm text-gray-400">
            📚 Based on research: <span className="text-blue-400">Price-Time Priority (FIFO)</span>, 
            <span className="text-purple-400">CoinTossX (2022)</span>, 
            <span className="text-pink-400">Limit Order Books Survey (2013)</span>, 
            <span className="text-indigo-400">CloudEx (2021)</span>
          </p>
          <p className="text-xs text-gray-500 mt-2">Built with research-backed best practices for educational purposes</p>
        </div>
      </footer>
    </div>
  )
}

export default App
