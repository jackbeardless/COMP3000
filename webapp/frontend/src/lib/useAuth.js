import { useState, useEffect } from "react";
import { supabase } from "./supabase";

export function useAuth() {
  const [user, setUser]       = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      setUser(data.session?.user ?? null);
      setLoading(false);
    });
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_e, session) => {
      setUser(session?.user ?? null);
    });
    return () => subscription.unsubscribe();
  }, []);

  const signIn  = (email, password) => supabase.auth.signInWithPassword({ email, password });
  const signUp  = (email, password, username) =>
    supabase.auth.signUp({ email, password, options: { data: { username } } });
  const signOut = () => supabase.auth.signOut();

  return { user, loading, signIn, signUp, signOut };
}
