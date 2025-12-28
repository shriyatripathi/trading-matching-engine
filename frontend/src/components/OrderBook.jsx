/**
 * OrderBook Component
 * 
 * Displays real-time order book with price levels and quantities
 * Based on research: Standard "ladder" visualization used by all exchanges
 * 
 * Features:
 * - Color-coded bids (green) and asks (red)
 * - Volume bars for visual depth
 * - Best bid/ask highlighted
 * - Spread calculation
 */
import React from 'react'

function OrderBook({ orderBook, symbol }) {
  if (!orderBook) {
    return (
      <div className="glass-card rounded-xl p-6">
        <h2 className="text-2xl font-bold mb-4 bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
          Order Book - {symbol}
        </h2>
        <div className="flex items-center justify-center py-8">
          <div className="animate-pulse text-gray-400">Loading order book...</div>
        </div>
      </div>
    )
  }

  const { bids, asks, best_bid, best_ask, spread, mid_price } = orderBook

  // Calculate max volume for bar chart scaling
  const allVolumes = [...bids, ...asks].map(level => parseFloat(level.quantity))
  const maxVolume = Math.max(...allVolumes, 1)

  const PriceLevel = ({ price, quantity, side, isBest }) => {
    const volumePercent = (parseFloat(quantity) / maxVolume) * 100
    const color = side === 'bid' ? 'bg-green-500' : 'bg-red-500'
    const textColor = side === 'bid' ? 'text-green-400' : 'text-red-400'

    return (
      <tr className={`relative order-book-row ${isBest ? 'glass-card font-bold ring-2 ring-blue-500/50' : ''}`}>
        {/* Volume bar background */}
        <td className="relative py-3 px-4 text-center">
          <div 
            className={`absolute inset-0 ${color} opacity-20`}
            style={{ width: `${volumePercent}%` }}
          ></div>
          <span className={`relative font-mono text-base ${textColor} ${isBest ? 'font-bold' : ''}`}>
            {parseFloat(price).toFixed(2)}
          </span>
        </td>
        <td className="relative py-3 px-4 text-center">
          <span className="relative font-mono text-gray-300 text-base">
            {parseFloat(quantity).toFixed(4)}
          </span>
        </td>
      </tr>
    )
  }

  return (
    <div className="glass-card rounded-xl p-6 shadow-xl">
      <div className="flex flex-col items-center mb-6">
        <h2 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent text-center">
          📖 Order Book - {symbol}
        </h2>
        <div className="text-xs text-gray-400 bg-gray-800/50 px-3 py-1.5 rounded-full mt-2">
          {bids.length + asks.length} levels
        </div>
      </div>

      {/* Market Info */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="glass-card p-4 rounded-xl border border-green-500/20 glow-green text-center">
          <div className="text-xs text-gray-400 mb-1">Best Bid</div>
          <div className="text-xl font-mono text-green-400 font-bold">
            {best_bid ? parseFloat(best_bid).toFixed(2) : '-'}
          </div>
        </div>
        <div className="glass-card p-4 rounded-xl border border-red-500/20 glow-red text-center">
          <div className="text-xs text-gray-400 mb-1">Best Ask</div>
          <div className="text-xl font-mono text-red-400 font-bold">
            {best_ask ? parseFloat(best_ask).toFixed(2) : '-'}
          </div>
        </div>
        <div className="glass-card p-4 rounded-xl border border-yellow-500/20 text-center">
          <div className="text-xs text-gray-400 mb-1">Spread</div>
          <div className="text-xl font-mono text-yellow-400 font-bold">
            {spread ? parseFloat(spread).toFixed(2) : '-'}
          </div>
        </div>
      </div>

      {/* Order Book Ladder */}
      <div className="grid grid-cols-2 gap-4">
        {/* Asks (Sell Orders) - Top to bottom, best (lowest) at bottom */}
        <div className="glass-card rounded-xl overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-red-500/20">
                <th className="text-xs text-gray-400 uppercase tracking-wide font-semibold py-3 text-center">Price (Ask)</th>
                <th className="text-xs text-gray-400 uppercase tracking-wide font-semibold py-3 text-center">Quantity</th>
              </tr>
            </thead>
            <tbody>
              {asks.length > 0 ? (
                [...asks].reverse().map((level, index) => (
                  <PriceLevel
                    key={index}
                    price={level.price}
                    quantity={level.quantity}
                    side="ask"
                    isBest={level.price === best_ask}
                  />
                ))
              ) : (
                <tr>
                  <td colSpan="2" className="p-6 text-center text-gray-500 italic">No sell orders</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Bids (Buy Orders) - Top to bottom, best (highest) at top */}
        <div className="glass-card rounded-xl overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-green-500/20">
                <th className="text-xs text-gray-400 uppercase tracking-wide font-semibold py-3 text-center">Price (Bid)</th>
                <th className="text-xs text-gray-400 uppercase tracking-wide font-semibold py-3 text-center">Quantity</th>
              </tr>
            </thead>
            <tbody>
              {bids.length > 0 ? (
                bids.map((level, index) => (
                  <PriceLevel
                    key={index}
                    price={level.price}
                    quantity={level.quantity}
                    side="bid"
                    isBest={level.price === best_bid}
                  />
                ))
              ) : (
                <tr>
                  <td colSpan="2" className="p-6 text-center text-gray-500 italic">No buy orders</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Mid Price */}
      {mid_price && (
        <div className="mt-6 text-center p-3 glass-card rounded-xl">
          <span className="text-sm text-gray-400">Mid Price: </span>
          <span className="font-mono text-blue-400 text-lg font-bold">{parseFloat(mid_price).toFixed(2)}</span>
        </div>
      )}
    </div>
  )
}

export default OrderBook
