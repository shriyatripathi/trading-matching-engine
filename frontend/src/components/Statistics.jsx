/**
 * Statistics Component
 * 
 * Displays market statistics:
 * - Last trade price
 * - Spread
 * - Total orders in book
 * - Volume statistics
 * 
 * Research note: Key metrics from LOB-Bench paper
 */
import React, { useEffect, useState } from 'react'

function Statistics({ orderBook, trades }) {
  const [stats, setStats] = useState({
    lastPrice: null,
    priceChange: 0,
    spread: null,
    totalOrders: 0,
    volume24h: 0
  })

  useEffect(() => {
    if (!orderBook) return

    const totalBids = orderBook.bids.length
    const totalAsks = orderBook.asks.length
    const totalOrders = totalBids + totalAsks

    // Calculate 24h volume from trades (sum of all trade quantities * price)
    const volume24h = trades.reduce((sum, trade) => {
      return sum + (parseFloat(trade.price) * parseFloat(trade.quantity))
    }, 0)

    // Price change (compare with first trade)
    const lastPrice = orderBook.last_trade_price ? parseFloat(orderBook.last_trade_price) : null
    const firstTradePrice = trades.length > 0 ? parseFloat(trades[trades.length - 1].price) : null
    const priceChange = lastPrice && firstTradePrice ? ((lastPrice - firstTradePrice) / firstTradePrice * 100) : 0

    setStats({
      lastPrice,
      priceChange,
      spread: orderBook.spread ? parseFloat(orderBook.spread) : null,
      totalOrders,
      volume24h
    })
  }, [orderBook, trades])

  const StatCard = ({ label, value, suffix = '', valueColor = 'text-white', icon }) => (
    <div className="glass-card rounded-xl p-5 transform hover:scale-105 transition-all text-center">
      <div className="flex items-center justify-center gap-2 mb-2">
        {icon && <span className="text-2xl">{icon}</span>}
        <div className="text-xs text-gray-400 uppercase tracking-wide font-medium">{label}</div>
      </div>
      <div className={`text-3xl font-bold ${valueColor}`}>
        {value !== null && value !== undefined ? value : '-'}
        {suffix && <span className="text-base ml-1 text-gray-400">{suffix}</span>}
      </div>
    </div>
  )

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <StatCard
        label="Last Price"
        value={stats.lastPrice !== null ? stats.lastPrice.toFixed(2) : '-'}
        valueColor="text-blue-400"
        icon="💰"
      />

      <StatCard
        label="24h Change"
        value={stats.priceChange !== 0 ? `${stats.priceChange > 0 ? '+' : ''}${stats.priceChange.toFixed(2)}` : '-'}
        suffix="%"
        valueColor={stats.priceChange > 0 ? 'text-green-400' : stats.priceChange < 0 ? 'text-red-400' : 'text-white'}
        icon={stats.priceChange > 0 ? '📈' : stats.priceChange < 0 ? '📉' : '➖'}
      />

      <StatCard
        label="Spread"
        value={stats.spread !== null ? stats.spread.toFixed(2) : '-'}
        valueColor="text-yellow-400"
        icon="📊"
      />

      <StatCard
        label="Orders in Book"
        value={stats.totalOrders}
        valueColor="text-purple-400"
        icon="📋"
      />
    </div>
  )
}

export default Statistics
