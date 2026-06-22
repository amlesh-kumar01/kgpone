import React from 'react';
import { NavLink } from 'react-router-dom';
import { Library } from 'lucide-react';

const DepartmentSidebar = ({ departments }) => {
  return (
    <div className="w-full md:w-64 flex-shrink-0">
      <div className="bg-card border border-border rounded-lg p-4 shadow-sm sticky top-24">
        <h2 className="text-lg font-serif font-semibold text-foreground mb-4 flex items-center gap-2">
          <Library size={20} className="text-accent" />
          Departments
        </h2>
        <nav className="flex flex-col gap-1">
          <NavLink
            to="/marketplace"
            end
            className={({ isActive }) =>
              `px-3 py-2 rounded-md text-sm transition-colors ${
                isActive 
                  ? 'bg-accent/10 text-accent font-medium' 
                  : 'text-muted-foreground hover:bg-muted hover:text-foreground'
              }`
            }
          >
            All Courses
          </NavLink>
          {departments.map(dept => (
            <NavLink
              key={dept.id}
              to={`/marketplace/departments/${dept.id}`}
              className={({ isActive }) =>
                `px-3 py-2 rounded-md text-sm transition-colors ${
                  isActive 
                    ? 'bg-accent/10 text-accent font-medium' 
                    : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                }`
              }
            >
              {dept.name}
            </NavLink>
          ))}
        </nav>
      </div>
    </div>
  );
};

export default DepartmentSidebar;
