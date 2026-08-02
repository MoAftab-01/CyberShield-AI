import api from "./api";

export interface UploadedDocument {
  filename: string;
  size: number;
}

export async function uploadDocument(file: File) {
  const formData = new FormData();

  formData.append("file", file);

  const response = await api.post(
    "/uploads/",
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );

  return response.data;
}

export async function getUploadedDocuments() {
  const response = await api.get("/uploads/");

  return response.data;
}

export async function deleteUploadedDocument(
  filename: string
) {
  await api.delete(`/uploads/${filename}`);
}