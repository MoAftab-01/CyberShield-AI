export default function TypingIndicator() {

    return (

        <div className="flex items-center gap-2">

            <div className="w-2 h-2 rounded-full bg-slate-400 animate-bounce"/>

            <div className="w-2 h-2 rounded-full bg-slate-400 animate-bounce [animation-delay:0.2s]"/>

            <div className="w-2 h-2 rounded-full bg-slate-400 animate-bounce [animation-delay:0.4s]"/>

            <span className="text-sm text-slate-500">

                CyberShield AI is thinking...

            </span>

        </div>

    );

}