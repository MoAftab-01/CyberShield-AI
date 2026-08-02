import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";

export function generateExecutiveReport(
  summary: string,
  passwordCount: number,
  urlCount: number,
) {
  const pdf = new jsPDF();

  pdf.setFontSize(22);
  pdf.text(
    "CyberShield AI",
    20,
    20,
  );

  pdf.setFontSize(16);
  pdf.text(
    "Executive Security Report",
    20,
    32,
  );

  pdf.setFontSize(12);

  pdf.text(
    `Generated: ${new Date().toLocaleString()}`,
    20,
    42,
  );

  pdf.text(
    "AI Executive Summary",
    20,
    58,
  );

  pdf.setFontSize(11);

  pdf.text(
    summary,
    20,
    66,
    {
      maxWidth: 170,
    },
  );

  autoTable(pdf, {
    startY: 110,

    head: [["Metric", "Value"]],

    body: [

      [
        "Password Reports",
        passwordCount.toString(),
      ],

      [
        "URL Reports",
        urlCount.toString(),
      ],

    ],

  });

  pdf.save(
    "CyberShield_AI_Report.pdf",
  );
}