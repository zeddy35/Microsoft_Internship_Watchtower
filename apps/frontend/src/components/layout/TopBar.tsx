import { Avatar } from "@/components/ui/Avatar";
import { Icon } from "@/components/ui/Icon";

type TopBarProps = {
  userName?: string;
};

export function TopBar({ userName = "Jordan Ellis" }: TopBarProps) {
  return (
    <header className="sticky top-0 z-40 flex h-16 items-center justify-between border-b border-outline-variant bg-surface-container-lowest px-margin_page">
      <div className="flex items-center gap-4">
        <div className="flex w-64 items-center rounded-lg border border-outline-variant bg-surface-container px-3 py-1.5">
          <Icon name="search" className="mr-2 text-outline" size={20} />
          <input
            type="text"
            placeholder="Search teams or repos..."
            className="w-full border-none bg-transparent p-0 text-body-sm focus:ring-0"
          />
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <button
            type="button"
            className="text-secondary hover:text-primary"
            aria-label="Notifications"
          >
            <Icon name="notifications" />
          </button>
          <button
            type="button"
            className="text-secondary hover:text-primary"
            aria-label="History"
          >
            <Icon name="history" />
          </button>
        </div>
        <button
          type="button"
          className="flex items-center gap-2 rounded-lg bg-primary px-4 py-1.5 text-body-sm font-semibold text-white transition-all hover:opacity-90"
        >
          <Icon name="download" size={18} />
          Export digest
        </button>
        <Avatar name={userName} size={32} className="border border-outline-variant" />
      </div>
    </header>
  );
}
