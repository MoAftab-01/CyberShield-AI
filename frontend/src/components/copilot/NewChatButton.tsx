import { Plus } from "lucide-react";

interface Props {

  onClick: () => void;

}

export default function NewChatButton({

  onClick,

}: Props) {

  return (

    <button

      onClick={onClick}

      className="
        w-full
        flex
        items-center
        justify-center
        gap-2

        rounded-xl

        bg-cyan-600

        hover:bg-cyan-500

        text-white

        font-semibold

        py-3

        transition

        shadow-lg
      "

    >

      <Plus size={20} />

      New Chat

    </button>

  );

}