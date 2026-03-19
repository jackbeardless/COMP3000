import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { getCases, createCase, updateCase, deleteCase } from "../lib/api";
import { Card, CardBody } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { Spinner } from "../components/ui/Spinner";
import { Plus, FolderOpen, Archive, Trash2, ChevronRight, Search } from "lucide-react";
import { formatDistanceToNow } from "../lib/time";

export function CasesPage() {
  const qc = useQueryClient();
  const navigate = useNavigate();
  const [showNew, setShowNew] = useState(false);
  const [name, setName]       = useState("");
  const [target, setTarget]   = useState("");
  const [description, setDesc] = useState("");
  const [search, setSearch]   = useState("");

  const { data: cases = [], isLoading } = useQuery({ queryKey: ["cases"], queryFn: getCases });

  const create = useMutation({
    mutationFn: () => createCase({ name, target, description }),
    onSuccess: (c) => { qc.invalidateQueries({ queryKey: ["cases"] }); setShowNew(false); setName(""); setTarget(""); setDesc(""); navigate(`/cases/${c.id}`); },
  });

  const archive = useMutation({
    mutationFn: (id) => updateCase(id, { status: "archived" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["cases"] }),
  });

  const remove = useMutation({
    mutationFn: (id) => deleteCase(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["cases"] }),
  });

  const filtered = cases.filter(c =>
    c.name.toLowerCase().includes(search.toLowerCase()) ||
    c.target.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="max-w-3xl mx-auto py-8 px-4">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Cases</h1>
          <p className="text-gray-500 text-sm mt-0.5">Each case is an OSINT investigation into a target</p>
        </div>
        <Button onClick={() => setShowNew(true)}><Plus size={16} /> New Case</Button>
      </div>

      {/* Search */}
      <div className="relative mb-4">
        <Search size={16} className="absolute left-3 top-2.5 text-gray-400" />
        <input
          value={search} onChange={e => setSearch(e.target.value)}
          placeholder="Search cases or targets…"
          className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm
            focus:outline-none focus:ring-2 focus:ring-brand-500"
        />
      </div>

      {/* New case form */}
      {showNew && (
        <Card className="mb-4 border-brand-200">
          <CardBody>
            <h2 className="font-semibold text-gray-900 mb-3">New Case</h2>
            <div className="space-y-3">
              <input value={name} onChange={e => setName(e.target.value)} placeholder="Case name *"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" />
              <input value={target} onChange={e => setTarget(e.target.value)} placeholder="Target username *"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" />
              <textarea value={description} onChange={e => setDesc(e.target.value)} placeholder="Description (optional)" rows={2}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none" />
              <div className="flex gap-2">
                <Button onClick={() => create.mutate()} disabled={!name || !target || create.isPending}>
                  {create.isPending ? <Spinner size="sm" /> : "Create"}
                </Button>
                <Button variant="secondary" onClick={() => setShowNew(false)}>Cancel</Button>
              </div>
            </div>
          </CardBody>
        </Card>
      )}

      {/* Cases list */}
      {isLoading ? (
        <div className="flex justify-center py-16"><Spinner size="lg" /></div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <FolderOpen size={40} className="mx-auto mb-3 opacity-40" />
          <p>{search ? "No matching cases." : "No cases yet. Create one to get started."}</p>
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map(c => (
            <Card key={c.id} className="hover:border-brand-300 transition-colors cursor-pointer"
              onClick={() => navigate(`/cases/${c.id}`)}>
              <CardBody>
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-gray-900 truncate">{c.name}</span>
                      <Badge variant={c.status} label={c.status} />
                    </div>
                    <div className="flex items-center gap-3 mt-1">
                      <span className="text-sm text-gray-500">Target: <span className="font-mono text-gray-700">{c.target}</span></span>
                      <span className="text-xs text-gray-400">{c.total_scans ?? 0} scan{c.total_scans !== 1 ? "s" : ""}</span>
                      <span className="text-xs text-gray-400">{formatDistanceToNow(c.updated_at)}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-1 ml-3" onClick={e => e.stopPropagation()}>
                    {c.status === "active" && (
                      <button className="p-1.5 text-gray-400 hover:text-gray-600 rounded"
                        title="Archive" onClick={() => archive.mutate(c.id)}>
                        <Archive size={15} />
                      </button>
                    )}
                    <button className="p-1.5 text-gray-400 hover:text-red-500 rounded"
                      title="Delete" onClick={() => { if (confirm(`Delete case "${c.name}"?`)) remove.mutate(c.id); }}>
                      <Trash2 size={15} />
                    </button>
                    <ChevronRight size={16} className="text-gray-300 ml-1" />
                  </div>
                </div>
              </CardBody>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
