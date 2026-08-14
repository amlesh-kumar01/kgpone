import React, { useState } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { APP_CONFIG } from '../config/appConfig';
import { Button } from '@/components/ui/button';
import { 
  LayoutDashboard, 
  Library, 
  Users, 
  FileText,
  LogOut,
  Menu,
  MessageSquare,
  Palette,
  Check,
  PanelLeftClose,
  PanelLeftOpen,
  MoreVertical,
  Sun,
  Moon,
  Monitor
} from 'lucide-react';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuPortal,
} from "@/components/ui/dropdown-menu"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"

const DashboardLayout = () => {
  const { user, logout } = useAuth();
  const { theme, setTheme } = useTheme();
  const location = useLocation();
  const [isCollapsed, setIsCollapsed] = useState(false);

  // Navigation config based on roles
  const navItems = [
    { label: 'Dashboard', path: '/', icon: <LayoutDashboard className="w-5 h-5 shrink-0" />, roles: ['ADMIN', 'PUBLISHER', 'STUDENT'] },
    { label: 'Assistant', path: '/chat', icon: <MessageSquare className="w-5 h-5 shrink-0 text-primary" />, roles: ['ADMIN', 'PUBLISHER', 'STUDENT'] },
    { label: 'Academic Config', path: '/academic-management', icon: <Library className="w-5 h-5 shrink-0" />, roles: ['ADMIN', 'PUBLISHER'] },
    { label: 'Marketplace', path: '/marketplace', icon: <Library className="w-5 h-5 shrink-0" />, roles: ['STUDENT'] },
    { label: 'Documents', path: '/documents', icon: <FileText className="w-5 h-5 shrink-0" />, roles: ['ADMIN', 'PUBLISHER'] },
    { label: 'Users', path: '/users', icon: <Users className="w-5 h-5 shrink-0" />, roles: ['ADMIN'] },
  ].filter(item => user && item.roles.includes(user.role));

  const NavLinks = ({ mobile = false }) => (
    <nav className="flex flex-col gap-1 w-full px-2">
      {navItems.map((item) => {
        const isActive = location.pathname === item.path;
        return (
          <Link
            key={item.path}
            to={item.path}
            title={isCollapsed && !mobile ? item.label : undefined}
            className={`flex items-center gap-3 px-3 py-2.5 rounded-md transition-all ${
              isActive 
                ? 'bg-muted text-foreground font-semibold' 
                : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground font-medium'
            } ${isCollapsed && !mobile ? 'justify-center' : 'justify-start'}`}
          >
            {item.icon}
            {(!isCollapsed || mobile) && <span className="text-sm truncate">{item.label}</span>}
          </Link>
        )
      })}
    </nav>
  );

  return (
    <div className="flex h-screen overflow-hidden w-full bg-background text-foreground">
      {/* Mobile Top Header (Only visible on small screens to provide access to the hamburger) */}
      <div className="md:hidden fixed top-0 left-0 right-0 h-14 bg-card border-b border-border z-30 flex items-center justify-between px-4">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded bg-primary flex items-center justify-center text-primary-foreground font-serif font-bold text-lg">
            {APP_CONFIG.APP_NAME.charAt(0)}
          </div>
          <span className="font-serif font-bold text-lg tracking-tight">{APP_CONFIG.APP_NAME}</span>
        </div>
        <Sheet>
          <SheetTrigger asChild>
            <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-foreground">
              <Menu className="h-6 w-6" />
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="flex flex-col bg-card border-r-border w-72 p-0 h-full">
            <div className="flex h-16 items-center border-b border-border/50 px-6 mb-4">
              <div className="flex items-center gap-2">
                <div className="h-8 w-8 rounded bg-primary flex items-center justify-center text-primary-foreground font-serif font-bold text-lg">
                  {APP_CONFIG.APP_NAME.charAt(0)}
                </div>
                <span className="font-serif font-bold text-xl tracking-tight">{APP_CONFIG.APP_NAME}</span>
              </div>
            </div>
            <div className="flex-1 overflow-y-auto no-scrollbar">
               <NavLinks mobile />
            </div>
            
            {/* Mobile Bottom User Menu */}
            <div className="p-4 border-t border-border mt-auto">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" className="w-full justify-between px-2 py-6 h-auto hover:bg-muted">
                      <div className="flex items-center gap-3 overflow-hidden text-left">
                        <Avatar className="h-9 w-9 shrink-0 border border-border">
                          <AvatarFallback className="bg-muted text-foreground font-bold font-serif text-sm">
                            {user?.full_name?.charAt(0) || 'U'}
                          </AvatarFallback>
                        </Avatar>
                        <div className="flex flex-col overflow-hidden">
                          <span className="text-sm font-semibold truncate">{user?.full_name}</span>
                          <span className="text-xs text-muted-foreground truncate">{user?.email}</span>
                        </div>
                      </div>
                      <MoreVertical className="w-4 h-4 text-muted-foreground shrink-0" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-64 border-border mb-2" sideOffset={10}>
                    <DropdownMenuLabel className="font-normal">
                      <div className="flex flex-col space-y-1">
                        <p className="text-sm font-semibold leading-none">{user?.full_name}</p>
                        <p className="text-xs leading-none text-muted-foreground mt-1">
                          {user?.role}
                        </p>
                      </div>
                    </DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    <DropdownMenuSub>
                      <DropdownMenuSubTrigger>
                        <Palette className="mr-2 h-4 w-4" />
                        <span>Theme</span>
                      </DropdownMenuSubTrigger>
                      <DropdownMenuPortal>
                        <DropdownMenuSubContent>
                          <DropdownMenuItem onClick={() => setTheme('light')}>
                            <Sun className="mr-2 h-4 w-4" />
                            <span>Light</span>
                            {theme === 'light' && <Check className="ml-auto h-4 w-4" />}
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => setTheme('dark')}>
                            <Moon className="mr-2 h-4 w-4" />
                            <span>Dark</span>
                            {theme === 'dark' && <Check className="ml-auto h-4 w-4" />}
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => setTheme('system')}>
                            <Monitor className="mr-2 h-4 w-4" />
                            <span>System</span>
                            {theme === 'system' && <Check className="ml-auto h-4 w-4" />}
                          </DropdownMenuItem>
                        </DropdownMenuSubContent>
                      </DropdownMenuPortal>
                    </DropdownMenuSub>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={logout} className="text-red-600 focus:bg-red-50 focus:text-red-600 dark:focus:bg-red-950 dark:focus:text-red-400 font-medium">
                      <LogOut className="mr-2 h-4 w-4" />
                      <span>Log out</span>
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
            </div>
          </SheetContent>
        </Sheet>
      </div>

      {/* Desktop Collapsible Sidebar */}
      <aside 
        className={`hidden md:flex flex-col border-r border-border bg-card transition-all duration-300 ease-in-out relative z-20 shadow-sm ${
          isCollapsed ? 'w-16' : 'w-64'
        }`}
      >
        <div className="flex h-16 items-center justify-between border-b border-border/50 px-4 shrink-0 overflow-hidden">
          <Link to="/" className="flex items-center gap-3 overflow-hidden">
            <div className="h-8 w-8 rounded shrink-0 bg-primary flex items-center justify-center text-primary-foreground font-serif font-bold text-lg shadow-sm">
              {APP_CONFIG.APP_NAME.charAt(0)}
            </div>
            {!isCollapsed && <span className="font-serif font-bold text-xl tracking-tight text-foreground truncate">{APP_CONFIG.APP_NAME}</span>}
          </Link>
          
          {/* Collapse Toggle inside header */}
          {!isCollapsed && (
            <button 
              onClick={() => setIsCollapsed(true)}
              className="text-muted-foreground hover:text-foreground transition-colors p-1"
              title="Collapse Sidebar"
            >
              <PanelLeftClose size={18} />
            </button>
          )}
        </div>
        
        {isCollapsed && (
          <div className="flex justify-center mt-4">
             <button 
                onClick={() => setIsCollapsed(false)}
                className="text-muted-foreground hover:text-foreground transition-colors p-1 bg-muted rounded-md"
                title="Expand Sidebar"
              >
                <PanelLeftOpen size={18} />
              </button>
          </div>
        )}

        <div className="flex-1 overflow-y-auto py-4 flex flex-col gap-1 no-scrollbar">
          <NavLinks />
        </div>

        {/* User Account / Theme (Bottom of Sidebar) */}
        <div className="mt-auto p-2 border-t border-border/50 shrink-0">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button 
                variant="ghost" 
                className={`w-full flex items-center ${isCollapsed ? 'justify-center px-0' : 'justify-between px-2'} py-6 h-auto hover:bg-muted rounded-md transition-colors`}
              >
                <div className="flex items-center gap-3 overflow-hidden text-left">
                  <Avatar className="h-8 w-8 shrink-0 border border-border shadow-sm">
                    <AvatarFallback className="bg-muted text-foreground font-bold font-serif text-xs">
                      {user?.full_name?.charAt(0) || 'U'}
                    </AvatarFallback>
                  </Avatar>
                  {!isCollapsed && (
                    <div className="flex flex-col overflow-hidden">
                      <span className="text-sm font-semibold truncate text-foreground">{user?.full_name}</span>
                      <span className="text-xs text-muted-foreground truncate">{user?.role}</span>
                    </div>
                  )}
                </div>
                {!isCollapsed && <MoreVertical className="w-4 h-4 text-muted-foreground shrink-0 opacity-50 group-hover:opacity-100 transition-opacity" />}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align={isCollapsed ? "start" : "end"} side="right" className="w-56 border-border ml-2" sideOffset={10}>
              <DropdownMenuLabel className="font-normal">
                <div className="flex flex-col space-y-1">
                  <p className="text-sm font-semibold leading-none">{user?.full_name}</p>
                  <p className="text-xs leading-none text-muted-foreground mt-1">
                    {user?.email}
                  </p>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuSub>
                <DropdownMenuSubTrigger>
                  <Palette className="mr-2 h-4 w-4" />
                  <span>Theme</span>
                </DropdownMenuSubTrigger>
                <DropdownMenuPortal>
                  <DropdownMenuSubContent sideOffset={8}>
                    <DropdownMenuItem onClick={() => setTheme('light')}>
                      <Sun className="mr-2 h-4 w-4" />
                      <span>Light</span>
                      {theme === 'light' && <Check className="ml-auto h-4 w-4 text-primary" />}
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => setTheme('dark')}>
                      <Moon className="mr-2 h-4 w-4" />
                      <span>Dark</span>
                      {theme === 'dark' && <Check className="ml-auto h-4 w-4 text-primary" />}
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => setTheme('system')}>
                      <Monitor className="mr-2 h-4 w-4" />
                      <span>System</span>
                      {theme === 'system' && <Check className="ml-auto h-4 w-4 text-primary" />}
                    </DropdownMenuItem>
                  </DropdownMenuSubContent>
                </DropdownMenuPortal>
              </DropdownMenuSub>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={logout} className="text-red-600 focus:bg-red-50 focus:text-red-600 dark:focus:bg-red-950 dark:focus:text-red-400 font-medium">
                <LogOut className="mr-2 h-4 w-4" />
                <span>Log out</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex flex-col flex-1 w-full overflow-hidden">
        {/* Page Content */}
        <main className="flex-1 overflow-y-auto no-scrollbar relative w-full pt-14 md:pt-0 flex flex-col">
          <div className={`flex-1 w-full mx-auto ${location.pathname === '/chat' ? 'p-0 max-w-none' : 'p-4 sm:p-6 lg:p-8 max-w-[1400px]'}`}>
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};

export default DashboardLayout;
