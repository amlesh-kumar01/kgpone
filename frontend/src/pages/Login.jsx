import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import { Loader2 } from 'lucide-react';

const Login = ({ isRegister = false }) => {
  const { login, register } = useAuth();
  const { toast } = useToast();
  
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    fullName: ''
  });

  const handleChange = (e) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      if (isRegister) {
        await register(formData.email, formData.password, formData.fullName);
        toast({
          title: "Registration successful",
          description: "Welcome to KgpOne!",
        });
      } else {
        await login(formData.email, formData.password);
        toast({
          title: "Login successful",
          description: "Welcome back!",
        });
      }
    } catch (error) {
      toast({
        variant: "destructive",
        title: isRegister ? "Registration failed" : "Login failed",
        description: error.message || "An unexpected error occurred.",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col space-y-6">
      <div className="flex flex-col space-y-2 text-center">
        <h1 className="text-3xl font-semibold tracking-tight">
          {isRegister ? 'Create an account' : 'Welcome back'}
        </h1>
        <p className="text-sm text-slate-500">
          {isRegister 
            ? 'Enter your details below to create your student account' 
            : 'Enter your email to sign in to your account'}
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {isRegister && (
          <div className="space-y-2">
            <Label htmlFor="fullName">Full Name</Label>
            <Input 
              id="fullName" 
              name="fullName" 
              placeholder="John Doe" 
              required={isRegister}
              value={formData.fullName}
              onChange={handleChange}
            />
          </div>
        )}
        
        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input 
            id="email" 
            name="email" 
            type="email" 
            placeholder="m@example.com" 
            required 
            value={formData.email}
            onChange={handleChange}
          />
        </div>
        
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label htmlFor="password">Password</Label>
            {!isRegister && (
              <a href="#" className="text-sm font-medium text-cyan-600 hover:text-cyan-500">
                Forgot password?
              </a>
            )}
          </div>
          <Input 
            id="password" 
            name="password" 
            type="password" 
            required 
            value={formData.password}
            onChange={handleChange}
          />
        </div>

        <Button type="submit" className="w-full" disabled={loading}>
          {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {isRegister ? 'Sign Up' : 'Sign In'}
        </Button>
      </form>

      <div className="text-center text-sm text-slate-500">
        {isRegister ? 'Already have an account? ' : 'Don\'t have an account? '}
        <Link 
          to={isRegister ? '/login' : '/register'} 
          className="font-medium text-cyan-600 hover:text-cyan-500"
        >
          {isRegister ? 'Sign in' : 'Sign up'}
        </Link>
      </div>
    </div>
  );
};

export default Login;
