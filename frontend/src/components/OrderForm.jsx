/**
 * OrderForm Component
 * 
 * Form for submitting orders to the matching engine
 * Supports limit and market orders on both sides (buy/sell)
 */
import { useState } from 'react'

function OrderForm({ onSubmit, symbol }) {
  const [orderType, setOrderType] = useState('LIMIT')
  const [side, setSide] = useState('BUY')
  const [quantity, setQuantity] = useState('')
  const [price, setPrice] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()

    if (!quantity || parseFloat(quantity) <= 0) {
      alert('Please enter a valid quantity')
      return
    }

    if (orderType === 'LIMIT' && (!price || parseFloat(price) <= 0)) {
      alert('Please enter a valid price for limit orders')
      return
    }

    const orderData = {
      order_type: orderType,
      side: side,
      quantity: quantity,
      price: orderType === 'LIMIT' ? price : null
    }

    onSubmit(orderData)

    // Reset form
    setQuantity('')
    setPrice('')
  }

  return (
    <div className="glass-card rounded-xl p-6 shadow-xl">
      <h3 className="text-xl font-bold mb-6 bg-gradient-to-r from-green-400 to-blue-500 bg-clip-text text-transparent text-center">
        📝 Place Order
      </h3>

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Order Type */}
        <div>
          <label className="block text-sm text-gray-400 mb-3 uppercase tracking-wide font-semibold">Order Type</label>
          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => setOrderType('LIMIT')}
              className={`py-3 rounded-xl font-semibold transition-all transform hover:scale-105 ${orderType === 'LIMIT' ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg glow-blue' : 'glass-card hover:bg-gray-700'}`}
            >
              Limit
            </button>
            <button
              type="button"
              onClick={() => setOrderType('MARKET')}
              className={`py-3 rounded-xl font-semibold transition-all transform hover:scale-105 ${orderType === 'MARKET' ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg glow-blue' : 'glass-card hover:bg-gray-700'}`}
            >
              Market
            </button>
          </div>
        </div>

        {/* Side */}
        <div>
          <label className="block text-sm text-gray-400 mb-3 uppercase tracking-wide font-semibold">Side</label>
          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => setSide('BUY')}
              className={`py-3 rounded-xl font-semibold transition-all transform hover:scale-105 ${side === 'BUY' ? 'bg-gradient-to-r from-green-600 to-emerald-600 text-white shadow-lg glow-green' : 'glass-card hover:bg-gray-700'}`}
            >
              Buy
            </button>
            <button
              type="button"
              onClick={() => setSide('SELL')}
              className={`py-3 rounded-xl font-semibold transition-all transform hover:scale-105 ${side === 'SELL' ? 'bg-gradient-to-r from-red-600 to-rose-600 text-white shadow-lg glow-red' : 'glass-card hover:bg-gray-700'}`}
            >
              Sell
            </button>
          </div>
        </div>

        {/* Price (only for limit orders) */}
        {orderType === 'LIMIT' && (
          <div>
            <label className="block text-sm text-gray-400 mb-2 uppercase tracking-wide font-semibold">Price</label>
            <input
              type="number"
              step="0.01"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              placeholder="Enter price"
              className="w-full p-3 glass-card border border-gray-600 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            />
          </div>
        )}

        {/* Quantity */}
        <div>
          <label className="block text-sm text-gray-400 mb-2 uppercase tracking-wide font-semibold">Quantity</label>
          <input
            type="number"
            step="0.0001"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
            placeholder="Enter quantity"
            className="w-full p-3 glass-card border border-gray-600 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
          />
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          className={`w-full py-4 rounded-xl font-bold text-lg transition-all transform hover:scale-105 shadow-lg ${
            side === 'BUY' 
              ? 'bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 glow-green' 
              : 'bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-700 hover:to-rose-700 glow-red'
          }`}
        >
          {side === 'BUY' ? '🚀 Buy' : '💸 Sell'} {symbol}
        </button>
      </form>

      {/* Info */}
      <div className="mt-5 p-4 glass-card rounded-xl text-xs text-gray-400 border border-blue-500/20">
        <p className="mb-2 flex items-start gap-2">
          <span className="text-blue-400">💡</span>
          <span><strong className="text-blue-400">Limit Order:</strong> Order at specific price (may not fill immediately)</span>
        </p>
        <p className="flex items-start gap-2">
          <span className="text-purple-400">⚡</span>
          <span><strong className="text-purple-400">Market Order:</strong> Order at best available price (fills immediately)</span>
        </p>
      </div>
    </div>
  )
}

export default OrderForm
