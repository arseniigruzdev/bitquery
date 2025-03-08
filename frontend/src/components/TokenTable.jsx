import { useState } from 'react';
import Link from 'next/link';

export default function TokenTable({ tokens }) {
  const [sortField, setSortField] = useState('market_cap');
  const [sortDirection, setSortDirection] = useState('desc');

  const handleSort = (field) => {
    if (field === sortField) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const sortedTokens = [...tokens].sort((a, b) => {
    if (a[sortField] === null) return 1;
    if (b[sortField] === null) return -1;
    
    if (sortDirection === 'asc') {
      return a[sortField] < b[sortField] ? -1 : 1;
    } else {
      return a[sortField] > b[sortField] ? -1 : 1;
    }
  });

  const formatCurrency = (value) => {
    if (value === null || value === undefined) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 6
    }).format(value);
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full bg-white border border-gray-200">
        <thead>
          <tr className="bg-gray-100">
            <th className="px-4 py-2 cursor-pointer" onClick={() => handleSort('token_name')}>
              Token Name
              {sortField === 'token_name' && (
                <span>{sortDirection === 'asc' ? ' ↑' : ' ↓'}</span>
              )}
            </th>
            <th className="px-4 py-2 cursor-pointer" onClick={() => handleSort('token_symbol')}>
              Symbol
              {sortField === 'token_symbol' && (
                <span>{sortDirection === 'asc' ? ' ↑' : ' ↓'}</span>
              )}
            </th>
            <th className="px-4 py-2 cursor-pointer" onClick={() => handleSort('price')}>
              Price
              {sortField === 'price' && (
                <span>{sortDirection === 'asc' ? ' ↑' : ' ↓'}</span>
              )}
            </th>
            <th className="px-4 py-2 cursor-pointer" onClick={() => handleSort('market_cap')}>
              Market Cap
              {sortField === 'market_cap' && (
                <span>{sortDirection === 'asc' ? ' ↑' : ' ↓'}</span>
              )}
            </th>
            <th className="px-4 py-2 cursor-pointer" onClick={() => handleSort('volume_24h')}>
              24h Volume
              {sortField === 'volume_24h' && (
                <span>{sortDirection === 'asc' ? ' ↑' : ' ↓'}</span>
              )}
            </th>
            <th className="px-4 py-2 cursor-pointer" onClick={() => handleSort('bonding_curve_progress')}>
              Bonding Curve
              {sortField === 'bonding_curve_progress' && (
                <span>{sortDirection === 'asc' ? ' ↑' : ' ↓'}</span>
              )}
            </th>
            <th className="px-4 py-2 cursor-pointer" onClick={() => handleSort('creation_time')}>
              Created
              {sortField === 'creation_time' && (
                <span>{sortDirection === 'asc' ? ' ↑' : ' ↓'}</span>
              )}
            </th>
            <th className="px-4 py-2">Status</th>
          </tr>
        </thead>
        <tbody>
          {sortedTokens.map((token) => (
            <tr key={token.id} className="border-t border-gray-200 hover:bg-gray-50">
              <td className="px-4 py-2">
                <Link href={`/tokens/${token.token_address}`}>
                  <a className="text-blue-600 hover:underline">
                    {token.token_name || 'Unknown'}
                  </a>
                </Link>
              </td>
              <td className="px-4 py-2">{token.token_symbol || 'N/A'}</td>
              <td className="px-4 py-2">{formatCurrency(token.price)}</td>
              <td className="px-4 py-2">{formatCurrency(token.market_cap)}</td>
              <td className="px-4 py-2">{formatCurrency(token.volume_24h)}</td>
              <td className="px-4 py-2">
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <div 
                    className="bg-blue-600 h-2.5 rounded-full" 
                    style={{ width: `${token.bonding_curve_progress || 0}%` }}
                  ></div>
                </div>
                <span className="text-xs">{token.bonding_curve_progress?.toFixed(2) || 0}%</span>
              </td>
              <td className="px-4 py-2">{formatDate(token.creation_time)}</td>
              <td className="px-4 py-2">
                {token.is_king_of_hill && (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 mr-1">
                    King
                  </span>
                )}
                {token.raydium_migrated && (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    Raydium
                  </span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
