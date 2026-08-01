import { FileText } from "lucide-react";

import { Source } from "@/types/copilot";

interface Props {

    source: Source;

}

export default function SourceCard({

    source,

}: Props) {

    return (

        <div className="rounded-lg border border-slate-200 p-3">

            <div className="flex items-center gap-2">

                <FileText size={18}/>

                <span className="font-semibold">

                    {source.filename}

                </span>

            </div>

            <p className="text-sm text-slate-500 mt-2">

                Folder: {source.folder}

            </p>

            <p className="text-sm text-slate-500">

                Page {source.page}

            </p>

        </div>

    );

}