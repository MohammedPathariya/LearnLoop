import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { supabase } from './supabase';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(Boolean(supabase));

  useEffect(() => {
    if (!supabase) return undefined;

    let mounted = true;
    supabase.auth.getSession().then(({ data }) => {
      if (mounted) {
        setSession(data.session);
        setLoading(false);
      }
    });

    const { data: listener } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession);
      setLoading(false);
    });

    return () => {
      mounted = false;
      listener.subscription.unsubscribe();
    };
  }, []);

  const value = useMemo(() => ({
    session,
    user: session?.user || null,
    loading,
    configured: Boolean(supabase),
    async signIn(email, password) {
      if (!supabase) throw new Error('Supabase is not configured');
      const result = await supabase.auth.signInWithPassword({ email, password });
      if (result.error) throw result.error;
      return result.data;
    },
    async signUp(email, password) {
      if (!supabase) throw new Error('Supabase is not configured');
      const result = await supabase.auth.signUp({ email, password });
      if (result.error) throw result.error;
      return result.data;
    },
    async signOut() {
      if (!supabase) return;
      const result = await supabase.auth.signOut();
      if (result.error) throw result.error;
    },
  }), [loading, session]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
