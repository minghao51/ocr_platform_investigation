import { useEffect, useState } from 'react';
import { isAuthenticated } from '@/lib/api';
import LoginPanel from '@/components/LoginPanel';

interface LoginPageProps {
  onLoginSuccess: () => void;
}

export default function LoginPage({ onLoginSuccess }: LoginPageProps) {
  const [shouldRedirect, setShouldRedirect] = useState(false);

  // If already authenticated, redirect
  useEffect(() => {
    if (isAuthenticated()) {
      setShouldRedirect(true);
      onLoginSuccess();
    }
  }, [onLoginSuccess]);

  if (shouldRedirect) {
    return null;
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-4">
        <div className="text-center">
          <h1 className="text-3xl font-extrabold text-gray-900">OCR Platform</h1>
          <p className="mt-2 text-sm text-gray-600">Sign in to your account</p>
        </div>
        <LoginPanel
          onLoginSuccess={onLoginSuccess}
          title="Sign in"
          subtitle="Use your account to upload documents and run OCR."
        />
        <div className="mt-4 text-center">
          <p className="text-xs text-gray-500">
            To create an admin user, run: <code>uv run python -m backend.cli create-admin &lt;username&gt; &lt;password&gt;</code>
          </p>
        </div>
      </div>
    </div>
  );
}
