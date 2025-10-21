"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Schedule } from "@/lib/types";
import { cn } from "@/lib/utils";

interface LedgerTableProps {
  schedule: Schedule;
}

export function LedgerTable({ schedule }: LedgerTableProps) {
  const getBalanceColor = (closing: string): string => {
    const amount = parseFloat(closing);
    if (amount < 0) return "text-red-500 font-bold";
    if (amount < 100) return "text-orange-500";
    if (amount < 500) return "text-yellow-600";
    return "text-green-600";
  };

  return (
    <div>
      {/* Mobile hint */}
      <div className="md:hidden text-xs text-muted-foreground mb-2 px-2">
        Scroll horizontally to see all columns →
      </div>

      <div className="max-h-[600px] overflow-auto rounded-md border">
          <Table className="min-w-[600px]">
            <TableHeader className="sticky top-0 bg-background z-10">
              <TableRow>
                <TableHead className="w-12 sticky left-0 bg-background z-20">Day</TableHead>
                <TableHead className="text-right text-xs sm:text-sm">Opening</TableHead>
                <TableHead className="text-right text-xs sm:text-sm">Deposits</TableHead>
                <TableHead className="text-xs sm:text-sm">Action</TableHead>
                <TableHead className="text-right text-xs sm:text-sm">Net</TableHead>
                <TableHead className="text-right text-xs sm:text-sm">Bills</TableHead>
                <TableHead className="text-right text-xs sm:text-sm sticky right-0 bg-background z-20">Closing</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {schedule.ledger.map((row, idx) => {
                const isWorkDay = row.action === "Spark";
                const hasDeposit = parseFloat(row.deposits) > 0;
                const hasBills = parseFloat(row.bills) > 0;

                return (
                  <TableRow
                    key={row.day}
                    className={cn(
                      idx % 2 === 0 ? "bg-muted/30" : "",
                      isWorkDay && "border-l-4 border-l-blue-500"
                    )}
                  >
                    <TableCell className="font-medium sticky left-0 bg-inherit z-10">{row.day}</TableCell>
                    <TableCell className="text-right text-muted-foreground text-xs sm:text-sm whitespace-nowrap">
                      ${row.opening}
                    </TableCell>
                    <TableCell className={cn(
                      "text-right text-xs sm:text-sm whitespace-nowrap",
                      hasDeposit && "text-green-600 font-medium"
                    )}>
                      {hasDeposit ? `+$${row.deposits}` : "-"}
                    </TableCell>
                    <TableCell>
                      <span
                        className={cn(
                          "px-2 py-1 rounded text-[10px] sm:text-xs font-medium whitespace-nowrap",
                          isWorkDay
                            ? "bg-blue-500/20 text-blue-700 dark:text-blue-300"
                            : "bg-muted text-muted-foreground"
                        )}
                      >
                        {row.action}
                      </span>
                    </TableCell>
                    <TableCell className={cn(
                      "text-right text-xs sm:text-sm whitespace-nowrap",
                      parseFloat(row.net) > 0 ? "text-green-600" : "text-muted-foreground"
                    )}>
                      {parseFloat(row.net) > 0 ? `+$${row.net}` : "$0.00"}
                    </TableCell>
                    <TableCell className={cn(
                      "text-right text-xs sm:text-sm whitespace-nowrap",
                      hasBills && "text-red-600 font-medium"
                    )}>
                      {hasBills ? `-$${row.bills}` : "-"}
                    </TableCell>
                    <TableCell className={cn(
                      "text-right font-semibold text-xs sm:text-sm sticky right-0 bg-inherit z-10 whitespace-nowrap",
                      getBalanceColor(row.closing)
                    )}>
                      ${row.closing}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      </div>
  );
}
