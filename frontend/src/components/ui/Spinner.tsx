import { Loader2 } from "lucide-react";

export default function Spinner() {
  return (
    <div className="flex justify-center items-center py-8">
      <Loader2 className="animate-spin text-blue-500" size={32} />
    </div>
  );
}