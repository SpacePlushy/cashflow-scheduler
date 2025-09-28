"use client";

import {
  CloudDownload,
  FileJson,
  Layers3,
  LineChart,
} from "lucide-react";

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from "@/components/ui/sidebar";

const NAV_ITEMS = [
  {
    title: "Plan Builder",
    description: "Edit your cashflow scenario.",
    url: "#plan",
    icon: Layers3,
  },
  {
    title: "Plan JSON",
    description: "Inspect or paste raw plan data.",
    url: "#plan-json",
    icon: FileJson,
  },
  {
    title: "Verification",
    description: "Cross-check DP vs CP-SAT.",
    url: "#verification",
    icon: LineChart,
  },
  {
    title: "Exports",
    description: "Download schedules and reports.",
    url: "#exports",
    icon: CloudDownload,
  },
];

export function AppSidebar() {
  return (
    <Sidebar>
      <SidebarHeader className="space-y-2">
        <div className="flex flex-col gap-1">
          <span className="text-xs font-medium uppercase tracking-wide text-sidebar-foreground/60">
            Cashflow Scheduler
          </span>
          <h2 className="text-lg font-semibold leading-tight">Planning Suite</h2>
        </div>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Navigation</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {NAV_ITEMS.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild tooltip={item.description}>
                    <a href={item.url}>
                      <item.icon />
                      <span>{item.title}</span>
                    </a>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter className="text-xs text-sidebar-foreground/60">
        <p>DP optimal over integer cents. Use verification to confirm tie-breaks.</p>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}
