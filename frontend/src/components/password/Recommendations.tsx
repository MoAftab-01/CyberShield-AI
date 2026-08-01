interface Props {
  recommendations: string[];
}

export default function Recommendations({
  recommendations,
}: Props) {
  return (
    <div className="rounded-2xl border bg-white p-6 shadow-sm">
      <h2 className="mb-4 text-xl font-bold">
        Recommendations
      </h2>

      <ul className="list-disc space-y-2 pl-6">
        {recommendations.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}