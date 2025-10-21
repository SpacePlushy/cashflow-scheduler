"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Schedule, Bill } from "@/lib/types";
import { cn } from "@/lib/utils";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";

interface ScheduleCalendarProps {
  schedule: Schedule;
  bills: Bill[];
}

interface DayDetails {
  day: number;
  opening: string;
  deposits: string;
  action: string;
  net: string;
  bills: Bill[];
  totalBills: string;
  closing: string;
  isWorkDay: boolean;
}

export function ScheduleCalendar({ schedule, bills }: ScheduleCalendarProps) {
  const [selectedDay, setSelectedDay] = useState<DayDetails | null>(null);
  const [isSheetOpen, setIsSheetOpen] = useState(false);

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

  const handleDayClick = (row: typeof schedule.ledger[0]) => {
    const dayBills = getBillsForDay(row.day);
    const isWorkDay = row.action === "Spark";

    setSelectedDay({
      day: row.day,
      opening: row.opening,
      deposits: row.deposits,
      action: row.action,
      net: row.net,
      bills: dayBills,
      totalBills: row.bills,
      closing: row.closing,
      isWorkDay,
    });
    setIsSheetOpen(true);
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.03
      }
    }
  };

  const cellVariants = {
    hidden: { opacity: 0, scale: 0.8 },
    visible: {
      opacity: 1,
      scale: 1,
      transition: {
        type: "spring",
        stiffness: 300,
        damping: 25
      }
    }
  };

  return (
    <>
    <Card className="col-span-4">
      <CardHeader className="px-3 sm:px-6 py-3 sm:py-6">
        <CardTitle className="text-base sm:text-lg">30-Day Schedule</CardTitle>
        <p className="text-xs sm:text-sm text-muted-foreground mt-1">
          Tap any day to see details
        </p>
      </CardHeader>
      <CardContent className="px-2 sm:px-6 pb-3 sm:pb-6">
        <motion.div
          className="grid grid-cols-3 sm:grid-cols-5 md:grid-cols-7 lg:grid-cols-10 gap-1.5 sm:gap-2"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          {schedule.ledger.map((row) => {
            const dayBills = getBillsForDay(row.day);
            const isWorkDay = row.action === "Spark";
            const hasDeposit = parseFloat(row.deposits) > 0;

            return (
              <motion.div
                key={row.day}
                variants={cellVariants}
                onClick={() => handleDayClick(row)}
                className={cn(
                  "group relative rounded-lg border p-2 sm:p-2.5 transition-all active:scale-95 cursor-pointer touch-manipulation",
                  "hover:shadow-lg hover:scale-105 hover:z-10",
                  isWorkDay
                    ? "bg-blue-500/10 border-blue-500/50"
                    : "bg-muted/50 border-muted"
                )}
                whileTap={{ scale: 0.95 }}
              >
                {/* Day Number */}
                <div className="text-xs sm:text-sm font-bold mb-1 sm:mb-1.5">
                  <span className="block sm:inline">Day {row.day}</span>
                </div>

                {/* Action Badge - Hidden on mobile for cleaner look */}
                <div className="mb-1 hidden sm:block">
                  <Badge
                    variant={isWorkDay ? "default" : "secondary"}
                    className="text-[10px] h-5"
                  >
                    {row.action}
                  </Badge>
                </div>

                {/* Work Indicator - Mobile only */}
                {isWorkDay && (
                  <div className="sm:hidden mb-1">
                    <div className="h-1.5 w-1.5 rounded-full bg-blue-500"></div>
                  </div>
                )}

                {/* Balance */}
                <div className="text-xs sm:text-sm">
                  <div className={cn("font-semibold", getBalanceColor(row.closing))}>
                    ${row.closing}
                  </div>
                </div>

                {/* Deposit Indicator */}
                {hasDeposit && (
                  <div className="mt-1 hidden sm:block">
                    <Badge variant="outline" className="text-[9px] h-4 bg-green-500/20">
                      +${row.deposits}
                    </Badge>
                  </div>
                )}
                {hasDeposit && (
                  <div className="sm:hidden mt-0.5">
                    <div className="text-[9px] text-green-600 dark:text-green-400 font-medium">
                      +
                    </div>
                  </div>
                )}

                {/* Hover Tooltip - Desktop only */}
                <div className="hidden md:group-hover:block absolute left-1/2 transform -translate-x-1/2 top-full mt-2 w-56 pointer-events-none z-50">
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
              </motion.div>
            );
          })}
        </motion.div>
      </CardContent>
    </Card>

    {/* Mobile Day Details Sheet */}
    <Sheet open={isSheetOpen} onOpenChange={setIsSheetOpen}>
      <SheetContent side="bottom" className="h-[85vh] overflow-y-auto">
        <SheetHeader className="mb-6">
          <SheetTitle className="text-2xl">
            Day {selectedDay?.day} Details
          </SheetTitle>
          <SheetDescription>
            {selectedDay?.isWorkDay ? "Work day" : "Off day"} • Closing balance: ${selectedDay?.closing}
          </SheetDescription>
        </SheetHeader>

        {selectedDay && (
          <div className="space-y-6">
            {/* Action Badge */}
            <div className="flex items-center gap-2">
              <Badge
                variant={selectedDay.isWorkDay ? "default" : "secondary"}
                className="text-sm px-3 py-1"
              >
                {selectedDay.action}
              </Badge>
              {parseFloat(selectedDay.deposits) > 0 && (
                <Badge variant="outline" className="bg-green-500/20 text-sm px-3 py-1">
                  Deposit Day
                </Badge>
              )}
            </div>

            {/* Financial Flow */}
            <div className="space-y-4">
              <div className="flex justify-between items-center p-4 bg-muted/50 rounded-lg">
                <span className="text-sm text-muted-foreground">Opening Balance</span>
                <span className="text-lg font-bold">${selectedDay.opening}</span>
              </div>

              {parseFloat(selectedDay.deposits) > 0 && (
                <div className="flex justify-between items-center p-4 bg-green-500/10 rounded-lg border border-green-500/30">
                  <span className="text-sm text-green-700 dark:text-green-400">Deposit</span>
                  <span className="text-lg font-bold text-green-700 dark:text-green-400">
                    +${selectedDay.deposits}
                  </span>
                </div>
              )}

              {parseFloat(selectedDay.net) > 0 && (
                <div className="flex justify-between items-center p-4 bg-blue-500/10 rounded-lg border border-blue-500/30">
                  <span className="text-sm text-blue-700 dark:text-blue-400">Work Income</span>
                  <span className="text-lg font-bold text-blue-700 dark:text-blue-400">
                    +${selectedDay.net}
                  </span>
                </div>
              )}

              {selectedDay.bills.length > 0 && (
                <div className="space-y-2">
                  <div className="text-sm font-semibold text-muted-foreground px-4">Bills Due</div>
                  {selectedDay.bills.map((bill, i) => (
                    <div
                      key={i}
                      className="flex justify-between items-center p-4 bg-red-500/10 rounded-lg border border-red-500/30"
                    >
                      <span className="text-sm text-red-700 dark:text-red-400 truncate mr-4">
                        {bill.name}
                      </span>
                      <span className="text-lg font-bold text-red-700 dark:text-red-400 whitespace-nowrap">
                        -${bill.amount}
                      </span>
                    </div>
                  ))}
                  {selectedDay.bills.length > 1 && (
                    <div className="flex justify-between items-center p-3 bg-red-500/20 rounded-lg border-2 border-red-500/50">
                      <span className="text-sm font-semibold text-red-700 dark:text-red-400">
                        Total Bills
                      </span>
                      <span className="text-lg font-bold text-red-700 dark:text-red-400">
                        -${selectedDay.totalBills}
                      </span>
                    </div>
                  )}
                </div>
              )}

              <div className="flex justify-between items-center p-4 bg-primary/10 rounded-lg border-2 border-primary/30">
                <span className="text-base font-semibold">Closing Balance</span>
                <span className={cn("text-2xl font-bold", getBalanceColor(selectedDay.closing))}>
                  ${selectedDay.closing}
                </span>
              </div>
            </div>
          </div>
        )}
      </SheetContent>
    </Sheet>
    </>
  );
}
