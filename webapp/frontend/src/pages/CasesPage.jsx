import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { getCases, createCase, updateCase, deleteCase, getMyOrg, createDeletionRequest } from "../lib/api";
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
  const [description, setDesc] = useState("");
  const [search, setSearch]   = useState("");
  const [knownName, setKnownName]         = useState("");
  const [knownAliases, setKnownAliases]   = useState("");
  const [knownLocation, setKnownLocation] = useState("");
  const [knownNotes, setKnownNotes]       = useState("");
  const [showKnownInfo, setShowKnownInfo] = useState(false);
  const [createError, setCreateError]     = useState("");

  const { data: cases = [], isLoading } = useQuery({ queryKey: ["cases"], queryFn: getCases });
  const { data: org } = useQuery({ queryKey: ["org-me"], queryFn: getMyOrg });
  const isAdmin = org?.role === "admin";

  const create = useMutation({
    mutationFn: () => createCase({ name, description, known_info: { known_name: knownName, known_aliases: knownAliases, known_location: knownLocation, known_notes: knownNotes } }),
    onSuccess: (c) => { qc.invalidateQueries({ queryKey: ["cases"] }); setShowNew(false); setCreateError(""); setName(""); setDesc(""); setKnownName(""); setKnownAliases(""); setKnownLocation(""); setKnownNotes(""); navigate(`/cases/${c.id}`); },
    onError: (e) => setCreateError(e?.response?.data?.detail || e?.message || "Failed to create case."),
  });

  const archive = useMutation({
    mutationFn: (id) => updateCase(id, { status: "archived" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["cases"] }),
  });

  const remove = useMutation({
    mutationFn: (id) => deleteCase(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["cases"] }),
  });

  const requestDelete = useMutation({
    mutationFn: ({ id, name }) => createDeletionRequest({ resource_type: "case", resource_id: id, resource_name: name }),
    onSuccess: () => alert("Deletion request submitted. An admin will review it."),
    onError: (e) => alert(e?.response?.data?.detail || "Failed to submit deletion request."),
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
              <textarea value={description} onChange={e => setDesc(e.target.value)} placeholder="Description (optional)" rows={2}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none" />
              <button
                type="button"
                onClick={() => setShowKnownInfo(v => !v)}
                className="text-sm text-gray-500 hover:text-gray-700 text-left"
              >
                Known information (optional) {showKnownInfo ? "▴" : "▾"}
              </button>
              {showKnownInfo && (
                <div className="space-y-2 p-3 bg-gray-50 rounded-lg border border-gray-200">
                  <input value={knownName} onChange={e => setKnownName(e.target.value)} placeholder="Full name (e.g. Mark Zuckerberg)"
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm bg-gray-50 focus:outline-none focus:ring-2 focus:ring-brand-500" />
                  <input value={knownAliases} onChange={e => setKnownAliases(e.target.value)} placeholder="Other aliases (comma-separated)"
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm bg-gray-50 focus:outline-none focus:ring-2 focus:ring-brand-500" />
                  <input value={knownLocation} onChange={e => setKnownLocation(e.target.value)} placeholder="Location (e.g. San Francisco, CA)"
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm bg-gray-50 focus:outline-none focus:ring-2 focus:ring-brand-500" />
                  <input value={knownNotes} onChange={e => setKnownNotes(e.target.value)} placeholder="Additional notes (job, bio keywords…)"
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm bg-gray-50 focus:outline-none focus:ring-2 focus:ring-brand-500" />
                </div>
              )}
              {createError && (
                <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2">{createError}</p>
              )}
              <div className="flex gap-2">
                <Button onClick={() => create.mutate()} disabled={!name || create.isPending}>
                  {create.isPending ? <Spinner size="sm" /> : "Create"}
                </Button>
                <Button variant="secondary" onClick={() => { setShowNew(false); setCreateError(""); }}>Cancel</Button>
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
                      {c.target && <span className="text-sm text-gray-500">Target: <span className="font-mono text-gray-700">{c.target}</span></span>}
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
                    {isAdmin ? (
                      <button className="p-1.5 text-gray-400 hover:text-red-500 rounded"
                        title="Delete" onClick={() => { if (confirm(`Delete case "${c.name}"?`)) remove.mutate(c.id); }}>
                        <Trash2 size={15} />
                      </button>
                    ) : (
                      <button className="p-1.5 text-gray-400 hover:text-amber-500 rounded"
                        title="Request deletion" onClick={() => { if (confirm(`Request deletion of "${c.name}"? An admin will need to approve it.`)) requestDelete.mutate({ id: c.id, name: c.name }); }}>
                        <Trash2 size={15} />
                      </button>
                    )}
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
