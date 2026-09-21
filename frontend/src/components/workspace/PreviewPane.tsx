import { RefreshCw } from "lucide-react";
import { useState } from "react";

import { api } from "../../lib/api";
import { Button } from "../ui/Button";
import { Card, CardBody, CardHeader } from "../ui/Card";
import { EmptyState } from "../ui/Feedback";

export function PreviewPane({ docId, ready }: { docId: string; ready: boolean }) {
  const [nonce, setNonce] = useState(0);

  return (
    <Card>
      <CardHeader
        title="Preview"
        description="The generated document — a rendered PDF when LibreOffice is available, otherwise a structural view."
        action={
          ready ? (
            <Button size="sm" variant="secondary" onClick={() => setNonce((n) => n + 1)}>
              <RefreshCw className="h-3.5 w-3.5" /> Refresh
            </Button>
          ) : null
        }
      />
      <CardBody>
        {ready ? (
          <iframe
            key={nonce}
            title="Document preview"
            src={`${api.previewUrl(docId)}?v=${nonce}`}
            className="h-[70vh] w-full rounded-lg border border-zinc-200 dark:border-white/10 bg-white"
          />
        ) : (
          <EmptyState title="Apply a format to preview the document" />
        )}
      </CardBody>
    </Card>
  );
}
