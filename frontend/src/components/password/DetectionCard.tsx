interface Props {
  title: string;
  detected: boolean;
  values: string[];
}

export default function DetectionCard({
  title,
  detected,
  values,
}: Props) {
  return (
    <div className="rounded-2xl border bg-white p-6 shadow-sm">
      <h2 className="mb-4 text-xl font-bold">
        {title}
      </h2>

      {!detected ? (
        <p className="text-green-600">
          None detected
        </p>
      ) : (
        <ul className="list-disc pl-6">
          {values.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      )}
    </div>
  );
}