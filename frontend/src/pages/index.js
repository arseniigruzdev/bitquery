import { useState, useEffect } from 'react';
import { supabase } from '../utils/supabaseClient';
import TokenTable from '../components/TokenTable';
import Dashboard from '../components/Dashboard';

export default function Home() {
  const [tokens, setTokens] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalTokens: 0,
    kingsOfHill: 0,
    raydiumMigrated: 0,
    averageMarketCap: 0
  });

  useEffect(() => {
    fetchTokens();
    fetchStats();
  }, []);

  async function fetchTokens() {
    try {
      setLoading(true);
      const { data, error } = await supabase
        .from('tokens')
        .select('*')
        .order('market_cap', { ascending: false })
        .limit(50);

      if (error) throw error;
      setTokens(data || []);
    } catch (error) {
      console.error('Error fetching tokens:', error);
    } finally {
      setLoading(false);
    }
  }

  async function fetchStats() {
    try {
      // Get total tokens count
      const { count: totalTokens } = await supabase
        .from('tokens')
        .select('*', { count: 'exact', head: true });

      // Get kings of hill count
      const { count: kingsOfHill } = await supabase
        .from('tokens')
        .select('*', { count: 'exact', head: true })
        .eq('is_king_of_hill', true);

      // Get raydium migrated count
      const { count: raydiumMigrated } = await supabase
        .from('tokens')
        .select('*', { count: 'exact', head: true })
        .eq('raydium_migrated', true);

      // Get average market cap
      const { data: marketCapData } = await supabase
        .from('tokens')
        .select('market_cap');

      const validMarketCaps = marketCapData
        .filter(token => token.market_cap)
        .map(token => token.market_cap);
      
      const averageMarketCap = validMarketCaps.length > 0
        ? validMarketCaps.reduce((sum, cap) => sum + cap, 0) / validMarketCaps.length
        : 0;

      setStats({
        totalTokens: totalTokens || 0,
        kingsOfHill: kingsOfHill || 0,
        raydiumMigrated: raydiumMigrated || 0,
        averageMarketCap
      });
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Solana Token Dashboard</h1>
      
      <Dashboard stats={stats} />
      
      <div className="mt-10">
        <h2 className="text-2xl font-semibold mb-4">Top Tokens</h2>
        {loading ? (
          <p>Loading tokens...</p>
        ) : (
          <TokenTable tokens={tokens} />
        )}
      </div>
    </div>
  );
}
