import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { Button } from '@/components/ui/button';
import { 
  LayoutDashboard, 
  Library, 
  Users, 
  BookOpen, 
  FileText,
  LogOut,
  Menu,
  MessageSquare,
  Palette,
  Check,
  BrainCircuit
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
  const { theme, setTheme } = useTheme();
  const location = useLocation();

  // Navigation config based on roles
  const navItems = [
    { label: 'Dashboard', path: '/', icon: <LayoutDashboard className="w-5 h-5" />, roles: ['ADMIN', 'PUBLISHER', 'STUDENT'] },
    { label: 'Assistant', path: '/chat', icon: <MessageSquare className="w-5 h-5 text-primary" />, roles: ['ADMIN', 'PUBLISHER', 'STUDENT'] },
    { label: 'Academic Config', path: '/academic-management', icon: <Library className="w-5 h-5" />, roles: ['ADMIN', 'PUBLISHER'] },
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
                ? 'bg-accent text-accent-foreground font-medium' 
                : 'text-muted-foreground hover:bg-accent/50 hover:text-accent-foreground'
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
    <div className="flex h-screen overflow-hidden w-full bg-background text-foreground">
      {/* Desktop Sidebar */}
      <aside className="hidden w-64 border-r bg-card text-card-foreground md:flex md:flex-col">
        <div className="flex h-14 items-center border-b px-6 lg:h-[60px]">
          <Link to="/" className="flex items-center gap-2 font-bold tracking-tight">
            <div className="h-6 w-6 rounded bg-primary flex items-center justify-center text-primary-foreground font-serif font-bold text-xs">
              L
            </div>
            <span className="font-serif">Knowledge OS</span>
          </Link>
        </div>
        <div className="flex-1 overflow-auto py-4 px-3">
          <NavLinks />
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex w-full flex-col">
        <header className="flex h-14 items-center gap-4 border-b bg-card text-card-foreground px-4 lg:h-[60px] lg:px-6 justify-between md:justify-end">
          
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
                <div className="h-6 w-6 rounded bg-primary flex items-center justify-center text-primary-foreground font-serif font-bold text-xs">
                  L
                </div>
                <span className="font-serif">Knowledge OS</span>
              </div>
              <NavLinks />
            </SheetContent>
          </Sheet>

          <div className="flex items-center gap-2">
            {/* Theme Toggle Dropdown */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="rounded-full h-8 w-8 text-muted-foreground hover:text-foreground">
                  <Palette className="h-4 w-4" />
                  <span className="sr-only">Toggle theme</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuLabel className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Theme</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => setTheme('system')} className="flex items-center justify-between cursor-pointer">
                  System {theme === 'system' && <Check className="h-4 w-4 ml-2" />}
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setTheme('light')} className="flex items-center justify-between cursor-pointer">
                  Light Mode {theme === 'light' && <Check className="h-4 w-4 ml-2" />}
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setTheme('dark')} className="flex items-center justify-between cursor-pointer">
                  Dark (Neutral) {theme === 'dark' && <Check className="h-4 w-4 ml-2" />}
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setTheme('slate')} className="flex items-center justify-between cursor-pointer">
                  Dark (Slate) {theme === 'slate' && <Check className="h-4 w-4 ml-2" />}
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setTheme('black')} className="flex items-center justify-between cursor-pointer">
                  Dark (Black) {theme === 'black' && <Check className="h-4 w-4 ml-2" />}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>

            {/* User Profile Dropdown */}
            <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="rounded-full">
                <Avatar className="h-8 w-8">
                  <AvatarFallback className="bg-primary/10 text-primary font-bold">
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
                  <p className="text-xs leading-none text-muted-foreground">
                    {user?.email}
                  </p>
                  <div className="mt-1 flex items-center">
                     <span className="inline-flex items-center rounded-full bg-muted px-2.5 py-0.5 text-xs font-semibold text-muted-foreground">
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
          </div>
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
