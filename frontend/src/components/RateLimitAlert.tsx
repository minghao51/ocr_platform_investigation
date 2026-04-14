interface RateLimitAlertProps {
  message: string;
  limitType?: "daily" | "per_minute";
}

export function RateLimitAlert({ message, limitType }: RateLimitAlertProps) {
  const isDaily = limitType === "daily";

  return (
    <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
      <div className="flex items-start">
        <svg className="w-5 h-5 text-amber-500 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
        </svg>
        <div className="ml-3">
          <h3 className="text-sm font-semibold text-amber-800">
            {isDaily ? "Daily Limit Reached" : "Too Many Requests"}
          </h3>
          <p className="text-sm text-amber-700 mt-1">{message}</p>
          {isDaily && (
            <p className="text-xs text-amber-600 mt-2">
              Your daily limit resets tomorrow. Contact support for increased limits.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
