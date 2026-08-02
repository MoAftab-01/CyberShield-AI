import { Search, X } from "lucide-react";

interface Props {

  value: string;

  onChange: (value: string) => void;

}

export default function SearchConversation({

  value,

  onChange,

}: Props) {

  return (

    <div className="relative">

      <Search
        size={18}
        className="
          absolute
          left-4
          top-1/2
          -translate-y-1/2
          text-slate-400
        "
      />

      <input

        value={value}

        onChange={(e) => onChange(e.target.value)}

        placeholder="Search conversations..."

        className="
          w-full
          rounded-xl
          border
          border-slate-700
          bg-slate-900
          py-3
          pl-11
          pr-11
          text-white
          placeholder:text-slate-500
          outline-none
          focus:border-cyan-500
          transition
        "

      />

      {

        value && (

          <button

            onClick={() => onChange("")}

            className="
              absolute
              right-3
              top-1/2
              -translate-y-1/2
              text-slate-400
              hover:text-white
              transition
            "

          >

            <X size={18} />

          </button>

        )

      }

    </div>

  );

}