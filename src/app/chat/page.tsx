"use client";
import Link from "next/link";
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { sendChat } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";

type Msg = { role: "user" | "ai"; text: string; investigationId?: string | null };

export default function ChatPage() {
  const [input, setInput] = useState("");
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const mutation = useMutation({
    mutationFn: sendChat,
    onSuccess: r => setMsgs(m => [...m, { role: "ai", text: r.text, investigationId: r.investigation_id }]),
  });
  const send = () => {
    if (!input.trim()) return;
    setMsgs(m => [...m, { role: "user", text: input }]);
    mutation.mutate(input);
    setInput("");
  };
  return (
    <div className="flex max-w-2xl flex-1 flex-col gap-4">
      <h1 className="text-xl font-semibold">AI Chat</h1>
      <div className="flex-1 space-y-3">
        {msgs.length === 0 && <p className="text-sm text-muted-foreground">Try: &quot;investigate claim CLM-2025-000185&quot; or &quot;what is our loss ratio?&quot;</p>}
        {msgs.map((m, i) => (
          <Card key={i} className={m.role === "user" ? "ml-auto max-w-md" : "mr-auto max-w-lg"}>
            <CardContent className="p-3 text-sm">
              {m.text}
              {m.investigationId && (
                <Link href={`/investigations/${m.investigationId}`} className="mt-2 block text-xs text-blue-400 hover:underline">
                  → open investigation {m.investigationId}
                </Link>
              )}
            </CardContent>
          </Card>
        ))}
        {mutation.isPending && <p className="text-xs text-muted-foreground">agents thinking…</p>}
      </div>
      <div className="flex gap-2">
        <Input value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === "Enter" && send()} placeholder="Ask anything…" />
        <Button onClick={send} disabled={mutation.isPending}>Send</Button>
      </div>
    </div>
  );
}