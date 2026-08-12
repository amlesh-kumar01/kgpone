import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { GraduationCap, Library, BrainCircuit } from 'lucide-react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';

const CourseCard = ({ course, departmentName }) => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
  };

  return (
    <motion.div variants={itemVariants}>
      <Card className="rounded-lg bg-card border-border shadow-sm hover:shadow-md transition-all h-full flex flex-col hover:border-accent">
        <CardHeader className="pb-3 border-b border-border/50">
          <div className="flex justify-between items-start mb-2">
            <span className="px-3 py-1 bg-muted text-muted-foreground text-xs font-bold rounded-full font-mono">
              {course.code}
            </span>
            <span className="text-xs font-semibold text-accent flex items-center gap-1 bg-accent/10 px-2 py-1 rounded-md">
              <GraduationCap size={14} /> {course.credits || 3} Credits
            </span>
          </div>
          <CardTitle className="text-xl font-serif font-bold text-foreground leading-tight line-clamp-2">
            {course.title}
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-4 flex-1">
          <p className="text-sm text-muted-foreground line-clamp-3 mb-4 leading-relaxed">
            {course.description || "No description available for this course. Please contact the department for more details."}
          </p>
          <div className="flex items-center gap-2 text-xs text-muted-foreground font-medium">
            <Library size={14} className="text-accent" />
            <span>{departmentName}</span>
          </div>
        </CardContent>
        <CardFooter className="pt-4 pb-6 px-6 border-t border-border/50 bg-background/50 flex flex-col gap-2">
          {/* Exam Prep CTA for students */}
          {(user?.role === 'STUDENT' || user?.role === 'ADMIN' || user?.role === 'PUBLISHER') && (
            <button
              onClick={() => navigate(`/courses/${course.id}/analyze`)}
              className="w-full px-4 py-2.5 bg-accent text-accent-foreground font-semibold rounded-lg hover:bg-accent/90 transition-colors flex justify-center items-center gap-2 text-sm"
            >
              <BrainCircuit size={16} />
              Prepare for Exam
            </button>
          )}
          <button className="w-full px-4 py-2 border border-border text-muted-foreground font-medium rounded-lg hover:bg-muted transition-colors flex justify-center items-center gap-2 text-sm">
            View Details
          </button>
        </CardFooter>
      </Card>
    </motion.div>
  );
};

export default CourseCard;
