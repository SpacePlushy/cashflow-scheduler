"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Schedule, Bill } from "@/lib/types";
import { cn } from "@/lib/utils";

interface ScheduleCalendarProps {
  schedule: Schedule;
  bills: Bill[];
}

export function ScheduleCalendar({ schedule, bills }: ScheduleCalendarProps) {
  const getBillsForDay = (day: number): Bill[] => {
    return bills.filter((bill) => bill.day === day);
  };

  const getBalanceColor = (closing: string): string => {
    const amount = parseFloat(closing);
    if (amount < 0) return "text-red-500";
    if (amount < 100) return "text-orange-500";
    if (amount < 500) return "text-yellow-500";
    return "text-green-500";
  };

  return (
    <Card className="col-span-4">
      <CardHeader>
        <CardTitle>30-Day Schedule</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-5 md:grid-cols-7 lg:grid-cols-10 gap-2">
          {schedule.ledger.map((row) => {
            const dayBills = getBillsForDay(row.day);
            const isWorkDay = row.action === "Spark";
            const hasDeposit = parseFloat(row.deposits) > 0;
            // Show tooltip below for days 1-10, above for days 11-30
            const tooltipBelow = row.day <= 10;

            return (
              <div
                key={row.day}
                className={cn(
                  "group relative rounded-lg border p-2 transition-all hover:shadow-lg hover:scale-105 hover:z-[9999] cursor-pointer",
                  isWorkDay
                    ? "bg-blue-500/10 border-blue-500/50"
                    : "bg-muted/50 border-muted"
                )}
              >
                {/* Day Number */}
                <div className="text-xs font-bold mb-1 flex items-center justify-between">
                  <span>Day {row.day}</span>
                  {isWorkDay && (
                    <Badge variant="outline" className="h-4 px-1 text-[10px]">
                      Work
                    </Badge>
                  )}
                </div>

                {/* Action Badge */}
                <div className="mb-1">
                  <Badge
                    variant={isWorkDay ? "default" : "secondary"}
                    className="text-[10px] h-5"
                  >
                    {row.action}
                  </Badge>
                </div>

                {/* Balance */}
                <div className="text-xs">
                  <div className={cn("font-semibold", getBalanceColor(row.closing))}>
                    ${row.closing}
                  </div>
                </div>

                {/* Deposit Indicator */}
                {hasDeposit && (
                  <div className="mt-1">
                    <Badge variant="outline" className="text-[9px] h-4 bg-green-500/20">
                      +${row.deposits}
                    </Badge>
                  </div>
                )}

                {/* Hover Tooltip */}
                <div className={cn(
                  "absolute left-1/2 transform -translate-x-1/2 hidden group-hover:block w-56 pointer-events-none",
                  tooltipBelow ? "top-full mt-2" : "bottom-full mb-2"
                )}>
                  <div className="bg-popover/95 backdrop-blur-sm border-2 rounded-lg p-4 shadow-2xl text-xs">
                    <div className="font-bold mb-3 text-sm border-b pb-2">Day {row.day} Details</div>
                    <div className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-muted-foreground">Opening:</span>
                        <span className="font-semibold">${row.opening}</span>
                      </div>
                      {hasDeposit && (
                        <div className="flex justify-between items-center text-green-600 dark:text-green-400">
                          <span>Deposit:</span>
                          <span className="font-semibold">+${row.deposits}</span>
                        </div>
                      )}
                      <div className="flex justify-between items-center">
                        <span className="text-muted-foreground">Action:</span>
                        <span className="font-semibold">{row.action} (${row.net})</span>
                      </div>
                      {dayBills.length > 0 && (
                        <div className="pt-2 border-t mt-2">
                          <div className="text-muted-foreground mb-2 font-semibold">Bills:</div>
                          <div className="space-y-1">
                            {dayBills.map((bill, i) => (
                              <div key={i} className="flex justify-between items-center text-red-600 dark:text-red-400">
                                <span className="truncate mr-2 flex-1">{bill.name}:</span>
                                <span className="font-semibold whitespace-nowrap">-${bill.amount}</span>
                              </div>
                            ))}
                          </div>
                          <div className="flex justify-between items-center font-semibold text-red-600 dark:text-red-400 border-t pt-2 mt-2">
                            <span>Total:</span>
                            <span>-${row.bills}</span>
                          </div>
                        </div>
                      )}
                      <div className="flex justify-between items-center font-bold border-t pt-2 mt-2">
                        <span>Closing:</span>
                        <span className={getBalanceColor(row.closing)}>
                          ${row.closing}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
