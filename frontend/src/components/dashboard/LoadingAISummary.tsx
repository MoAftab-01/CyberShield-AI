export default function LoadingAISummary() {
  return (
    <div
      className="
      animate-pulse

      overflow-hidden

      rounded-[28px]

      border

      border-cyan-400/20

      bg-slate-900/55

      p-6

      backdrop-blur-2xl

      shadow-[0_0_40px_rgba(34,211,238,.08)]
      "
    >

      <div className="mb-6 flex items-center gap-4">

        <div
          className="
          h-14
          w-14

          rounded-2xl

          bg-slate-800
          "
        />

        <div className="space-y-2">

          <div className="h-5 w-56 rounded bg-slate-800"/>

          <div className="h-4 w-44 rounded bg-slate-800"/>

        </div>

      </div>

      <div className="space-y-3">

        <div className="h-4 rounded bg-slate-800"/>

        <div className="h-4 w-11/12 rounded bg-slate-800"/>

        <div className="h-4 w-10/12 rounded bg-slate-800"/>

        <div className="h-4 w-9/12 rounded bg-slate-800"/>

      </div>

    </div>
  );
}