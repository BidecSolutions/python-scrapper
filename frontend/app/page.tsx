"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();
  
  useEffect(() => {
    // Check if user is logged in
    const token = localStorage.getItem("auth_token");
    if (token) {
      router.push("/dashboard");
    } else {
      router.push("/login");
    }
  }, [router]);
  
  return (
    <div className="flex items-center justify-center h-screen bg-slate-950">
      <div className="text-slate-400">Redirecting...</div>
    </div>
  );
}

