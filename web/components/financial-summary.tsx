"use client";

import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Schedule } from "@/lib/types";
import { DollarSign, Calendar, TrendingUp, CheckCircle2, XCircle } from "lucide-react";

interface FinancialSummaryProps {
  schedule: Schedule;
}

export function FinancialSummary({ schedule }: FinancialSummaryProps) {
  const workdays = schedule.objective[0];
  const backToBackPairs = schedule.objective[1];
  const finalDiff = schedule.objective[2];

  // Checks are tuples: [name, ok, detail]
  const allChecksPassed = schedule.checks.every((check) => check[1]);

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const cardVariants = {
    hidden: { opacity: 0, y: 20, scale: 0.95 },
    visible: {
      opacity: 1,
      y: 0,
      scale: 1,
      transition: {
        type: "spring",
        stiffness: 200,
        damping: 20
      }
    }
  };

  return (
    <motion.div
      className="grid gap-3 sm:gap-4 grid-cols-2 lg:grid-cols-4"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      <motion.div variants={cardVariants}>
        <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 px-3 sm:px-6 pt-3 sm:pt-6">
          <CardTitle className="text-xs sm:text-sm font-medium">Workdays</CardTitle>
          <Calendar className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent className="px-3 sm:px-6 pb-3 sm:pb-6">
          <div className="text-xl sm:text-2xl font-bold">{workdays}</div>
          <p className="text-[10px] sm:text-xs text-muted-foreground">
            of 30 days
          </p>
        </CardContent>
      </Card>
      </motion.div>

      <motion.div variants={cardVariants}>
        <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 px-3 sm:px-6 pt-3 sm:pt-6">
          <CardTitle className="text-xs sm:text-sm font-medium">Balance</CardTitle>
          <DollarSign className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent className="px-3 sm:px-6 pb-3 sm:pb-6">
          <div className="text-xl sm:text-2xl font-bold">${schedule.final_closing}</div>
          <p className="text-[10px] sm:text-xs text-muted-foreground truncate">
            Diff: ${(finalDiff / 100).toFixed(2)}
          </p>
        </CardContent>
      </Card>
      </motion.div>

      <motion.div variants={cardVariants}>
        <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 px-3 sm:px-6 pt-3 sm:pt-6">
          <CardTitle className="text-xs sm:text-sm font-medium">Quality</CardTitle>
          <TrendingUp className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent className="px-3 sm:px-6 pb-3 sm:pb-6">
          <div className="text-xl sm:text-2xl font-bold">{backToBackPairs}</div>
          <p className="text-[10px] sm:text-xs text-muted-foreground">
            B2B pairs
          </p>
        </CardContent>
      </Card>
      </motion.div>

      <motion.div variants={cardVariants}>
        <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 px-3 sm:px-6 pt-3 sm:pt-6">
          <CardTitle className="text-xs sm:text-sm font-medium">Status</CardTitle>
          {allChecksPassed ? (
            <CheckCircle2 className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-green-500" />
          ) : (
            <XCircle className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-red-500" />
          )}
        </CardHeader>
        <CardContent className="px-3 sm:px-6 pb-3 sm:pb-6">
          <div className="flex items-center gap-2">
            <Badge variant={allChecksPassed ? "default" : "destructive"} className="text-[10px] sm:text-xs">
              {allChecksPassed ? "Passed" : "Failed"}
            </Badge>
          </div>
          <p className="text-[10px] sm:text-xs text-muted-foreground mt-1">
            {schedule.checks.filter(c => c[1]).length}/{schedule.checks.length} checks
          </p>
        </CardContent>
      </Card>
      </motion.div>
    </motion.div>
  );
}
