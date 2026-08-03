import ChatInput from "./ChatInput";
import UploadButton from "../upload/UploadButton";

import { UploadedDocument } from "@/services/uploadService";

interface Props {
  loading: boolean;
  uploadedFiles: UploadedDocument[];
  onSend: (message: string) => void;
  onUpload: (file: File) => void;
  onDeleteDocument: (filename: string) => void;
}

export default function ChatFooter({
  loading,
  uploadedFiles,
  onSend,
  onUpload,
  onDeleteDocument,
}: Props) {

  return (

    <footer className="bg-white border-t p-5 flex-shrink-0">

      <div className="max-w-5xl mx-auto">

        {uploadedFiles.length > 0 && (

          <div className="flex flex-wrap gap-2 mb-3">

            {uploadedFiles.map((file) => (

              <div
                key={file.filename}
                className="
                  flex
                  items-center
                  gap-2
                  bg-slate-100
                  border
                  rounded-full
                  px-3
                  py-1
                  text-sm
                "
              >

                📄

                <span className="max-w-[220px] truncate">
                  {file.filename}
                </span>

                <button
                  onClick={() =>
                    onDeleteDocument(file.filename)
                  }
                  className="
                    text-red-500
                    hover:text-red-700
                  "
                >
                  ✕

                </button>

              </div>

            ))}

          </div>

        )}

        <div className="flex items-center gap-3">

          <UploadButton
            onUpload={onUpload}
          />

          <div className="flex-1">

            <ChatInput
              loading={loading}
              onSend={onSend}
            />

          </div>

        </div>

      </div>

    </footer>

  );

}