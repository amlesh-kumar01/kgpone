import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '@/components/ui/button';
import { 
  LayoutDashboard, 
  Library, 
  Users, 
  BookOpen, 
  FileText,
  LogOut,
  Menu,
  MessageSquare
} from 'lucide-react';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"

const DashboardLayout = () => {
  const { user, logout } = useAuth();
  const location = useLocation();

  // Navigation config based on roles
  const navItems = [
    { label: 'Dashboard', path: '/', icon: <LayoutDashboard className="w-5 h-5" />, roles: ['ADMIN', 'PUBLISHER', 'STUDENT'] },
    { label: 'Assistant', path: '/chat', icon: <MessageSquare className="w-5 h-5 text-primary" />, roles: ['ADMIN', 'PUBLISHER', 'STUDENT'] },
    { label: 'Departments', path: '/departments', icon: <Library className="w-5 h-5" />, roles: ['ADMIN', 'PUBLISHER'] },
    { label: 'Courses', path: '/courses', icon: <BookOpen className="w-5 h-5" />, roles: ['ADMIN', 'PUBLISHER'] },
    { label: 'Marketplace', path: '/marketplace', icon: <Library className="w-5 h-5" />, roles: ['STUDENT'] },
    { label: 'Documents', path: '/documents', icon: <FileText className="w-5 h-5" />, roles: ['ADMIN', 'PUBLISHER'] },
    { label: 'Users', path: '/users', icon: <Users className="w-5 h-5" />, roles: ['ADMIN'] },
  ].filter(item => user && item.roles.includes(user.role));

  const NavLinks = () => (
    <nav className="space-y-1">
      {navItems.map((item) => {
        const isActive = location.pathname === item.path;
        return (
          <Link
            key={item.path}
            to={item.path}
            className={`flex items-center gap-3 px-3 py-2 rounded-md transition-colors ${
              isActive 
                ? 'bg-slate-100 text-slate-900 font-medium dark:bg-slate-800 dark:text-slate-50' 
                : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800/50 dark:hover:text-slate-50'
            }`}
          >
            {item.icon}
            {item.label}
          </Link>
        )
      })}
    </nav>
  );

  return (
    <div className="flex h-screen overflow-hidden w-full bg-slate-50/50 dark:bg-slate-950">
      {/* Desktop Sidebar */}
      <aside className="hidden w-64 border-r bg-white dark:bg-slate-900 md:flex md:flex-col">
        <div className="flex h-14 items-center border-b px-6 lg:h-[60px]">
          <Link to="/" className="flex items-center gap-2 font-bold tracking-tight">
            <div className="h-6 w-6 rounded bg-accent flex items-center justify-center text-accent-foreground font-serif font-bold text-xs">
              L
            </div>
            <span className="font-serif">Lumière</span>
          </Link>
        </div>
        <div className="flex-1 overflow-auto py-4 px-3">
          <NavLinks />
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex w-full flex-col">
        <header className="flex h-14 items-center gap-4 border-b bg-white dark:bg-slate-900 px-4 lg:h-[60px] lg:px-6 justify-between md:justify-end">
          
          {/* Mobile Navigation */}
          <Sheet>
            <SheetTrigger asChild>
              <Button variant="outline" size="icon" className="shrink-0 md:hidden">
                <Menu className="h-5 w-5" />
                <span className="sr-only">Toggle navigation menu</span>
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="flex flex-col">
              <div className="flex items-center gap-2 font-bold tracking-tight mb-4">
                <div className="h-6 w-6 rounded bg-accent flex items-center justify-center text-accent-foreground font-serif font-bold text-xs">
                  L
                </div>
                <span className="font-serif">Lumière</span>
              </div>
              <NavLinks />
            </SheetContent>
          </Sheet>

          {/* User Profile Dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="rounded-full">
                <Avatar className="h-8 w-8">
                  <AvatarFallback className="bg-slate-100 text-slate-900 dark:bg-slate-800 dark:text-slate-50">
                    {user?.full_name?.charAt(0) || 'U'}
                  </AvatarFallback>
                </Avatar>
                <span className="sr-only">Toggle user menu</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>
                <div className="flex flex-col space-y-1">
                  <p className="text-sm font-medium leading-none">{user?.full_name}</p>
                  <p className="text-xs leading-none text-slate-500 dark:text-slate-400">
                    {user?.email}
                  </p>
                  <div className="mt-1 flex items-center">
                     <span className="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-800 dark:bg-slate-800 dark:text-slate-300">
                        {user?.role}
                     </span>
                  </div>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={logout} className="text-red-600 dark:text-red-400 cursor-pointer">
                <LogOut className="mr-2 h-4 w-4" />
                <span>Log out</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </header>

        {/* Page Content */}
        <main className="flex-1 p-4 md:p-6 lg:p-8 max-w-7xl mx-auto w-full overflow-y-auto no-scrollbar">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default DashboardLayout;
