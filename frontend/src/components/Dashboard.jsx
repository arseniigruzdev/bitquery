export default function Dashboard({ stats }) {
  const formatNumber = (num) => {
    return new Intl.NumberFormat().format(Math.round(num));
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h3 className="text-lg font-medium text-gray-900">Total Tokens</h3>
        <p className="text-3xl font-bold text-indigo-600">{formatNumber(stats.totalTokens)}</p>
      </div>
      
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h3 className="text-lg font-medium text-gray-900">Kings of Hill</h3>
        <p className="text-3xl font-bold text-yellow-600">{formatNumber(stats.kingsOfHill)}</p>
      </div>
      
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h3 className="text-lg font-medium text-gray-900">Raydium Migrated</h3>
        <p className="text-3xl font-bold text-green-600">{formatNumber(stats.raydiumMigrated)}</p>
      </div>
      
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h3 className="text-lg font-medium text-gray-900">Avg. Market Cap</h3>
        <p className="text-3xl font-bold text-blue-600">{formatCurrency(stats.averageMarketCap)}</p>
      </div>
    </div>
  );
}
