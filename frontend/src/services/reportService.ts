import api from "./api";
import {
  PasswordReportResponse,
  URLReportResponse,
} from "../types/report";

export async function getPasswordReports(
  page = 1,
  pageSize = 10
): Promise<PasswordReportResponse> {
  const response = await api.get(
    `/reports/passwords?page=${page}&page_size=${pageSize}`
  );

  return response.data;
}

export async function getURLReports(
  page = 1,
  pageSize = 10
): Promise<URLReportResponse> {
  const response = await api.get(
    `/reports/urls?page=${page}&page_size=${pageSize}`
  );

  return response.data;
}