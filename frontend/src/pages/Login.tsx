import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";

import { useAuth } from "../contexts/AuthContext";

import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import Input from "../components/ui/Input";

export default function Login() {
  const navigate = useNavigate();

  const { login } = useAuth();

  const [email, setEmail] = useState("");

  const [password, setPassword] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  async function handleLogin(
    e: React.FormEvent
  ) {
    e.preventDefault();

    setError("");

    setLoading(true);

    try {
      await login(email, password);

      navigate("/dashboard");
    } catch (err: any) {
      setError(
        err.response?.data?.detail ??
          "Login failed."
      );
    }

    setLoading(false);
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-100 p-6">
      <Card>
        <h1 className="mb-8 text-center text-3xl font-bold">
          CyberShield AI
        </h1>

        <form
          onSubmit={handleLogin}
          className="space-y-5"
        >
          <Input
            label="Email"
            type="email"
            value={email}
            onChange={(e) =>
              setEmail(e.target.value)
            }
            required
          />

          <Input
            label="Password"
            type="password"
            value={password}
            onChange={(e) =>
              setPassword(e.target.value)
            }
            required
          />

          {error && (
            <div className="rounded bg-red-100 p-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <Button
            type="submit"
            loading={loading}
          >
            Login
          </Button>

          <p className="text-center text-sm">
            Don't have an account?{" "}
            <Link
              to="/register"
              className="font-semibold text-blue-600 hover:underline"
            >
              Register
            </Link>
          </p>
        </form>
      </Card>
    </div>
  );
}