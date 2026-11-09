import { useState } from 'react';

interface EscalationBannerProps {
  ticketId: string;
}

export function EscalationBanner({ ticketId }: EscalationBannerProps) {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) return null;

  return (
    <div className="mt-3 flex items-start gap-2 rounded-lg bg-amber-50 border border-amber-200 px-4 py-3">
      {/* Icon */}
      <span className="flex-shrink-0 text-amber-500 text-base mt-0.5">⚠️</span>

      {/* Text */}
      <p className="flex-1 text-sm text-amber-800 leading-relaxed">
        Your case has been escalated to our support team.{' '}
        <span className="font-semibold">Ticket #{ticketId}</span> has been created.
        A support specialist will reach out to you shortly.
      </p>

      {/* Dismiss button */}
      <button
        onClick={() => setDismissed(true)}
        className="flex-shrink-0 text-amber-500 hover:text-amber-700 transition-colors text-lg leading-none"
        aria-label="Dismiss escalation notice"
      >
        ×
      </button>
    </div>
  );
}
