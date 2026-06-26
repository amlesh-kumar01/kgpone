import React, { useState, useRef, useEffect } from 'react';
import { Search, BookOpen, Building2 } from 'lucide-react';

const MarketplaceSearch = ({ departments = [], courses = [], onDepartmentYearSelect = () => {}, onCourseSelect = () => {} }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const lowerSearch = searchTerm.toLowerCase();

  const matchedDepartments = departments.filter(dept => 
    searchTerm && (dept.name.toLowerCase().includes(lowerSearch) || dept.code.toLowerCase().includes(lowerSearch))
  );

  const matchedCourses = courses.filter(course => 
    searchTerm && (course.title.toLowerCase().includes(lowerSearch) || course.code.toLowerCase().includes(lowerSearch))
  );

  const yearOptions = [
    { label: "1 -> First Year", val: 1 },
    { label: "2 -> Second Year", val: 2 },
    { label: "3 -> Third Year", val: 3 },
    { label: "4 -> Fourth Year", val: 4 }
  ];

  return (
    <div className="bg-card border border-border rounded-lg p-6 flex flex-col gap-4 shadow-sm mb-8" ref={dropdownRef}>
      <div className="relative flex-1">
        <Search className="absolute left-3 top-3 h-5 w-5 text-muted-foreground" />
        <input 
          type="text" 
          placeholder="Search courses by name/id or search departments..." 
          className="w-full pl-10 pr-4 py-3 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent transition-all"
          value={searchTerm}
          onChange={(e) => {
            setSearchTerm(e.target.value);
            setShowDropdown(true);
          }}
          onFocus={() => setShowDropdown(true)}
        />
        
        {/* Universal Search Autocomplete Dropdown */}
        {showDropdown && searchTerm && (matchedDepartments.length > 0 || matchedCourses.length > 0) && (
          <div className="absolute top-full left-0 right-0 mt-2 bg-card border border-border rounded-lg shadow-lg overflow-hidden z-50 max-h-96 overflow-y-auto">
            {/* Department Results */}
            {matchedDepartments.map(dept => (
              <div key={dept.id} className="border-b border-border/50 last:border-0">
                <div className="bg-muted/30 px-4 py-2 font-semibold text-sm text-foreground flex items-center gap-2">
                  <Building2 size={16} className="text-muted-foreground" />
                  {dept.name} - {dept.code}
                </div>
                <div className="flex flex-col">
                  {yearOptions.map(opt => (
                    <button
                      key={`${dept.id}-${opt.val}`}
                      className="w-full text-left px-8 py-2 text-sm text-muted-foreground hover:bg-accent/10 hover:text-accent transition-colors flex items-center justify-between"
                      onClick={() => {
                        setSearchTerm('');
                        setShowDropdown(false);
                        onDepartmentYearSelect(dept.id, opt.val);
                      }}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>
            ))}

            {/* Course Results */}
            {matchedCourses.map(course => (
              <button
                key={course.id}
                className="w-full border-b border-border/50 last:border-0 text-left px-4 py-3 hover:bg-accent/10 transition-colors flex flex-col"
                onClick={() => {
                  setSearchTerm('');
                  setShowDropdown(false);
                  onCourseSelect(course.id);
                }}
              >
                <div className="font-medium text-foreground flex items-center gap-2">
                  <BookOpen size={16} className="text-muted-foreground" />
                  {course.title}
                </div>
                <div className="text-xs text-muted-foreground ml-6 mt-1">
                  Code: {course.code}
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default MarketplaceSearch;
