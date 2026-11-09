export function TypingIndicator() {
  return (
    <div className="flex items-start gap-3 px-4 py-2">
      {/* Bot avatar */}
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center">
        <span className="text-indigo-600 text-sm">🤖</span>
      </div>

      {/* Typing bubble */}
      <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
        <div className="flex items-center gap-1.5">
          <span
            className="w-2 h-2 rounded-full bg-gray-400 animate-bounce"
            style={{ animationDelay: '0ms', animationDuration: '1s' }}
          />
          <span
            className="w-2 h-2 rounded-full bg-gray-400 animate-bounce"
            style={{ animationDelay: '200ms', animationDuration: '1s' }}
          />
          <span
            className="w-2 h-2 rounded-full bg-gray-400 animate-bounce"
            style={{ animationDelay: '400ms', animationDuration: '1s' }}
          />
        </div>
      </div>
    </div>
  );
}
