import { Trash2, FileText } from "lucide-react";

import { UploadedDocument } from "@/services/uploadService";

interface Props {
  files: UploadedDocument[];
  onDelete: (filename: string) => void;
}

export default function UploadedFiles({
  files,
  onDelete,
}: Props) {
  if (files.length === 0) return null;

  return (
    <div className="mb-5 rounded-xl border bg-white p-4">
      <h3 className="font-semibold mb-3">
        Uploaded Documents
      </h3>

      <div className="space-y-2">
        {files.map((file) => (
          <div
            key={file.filename}
            className="flex items-center justify-between rounded-lg border p-3"
          >
            <div className="flex items-center gap-3">
              <FileText
                size={18}
                className="text-cyan-600"
              />

              <span className="text-sm">
                {file.filename}
              </span>
            </div>

            <button
              onClick={() =>
                onDelete(file.filename)
              }
            >
              <Trash2
                size={18}
                className="text-red-500"
              />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}