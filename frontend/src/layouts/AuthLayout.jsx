import React from 'react';
import { Outlet } from 'react-router-dom';
import { motion } from 'framer-motion';

const AuthLayout = () => {
  return (
    <div className="min-h-screen grid lg:grid-cols-2 bg-background">
      {/* Visual side for large screens */}
      <div className="hidden lg:flex relative bg-background overflow-hidden flex-col justify-between p-16 text-foreground border-r border-border">
        
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="relative z-10 max-w-lg mt-12"
        >
          <div className="flex items-center gap-3 font-serif font-bold text-5xl tracking-tight mb-12">
            <div className="h-12 w-12 rounded-lg bg-accent flex items-center justify-center text-accent-foreground shadow-sm">
              L
            </div>
            Knowldedge OS
          </div>
          
          <h1 className="text-5xl font-serif leading-tight mb-6 text-primary">
            Refined Knowledge, <br/>
            <span className="text-muted-foreground italic">Elevated Structure.</span>
          </h1>

          <p className="mt-8 text-muted-foreground font-sans text-xl leading-relaxed">
            The premium academic catalog & knowledge portal. Sophisticated structure meets elegant design.
          </p>
        </motion.div>
        
        <div className="relative z-10 text-sm font-sans text-muted-foreground/60 flex justify-between w-full">
          <span>© {new Date().getFullYear()} Knowldedge OS</span>
          <span>Access Restricted</span>
        </div>
      </div>
      
      {/* Form side */}
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 1, delay: 0.2 }}
        className="flex items-center justify-center p-8 lg:p-16 bg-card"
      >
        <div className="w-full max-w-md space-y-8 relative z-10">
          <Outlet />
        </div>
      </motion.div>
    </div>
  );
};

export default AuthLayout;
