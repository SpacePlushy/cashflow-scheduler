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
    <div className="max-h-[600px] overflow-y-auto rounded-md border">
          <Table>
            <TableHeader className="sticky top-0 bg-background z-10">
              <TableRow>
                <TableHead className="w-12">Day</TableHead>
                <TableHead className="text-right">Opening</TableHead>
                <TableHead className="text-right">Deposits</TableHead>
                <TableHead>Action</TableHead>
                <TableHead className="text-right">Net</TableHead>
                <TableHead className="text-right">Bills</TableHead>
                <TableHead className="text-right">Closing</TableHead>
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
                    <TableCell className="font-medium">{row.day}</TableCell>
                    <TableCell className="text-right text-muted-foreground">
                      ${row.opening}
                    </TableCell>
                    <TableCell className={cn(
                      "text-right",
                      hasDeposit && "text-green-600 font-medium"
                    )}>
                      {hasDeposit ? `+$${row.deposits}` : "-"}
                    </TableCell>
                    <TableCell>
                      <span
                        className={cn(
                          "px-2 py-1 rounded text-xs font-medium",
                          isWorkDay
                            ? "bg-blue-500/20 text-blue-700 dark:text-blue-300"
                            : "bg-muted text-muted-foreground"
                        )}
                      >
                        {row.action}
                      </span>
                    </TableCell>
                    <TableCell className={cn(
                      "text-right",
                      parseFloat(row.net) > 0 ? "text-green-600" : "text-muted-foreground"
                    )}>
                      {parseFloat(row.net) > 0 ? `+$${row.net}` : "$0.00"}
                    </TableCell>
                    <TableCell className={cn(
                      "text-right",
                      hasBills && "text-red-600 font-medium"
                    )}>
                      {hasBills ? `-$${row.bills}` : "-"}
                    </TableCell>
                    <TableCell className={cn(
                      "text-right font-semibold",
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
  );
}
