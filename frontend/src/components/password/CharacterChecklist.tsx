interface Props {
  uppercase: boolean;
  lowercase: boolean;
  number: boolean;
  special: boolean;
}

function Item({
  label,
  ok,
}: {
  label: string;
  ok: boolean;
}) {
  return (
    <div
      className="
      flex

      items-center

      justify-between

      rounded-2xl

      border

      border-cyan-500/10

      bg-slate-900/40

      px-5

      py-4

      backdrop-blur-xl

      transition-all

      duration-300

      hover:border-cyan-400/25
      "
    >

      <span
        className="
        font-medium

        text-slate-200
        "
      >
        {label}
      </span>

      <span
        className={`
        rounded-full

        px-3

        py-1

        text-xs

        font-semibold

        ${
          ok
            ? `
            border
            border-emerald-500/20

            bg-emerald-500/10

            text-emerald-300
            `
            : `
            border
            border-red-500/20

            bg-red-500/10

            text-red-300
            `
        }
        `}
      >
        {ok ? "✓ Present" : "✕ Missing"}
      </span>

    </div>
  );
}

export default function CharacterChecklist({
  uppercase,
  lowercase,
  number,
  special,
}: Props) {
  return (
    <div
      className="
      rounded-3xl

      border

      border-cyan-500/10

      bg-slate-900/40

      p-6

      backdrop-blur-2xl

      shadow-[0_0_35px_rgba(34,211,238,.08)]
      "
    >

      <h2
        className="
        mb-6

        text-xl

        font-bold

        text-white
        "
      >
        Character Checklist
      </h2>

      <div className="grid gap-4 md:grid-cols-2">

        <Item
          label="Uppercase Letters"
          ok={uppercase}
        />

        <Item
          label="Lowercase Letters"
          ok={lowercase}
        />

        <Item
          label="Numbers"
          ok={number}
        />

        <Item
          label="Special Characters"
          ok={special}
        />

      </div>

    </div>
  );
}