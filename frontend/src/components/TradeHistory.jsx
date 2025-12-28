/**
 * TradeHistory Component
 * 
 * Displays recent trades (trade tape)
 * Research note: This is standard in all trading UIs (LOB-Bench paper)
 */
import React from 'react'

function TradeHistory({ trades }) {
  if (!trades || trades.length === 0) {
    return (
      <div className="glass-card rounded-xl p-6 shadow-xl">
        <h3 className="text-xl font-bold mb-4 bg-gradient-to-r from-purple-400 to-pink-500 bg-clip-text text-transparent">
          📊 Recent Trades
        </h3>
        <div className="flex items-center justify-center py-8">
          <p className="text-gray-400 text-sm italic">No trades yet</p>
        </div>
      </div>
    )
  }

  return (
    <div className="glass-card rounded-xl p-6 shadow-xl">
      <div className="flex flex-col items-center mb-5">
        <h3 className="text-xl font-bold bg-gradient-to-r from-purple-400 to-pink-500 bg-clip-text text-transparent text-center">
          📊 Recent Trades
        </h3>
        <span className="text-xs text-gray-400 bg-gray-800/50 px-3 py-1.5 rounded-full mt-2">
          {trades.length} trades
        </span>
      </div>

      <div className="space-y-2 max-h-96 overflow-y-auto pr-2">
        {trades.map((trade, index) => {
          const time = new Date(trade.timestamp).toLocaleTimeString()
          const price = parseFloat(trade.price)
          const quantity = parseFloat(trade.quantity)

          return (
            <div 
              key={trade.trade_id || index}
              className="glass-card rounded-xl border border-purple-500/10 hover:border-purple-500/30 trade-flash transition-all p-4 text-center"
            >
              <div className="mb-2">
                <span className="font-mono text-lg font-bold text-blue-400">{price.toFixed(2)}</span>
              </div>
              <div className="mb-2">
                <span className="font-mono text-base font-semibold text-purple-400">{quantity.toFixed(4)}</span>
              </div>
              <div className="text-xs text-gray-400">
                Vol: <span className="text-pink-400 font-semibold">{(price * quantity).toFixed(2)}</span>
              </div>
              <div className="text-xs text-gray-400 mt-1 flex items-center justify-center gap-1">
                🕐 {time}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default TradeHistory
