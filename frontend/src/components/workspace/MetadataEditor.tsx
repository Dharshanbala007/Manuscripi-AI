import { Plus, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { percent } from "../../lib/format";
import type { MetadataIn, MetadataOut } from "../../lib/types";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { MorphButton } from "../ui/MorphButton";
import { Card, CardBody, CardHeader } from "../ui/Card";
import { TextArea, TextField } from "../ui/Field";

interface Draft {
  title: string;
  authors: string[];
  affiliations: string;
  abstract: string;
  keywords: string;
}

function toDraft(md: MetadataOut): Draft {
  return {
    title: md.title.value,
    authors: md.authors.value.length ? md.authors.value.map((a) => a.name) : [""],
    affiliations: md.affiliations.map((a) => a.text).join("\n"),
    abstract: md.abstract.value,
    keywords: md.keywords.value.join(", "),
  };
}

function toPayload(draft: Draft): MetadataIn {
  return {
    title: draft.title.trim(),
    authors: draft.authors
      .map((name) => name.trim())
      .filter(Boolean)
      .map((name) => ({ name })),
    affiliations: draft.affiliations
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean)
      .map((text) => ({ text })),
    abstract: draft.abstract.trim(),
    keywords: draft.keywords
      .split(",")
      .map((k) => k.trim())
      .filter(Boolean),
  };
}

function ConfidenceTag({ value, edited }: { value: number; edited: boolean }) {
  if (edited) return <Badge tone="success">edited</Badge>;
  if (value === 0) return <Badge tone="warning">not detected</Badge>;
  const tone = value < 0.6 ? "warning" : "muted";
  return <Badge tone={tone}>{percent(value)} confidence</Badge>;
}

export function MetadataEditor({
  metadata,
  onSave,
}: {
  metadata: MetadataOut;
  onSave: (body: MetadataIn) => Promise<void>;
}) {
  const [draft, setDraft] = useState<Draft>(() => toDraft(metadata));
  const pristine = useMemo(() => toDraft(metadata), [metadata]);

  useEffect(() => {
    setDraft(toDraft(metadata));
  }, [metadata]);

  const dirty = JSON.stringify(draft) !== JSON.stringify(pristine);

  async function save() {
    await onSave(toPayload(draft));
  }

  return (
    <Card>
      <CardHeader
        title="Metadata"
        description="Review and correct what was detected. Edits are kept as authoritative."
        action={
          <MorphButton
            variant="primary"
            size="sm"
            disabled={!dirty}
            pendingLabel="Saving…"
            successLabel="Saved"
            onAction={save}
          >
            Save changes
          </MorphButton>
        }
      />
      <CardBody className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-zinc-700">Title</span>
            <ConfidenceTag value={metadata.title.confidence} edited={metadata.title.edited_by_user} />
          </div>
          <TextField
            value={draft.title}
            onChange={(e) => setDraft({ ...draft, title: e.target.value })}
            placeholder="Manuscript title"
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-zinc-700">Authors</span>
            <ConfidenceTag
              value={metadata.authors.confidence}
              edited={metadata.authors.edited_by_user}
            />
          </div>
          <div className="flex flex-col gap-2">
            {draft.authors.map((name, i) => (
              <div key={i} className="flex items-center gap-2">
                <TextField
                  className="flex-1"
                  value={name}
                  onChange={(e) => {
                    const authors = [...draft.authors];
                    authors[i] = e.target.value;
                    setDraft({ ...draft, authors });
                  }}
                  placeholder="Author name"
                />
                <Button
                  size="sm"
                  variant="ghost"
                  aria-label="Remove author"
                  onClick={() =>
                    setDraft({
                      ...draft,
                      authors: draft.authors.filter((_, idx) => idx !== i),
                    })
                  }
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </Button>
              </div>
            ))}
            <Button
              size="sm"
              variant="secondary"
              className="self-start"
              onClick={() => setDraft({ ...draft, authors: [...draft.authors, ""] })}
            >
              <Plus className="h-3.5 w-3.5" /> Add author
            </Button>
          </div>
        </div>

        <TextArea
          label="Affiliations (one per line)"
          value={draft.affiliations}
          onChange={(e) => setDraft({ ...draft, affiliations: e.target.value })}
          rows={2}
        />

        <div className="flex flex-col gap-1.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-zinc-700">Abstract</span>
            <ConfidenceTag
              value={metadata.abstract.confidence}
              edited={metadata.abstract.edited_by_user}
            />
          </div>
          <TextArea
            aria-label="Abstract"
            value={draft.abstract}
            onChange={(e) => setDraft({ ...draft, abstract: e.target.value })}
            rows={4}
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-zinc-700">Keywords (comma-separated)</span>
            <ConfidenceTag
              value={metadata.keywords.confidence}
              edited={metadata.keywords.edited_by_user}
            />
          </div>
          <TextField
            value={draft.keywords}
            onChange={(e) => setDraft({ ...draft, keywords: e.target.value })}
            placeholder="keyword one, keyword two"
          />
        </div>
      </CardBody>
    </Card>
  );
}
