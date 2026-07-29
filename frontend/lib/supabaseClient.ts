import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL as string;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY as string;

if (!supabaseUrl || !supabaseAnonKey) {
  // Fails fast in dev if .env.local wasn't set up, rather than a confusing
  // runtime error deep inside a query.
  console.warn(
    "NEXT_PUBLIC_SUPABASE_URL / NEXT_PUBLIC_SUPABASE_ANON_KEY are not set — see frontend/.env.example"
  );
}

// Safe to use in both server and client components: this is the anon key,
// and every table it can reach is protected by Row Level Security
// (supabase/migrations/0002_rls.sql) to public read-only on published rows.
export const supabase = createClient(supabaseUrl ?? "", supabaseAnonKey ?? "");
