import { Upload } from "lucide-react";

interface Props {
  onUpload: (file: File) => void;
}

export default function UploadButton({
  onUpload,
}: Props) {

  return (

    <label
      className="
        w-12
        h-12
        rounded-xl
        bg-cyan-600
        hover:bg-cyan-700
        text-white
        flex
        items-center
        justify-center
        cursor-pointer
        transition
        shrink-0
      "
      title="Upload document"
    >

      <Upload size={20} />

      <input
        hidden
        type="file"
        accept=".pdf,.doc,.docx,.txt"
        onChange={(event) => {

          const file =
            event.target.files?.[0];

          if (file) {

            onUpload(file);

            event.target.value = "";

          }

        }}
      />

    </label>

  );

}