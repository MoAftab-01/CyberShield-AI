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
    <div className="flex items-center justify-between rounded-lg border p-4">
      <span>{label}</span>

      <span
        className={`font-bold ${
          ok
            ? "text-green-600"
            : "text-red-600"
        }`}
      >
        {ok ? "✓" : "✗"}
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
    <div className="rounded-2xl border bg-white p-6 shadow-sm">
      <h2 className="mb-5 text-xl font-bold">
        Character Checklist
      </h2>

      <div className="grid gap-4 md:grid-cols-2">
        <Item
          label="Uppercase"
          ok={uppercase}
        />

        <Item
          label="Lowercase"
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