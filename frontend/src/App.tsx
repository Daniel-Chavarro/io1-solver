import { useState } from "react";
import { MethodTabs } from "./components/MethodTabs";
import { ProblemForm } from "./components/ProblemForm";

export default function App() {
  const [tab, setTab] = useState("resolver");
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white px-6 py-4">
        <h1 className="text-xl font-bold">io1-solver — Simplex y Gran M</h1>
        <p className="text-sm text-slate-500">Investigación de Operaciones 1 · Grupo 3</p>
      </header>
      <main className="mx-auto max-w-5xl px-6 py-6">
        <MethodTabs value={tab} onChange={setTab} />
        {tab === "resolver" ? (
          <ProblemForm />
        ) : (
          <div className="mt-6 rounded border border-dashed border-slate-300 p-6 text-sm text-slate-500">
            Sección «{tab}» — pendiente de implementación (ver issues).
          </div>
        )}
      </main>
    </div>
  );
}
