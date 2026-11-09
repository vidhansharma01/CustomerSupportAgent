import { ChatWindow } from './components/ChatWindow';

function App() {
  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl h-[85vh] flex flex-col">
        <ChatWindow />
      </div>
    </div>
  );
}

export default App;
