import React from 'react';
import { Card, CardContent } from "@/components/ui/card";
import { Wrench } from 'lucide-react';

const ComingSoon = ({ title }) => {
  return (
    <div className="flex flex-col items-center justify-center h-[60vh] gap-4">
      <div className="bg-slate-100 dark:bg-slate-800 p-6 rounded-full">
        <Wrench className="w-12 h-12 text-slate-400" />
      </div>
      <h1 className="text-2xl font-bold tracking-tight text-center">
        {title} Page
      </h1>
      <p className="text-slate-500 text-center max-w-md">
        This page is currently under construction. Please check back later!
      </p>
    </div>
  );
};

export default ComingSoon;
