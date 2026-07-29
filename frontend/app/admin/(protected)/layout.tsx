"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabaseClient";
import { api, ApiError } from "@/lib/api";
import AdminSidebar from "@/components/AdminSidebar";

type AuthState = { status: "loading" } | { status: "authorized"; email: string } | { status: "denied" };

export default function ProtectedAdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [auth, setAuth] = useState<AuthState>({ status: "loading" });

  useEffect(() => {
    let active = true;

    async function check() {
      const { data } = await supabase.auth.getSession();
      if (!data.session) {
        if (active) setAuth({ status: "denied" });
        router.replace("/admin/login");
        return;
      }
      try {
        const me = await api.get<{ email: string; role: string }>("/api/v1/auth/me");
        if (active) setAuth({ status: "authorized", email: me.email });
      } catch (err) {
        if (active) setAuth({ status: "denied" });
        if (err instanceof ApiError && (err.status === 401 || err.status === 403)) {
          router.replace("/admin/login");
        }
      }
    }

    check();
    return () => {
      active = false;
    };
  }, [router]);

  if (auth.status === "loading") {
    return <p className="p-8 text-slate-500">Checking access…</p>;
  }
  if (auth.status === "denied") {
    return <p className="p-8 text-slate-500">Redirecting to sign in…</p>;
  }

  return (
    <div className="flex flex-col gap-4 lg:min-h-[70vh] lg:flex-row lg:gap-0">
      <AdminSidebar email={auth.email} />
      <div className="flex-1 py-2 lg:py-6 lg:pl-6">{children}</div>
    </div>
  );
}
