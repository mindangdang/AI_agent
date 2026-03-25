import * as Tabs from '@radix-ui/react-tabs';
import type React from 'react';

import { cn } from '../lib/utils';

type NavItemProps = {
  icon: React.ReactNode;
  label: string;
  value: string;
};

export function NavItem({ icon, label, value }: NavItemProps) {
  return (
    <Tabs.Trigger
      value={value}
      className={cn(
        "flex items-center gap-4 p-4 w-full rounded-2xl transition-all duration-200 text-left",
        "data-[state=active]:bg-black data-[state=active]:text-white data-[state=active]:shadow-lg",
        "text-gray-400 hover:bg-gray-50 hover:text-black"
      )}
    >
      <div className="shrink-0">
        {icon}
      </div>
      <span className="hidden md:block text-sm font-black tracking-widest uppercase">{label}</span>
    </Tabs.Trigger>
  );
}
