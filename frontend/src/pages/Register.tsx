import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";

import {
  register,
} from "../services/authService";

import Card from "../components/ui/Card";
import Input from "../components/ui/Input";
import Button from "../components/ui/Button";

export default function Register() {
  const navigate = useNavigate();

  const [name, setName] = useState("");

  const [email, setEmail] = useState("");

  const [password, setPassword] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  async function handleRegister(
    e: React.FormEvent
  ) {
    e.preventDefault();

    setLoading(true);

    setError("");

    try {
      await register({
        name,
        email,
        password,
      });

      navigate("/login");
    } catch (err: any) {
      setError(
        err.response?.data?.detail ??
          "Registration failed."
      );
    }

    setLoading(false);
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-100 p-6">
      <Card>
        <h1 className="mb-8 text-center text-3xl font-bold">
          Create Account
        </h1>

        <form
          onSubmit={handleRegister}
          className="space-y-5"
        >
          <Input
            label="Name"
            value={name}
            onChange={(e) =>
              setName(e.target.value)
            }
            required
          />

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
            <div className="rounded bg-red-100 p-3 text-red-700">
              {error}
            </div>
          )}

          <Button
            type="submit"
            loading={loading}
          >
            Register
          </Button>

          <p className="text-center text-sm">
            Already have an account?{" "}
            <Link
              to="/login"
              className="font-semibold text-blue-600 hover:underline"
            >
              Login
            </Link>
          </p>
        </form>
      </Card>
    </div>
  );
}