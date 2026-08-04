import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Shield } from "lucide-react";

import { register } from "../services/authService";

import Card from "../components/ui/Card";
import Input from "../components/ui/Input";
import Button from "../components/ui/Button";
import AnimatedBackground from "../components/layout/AnimatedBackground";

export default function Register() {
  const navigate = useNavigate();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

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
    <div
      className="
      relative

      flex

      min-h-screen

      items-center

      justify-center

      overflow-hidden

      bg-[#050C18]

      px-6
      "
    >
      <AnimatedBackground />

      <div className="relative z-10 w-full max-w-md">

        <Card className="p-8">

          <div className="mb-8 text-center">

            <div
              className="
              mx-auto

              mb-5

              flex

              h-16

              w-16

              items-center

              justify-center

              rounded-3xl

              bg-gradient-to-br

              from-cyan-400

              via-cyan-500

              to-blue-600

              shadow-[0_0_35px_rgba(34,211,238,.35)]
              "
            >
              <Shield
                size={30}
                className="text-white"
              />
            </div>

            <h1 className="text-3xl font-bold text-white">
              Create Account
            </h1>

            <p className="mt-2 text-slate-400">
              Join CyberGPT Enterprise
            </p>

          </div>

          <form
            onSubmit={handleRegister}
            className="space-y-5"
          >

            <Input
              label="Full Name"
              value={name}
              onChange={(e) =>
                setName(e.target.value)
              }
              placeholder="Enter your name"
              required
            />

            <Input
              label="Email"
              type="email"
              value={email}
              onChange={(e) =>
                setEmail(e.target.value)
              }
              placeholder="Enter your email"
              required
            />

            <Input
              label="Password"
              type="password"
              value={password}
              onChange={(e) =>
                setPassword(e.target.value)
              }
              placeholder="Create a password"
              required
            />

            {error && (

              <div
                className="
                rounded-2xl

                border

                border-red-500/20

                bg-red-500/10

                p-4

                text-red-300
                "
              >
                {error}
              </div>

            )}

            <Button
              type="submit"
              loading={loading}
              className="
              w-full

              rounded-2xl

              bg-gradient-to-r

              from-cyan-400

              via-cyan-500

              to-blue-600

              text-white

              hover:shadow-[0_0_35px_rgba(34,211,238,.35)]
              "
            >
              Create Account
            </Button>

            <p className="text-center text-sm text-slate-400">

              Already have an account?{" "}

              <Link
                to="/login"
                className="
                font-semibold

                text-cyan-300

                hover:text-cyan-200
                "
              >
                Sign In
              </Link>

            </p>

          </form>

        </Card>

      </div>

    </div>
  );
}