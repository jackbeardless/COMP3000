import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getMyOrg, createOrg, getMembers, inviteMember, removeMember,
  getDeletionRequests, approveDeletionRequest, rejectDeletionRequest,
} from "../lib/api";
import { Card, CardBody, CardHeader } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { Spinner } from "../components/ui/Spinner";
import { Building2, UserPlus, Users, Trash2, Check, X, Mail, Clock } from "lucide-react";
import { formatDistanceToNow } from "../lib/time";

export function OrgPage() {
  const qc = useQueryClient();
  const { data: org, isLoading } = useQuery({ queryKey: ["org-me"], queryFn: getMyOrg });

  if (isLoading) return <div className="flex justify-center py-24"><Spinner size="lg" /></div>;

  if (!org) return <NoOrgView onCreated={() => qc.invalidateQueries({ queryKey: ["org-me"] })} />;

  return (
    <div className="max-w-3xl mx-auto py-8 px-4 space-y-6">
      <div className="flex items-center gap-3">
        <Building2 size={22} className="text-brand-600" />
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{org.name}</h1>
          <p className="text-sm text-gray-500">
            {org.role === "admin" ? "You are the admin of this organisation" : "You are a member of this organisation"}
          </p>
        </div>
      </div>

      <MembersSection org={org} />

      {org.role === "admin" && (
        <>
          <InviteSection orgId={org.id} />
          <DeletionRequestsSection orgId={org.id} />
        </>
      )}
    </div>
  );
}


// ── No-org view ────────────────────────────────────────────────
function NoOrgView({ onCreated }) {
  const [name, setName] = useState("");
  const [error, setError] = useState("");

  const create = useMutation({
    mutationFn: () => createOrg({ name }),
    onSuccess: onCreated,
    onError: (e) => setError(e?.response?.data?.detail || "Failed to create organisation."),
  });

  return (
    <div className="max-w-md mx-auto py-16 px-4 text-center">
      <Building2 size={40} className="mx-auto mb-4 text-gray-300" />
      <h1 className="text-xl font-bold text-gray-900 mb-2">You're not in an organisation</h1>
      <p className="text-gray-500 text-sm mb-6">
        Create a new organisation to start collaborating, or accept an invite from your admin.
      </p>

      <Card className="text-left">
        <CardBody>
          <h2 className="font-semibold text-gray-900 mb-3">Create Organisation</h2>
          <div className="space-y-3">
            <input
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="Organisation name *"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
            {error && <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2">{error}</p>}
            <Button onClick={() => create.mutate()} disabled={!name.trim() || create.isPending}>
              {create.isPending ? <Spinner size="sm" /> : "Create Organisation"}
            </Button>
          </div>
        </CardBody>
      </Card>

      <p className="text-sm text-gray-400 mt-6">
        If you've been invited, check your email for a link and make sure you're signed in with the invited address.
      </p>
    </div>
  );
}


// ── Members section ────────────────────────────────────────────
function MembersSection({ org }) {
  const qc = useQueryClient();
  const { data: members = [], isLoading } = useQuery({
    queryKey: ["members", org.id],
    queryFn: () => getMembers(org.id),
  });

  const remove = useMutation({
    mutationFn: (memberId) => removeMember(org.id, memberId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["members", org.id] }),
  });

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Users size={16} className="text-gray-500" />
          <span className="font-semibold text-gray-900 text-sm">Members</span>
          <span className="text-xs text-gray-400 ml-auto">{members.length} total</span>
        </div>
      </CardHeader>
      <CardBody>
        {isLoading ? (
          <div className="flex justify-center py-4"><Spinner /></div>
        ) : (
          <div className="space-y-2">
            {members.map(m => (
              <div key={m.id} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-gray-800">{m.email}</span>
                    <Badge variant={m.role === "admin" ? "active" : "default"} label={m.role} />
                    {m.status === "pending" && (
                      <span className="text-xs text-amber-600 bg-amber-50 border border-amber-200 rounded px-1.5 py-0.5 flex items-center gap-1">
                        <Clock size={10} /> pending
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {m.joined_at ? `Joined ${formatDistanceToNow(m.joined_at)}` : `Invited ${formatDistanceToNow(m.invited_at)}`}
                  </p>
                </div>
                {org.role === "admin" && m.role !== "admin" && (
                  <button
                    className="p-1.5 text-gray-400 hover:text-red-500 rounded"
                    title="Remove member"
                    onClick={() => { if (confirm(`Remove ${m.email} from the organisation?`)) remove.mutate(m.id); }}
                  >
                    <Trash2 size={14} />
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </CardBody>
    </Card>
  );
}


// ── Invite section ─────────────────────────────────────────────
function InviteSection({ orgId }) {
  const qc = useQueryClient();
  const [email, setEmail] = useState("");
  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");

  const invite = useMutation({
    mutationFn: () => inviteMember(orgId, { email }),
    onSuccess: () => {
      setSuccess(`Invite sent to ${email}`);
      setEmail("");
      setError("");
      qc.invalidateQueries({ queryKey: ["members", orgId] });
      setTimeout(() => setSuccess(""), 4000);
    },
    onError: (e) => {
      setError(e?.response?.data?.detail || "Failed to send invite.");
      setSuccess("");
    },
  });

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <UserPlus size={16} className="text-gray-500" />
          <span className="font-semibold text-gray-900 text-sm">Invite Member</span>
        </div>
      </CardHeader>
      <CardBody>
        <p className="text-xs text-gray-500 mb-3">
          The person must already have a Vantage account. They'll receive an email with an invite link.
        </p>
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Mail size={14} className="absolute left-3 top-2.5 text-gray-400" />
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="employee@company.com"
              className="w-full pl-8 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
              onKeyDown={e => e.key === "Enter" && email && invite.mutate()}
            />
          </div>
          <Button onClick={() => invite.mutate()} disabled={!email.trim() || invite.isPending}>
            {invite.isPending ? <Spinner size="sm" /> : "Send Invite"}
          </Button>
        </div>
        {success && <p className="text-sm text-green-600 mt-2">{success}</p>}
        {error && <p className="text-sm text-red-600 mt-2">{error}</p>}
      </CardBody>
    </Card>
  );
}


// ── Deletion requests section ──────────────────────────────────
function DeletionRequestsSection({ orgId }) {
  const qc = useQueryClient();
  const { data: requests = [], isLoading } = useQuery({
    queryKey: ["deletion-requests", orgId],
    queryFn: () => getDeletionRequests(orgId),
    refetchInterval: 15000,
  });

  const approve = useMutation({
    mutationFn: (id) => approveDeletionRequest(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["deletion-requests", orgId] });
      qc.invalidateQueries({ queryKey: ["cases"] });
    },
  });

  const reject = useMutation({
    mutationFn: (id) => rejectDeletionRequest(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["deletion-requests", orgId] }),
  });

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Trash2 size={16} className="text-gray-500" />
          <span className="font-semibold text-gray-900 text-sm">Pending Deletion Requests</span>
          {requests.length > 0 && (
            <span className="ml-auto text-xs font-semibold text-white bg-red-500 rounded-full px-2 py-0.5">
              {requests.length}
            </span>
          )}
        </div>
      </CardHeader>
      <CardBody>
        {isLoading ? (
          <div className="flex justify-center py-4"><Spinner /></div>
        ) : requests.length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-4">No pending deletion requests.</p>
        ) : (
          <div className="space-y-3">
            {requests.map(r => (
              <div key={r.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium uppercase tracking-wide text-gray-500 bg-gray-200 rounded px-1.5 py-0.5">
                      {r.resource_type}
                    </span>
                    <span className="text-sm font-medium text-gray-800">{r.resource_name || r.resource_id}</span>
                  </div>
                  <p className="text-xs text-gray-400 mt-0.5">Requested {formatDistanceToNow(r.created_at)}</p>
                </div>
                <div className="flex items-center gap-1">
                  <button
                    className="p-1.5 text-gray-400 hover:text-green-600 rounded"
                    title="Approve deletion"
                    onClick={() => { if (confirm("Approve and permanently delete this resource?")) approve.mutate(r.id); }}
                  >
                    <Check size={16} />
                  </button>
                  <button
                    className="p-1.5 text-gray-400 hover:text-red-500 rounded"
                    title="Reject request"
                    onClick={() => reject.mutate(r.id)}
                  >
                    <X size={16} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardBody>
    </Card>
  );
}
