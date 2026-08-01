import api from "./api";

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface User {
  id: number;
  name: string;
  email: string;
}

export async function login(data: LoginRequest) {
  const response = await api.post<TokenResponse>(
    "/users/login",
    data
  );

  return response.data;
}

export async function register(
  data: RegisterRequest
) {
  const response = await api.post<User>(
    "/users/register",
    data
  );

  return response.data;
}

export async function getCurrentUser() {
  const response = await api.get<User>(
    "/users/me"
  );

  return response.data;
}