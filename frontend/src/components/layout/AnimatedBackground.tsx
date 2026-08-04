export default function AnimatedBackground() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">

      {/* ================================= */}
      {/* Premium Grid */}
      {/* ================================= */}

      <div
        className="
        absolute
        inset-0

        opacity-[0.025]

        bg-[linear-gradient(rgba(255,255,255,0.06)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.06)_1px,transparent_1px)]

        bg-[size:70px_70px]
        "
      />

      {/* Secondary Grid */}

      <div
        className="
        absolute

        inset-0

        opacity-[0.015]

        bg-[linear-gradient(45deg,rgba(255,255,255,0.05)_1px,transparent_1px)]

        bg-[size:120px_120px]
        "
      />

      {/* ================================= */}
      {/* Radial Overlay */}
      {/* ================================= */}

      <div
        className="
        absolute
        inset-0

        bg-[radial-gradient(circle_at_top,rgba(34,211,238,0.10),transparent_60%)]
        "
      />

      {/* ================================= */}
      {/* Main Center Glow */}
      {/* ================================= */}

      <div
        className="
        absolute

        -top-56

        left-1/2

        h-[900px]
        w-[900px]

        -translate-x-1/2

        rounded-full

        bg-cyan-500/15

        blur-[200px]

        animate-pulse
        "
      />

      {/* ================================= */}
      {/* Right Glow */}
      {/* ================================= */}

      <div
        className="
        absolute

        top-32

        -right-44

        h-[560px]
        w-[560px]

        rounded-full

        bg-sky-500/12

        blur-[190px]

        animate-floatSlow
        "
      />

      {/* ================================= */}
      {/* Bottom Left Glow */}
      {/* ================================= */}

      <div
        className="
        absolute

        -bottom-56

        -left-40

        h-[650px]
        w-[650px]

        rounded-full

        bg-cyan-400/12

        blur-[200px]

        animate-floatMedium
        "
      />

      {/* ================================= */}
      {/* Purple Accent */}
      {/* ================================= */}

      <div
        className="
        absolute

        top-1/3

        left-1/4

        h-[380px]
        w-[380px]

        rounded-full

        bg-violet-500/15

        blur-[170px]

        animate-floatSlow
        "
      />

      {/* ================================= */}
      {/* Blue Accent */}
      {/* ================================= */}

      <div
        className="
        absolute

        bottom-12

        right-8

        h-[420px]
        w-[420px]

        rounded-full

        bg-blue-500/12

        blur-[180px]

        animate-floatMedium
        "
      />

      {/* ================================= */}
      {/* Floating Particles */}
      {/* ================================= */}

      {[
        {
          pos: "top-24 left-20",
          size: "h-2 w-2",
          color: "bg-cyan-300",
          opacity: "opacity-80",
          animation: "animate-floatSlow",
        },
        {
          pos: "top-40 right-20",
          size: "h-3 w-3",
          color: "bg-sky-300",
          opacity: "opacity-70",
          animation: "animate-floatMedium",
        },
        {
          pos: "top-1/3 left-1/2",
          size: "h-2 w-2",
          color: "bg-cyan-200",
          opacity: "opacity-60",
          animation: "animate-floatSlow",
        },
        {
          pos: "top-1/2 right-1/4",
          size: "h-4 w-4",
          color: "bg-cyan-300",
          opacity: "opacity-80",
          animation: "animate-floatFast",
        },
        {
          pos: "bottom-24 left-1/4",
          size: "h-2 w-2",
          color: "bg-blue-300",
          opacity: "opacity-70",
          animation: "animate-floatMedium",
        },
        {
          pos: "bottom-16 right-1/3",
          size: "h-3 w-3",
          color: "bg-cyan-300",
          opacity: "opacity-70",
          animation: "animate-floatSlow",
        },
        {
          pos: "top-16 right-1/3",
          size: "h-2 w-2",
          color: "bg-cyan-200",
          opacity: "opacity-60",
          animation: "animate-floatMedium",
        },
        {
          pos: "bottom-44 left-2/3",
          size: "h-3 w-3",
          color: "bg-sky-300",
          opacity: "opacity-70",
          animation: "animate-floatFast",
        },
        {
          pos: "top-2/3 left-12",
          size: "h-2 w-2",
          color: "bg-cyan-300",
          opacity: "opacity-80",
          animation: "animate-floatSlow",
        },
        {
          pos: "bottom-36 right-12",
          size: "h-2 w-2",
          color: "bg-blue-300",
          opacity: "opacity-60",
          animation: "animate-floatMedium",
        },
        {
          pos: "top-72 left-3/4",
          size: "h-3 w-3",
          color: "bg-cyan-200",
          opacity: "opacity-70",
          animation: "animate-floatSlow",
        },
        {
          pos: "top-1/4 right-1/2",
          size: "h-2 w-2",
          color: "bg-cyan-300",
          opacity: "opacity-80",
          animation: "animate-floatFast",
        },
      ].map((particle, index) => (

        <div
          key={index}
          className={`
            absolute
            ${particle.pos}
            ${particle.size}
            rounded-full
            ${particle.color}
            ${particle.opacity}
            shadow-[0_0_18px_rgba(34,211,238,0.7)]
            ${particle.animation}
          `}
        />

      ))}

      {/* ================================= */}
      {/* Center Spotlight */}
      {/* ================================= */}

      <div
        className="
        absolute

        inset-0

        bg-[radial-gradient(circle_at_center,rgba(34,211,238,0.06),transparent_55%)]
        "
      />

      {/* ================================= */}
      {/* Edge Vignette */}
      {/* ================================= */}

      <div
        className="
        absolute

        inset-0

        bg-[radial-gradient(circle_at_center,transparent_45%,rgba(2,6,23,.75)_100%)]
        "
      />

    </div>
  );
}