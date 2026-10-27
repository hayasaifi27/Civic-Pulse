import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAuth } from '../hooks/useAuth';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Alert } from '../components/ui/Alert';
import { Eye, EyeOff, Loader2 } from 'lucide-react';
import { cn } from '../utils/helpers';

const registerSchema = z.object({
  full_name: z.string().min(2, 'Name must be at least 2 characters').max(100),
  email: z.string().email('Invalid email address'),
  phone: z.string().optional(),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: 'Passwords do not match',
  path: ['confirmPassword'],
});

type RegisterForm = z.infer<typeof registerSchema>;

export function Register() {
  const { register: registerUser } = useAuth();
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const { register, handleSubmit, watch, formState: { errors } } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      full_name: '',
      email: '',
      phone: '',
      password: '',
      confirmPassword: '',
    },
  });

  const password = watch('password');

  const onSubmit = async (data: RegisterForm) => {
    setIsLoading(true);
    setError('');
    try {
      await registerUser({
        email: data.email,
        password: data.password,
        full_name: data.full_name,
        phone: data.phone || undefined,
      });
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.message || 'Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Create your account</h1>
        <p className="text-gray-600 mt-2">Join CivicPulse to report and track civic issues</p>
      </div>

      {error && <Alert variant="error" className="mb-6">{error}</Alert>}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>
        <Input
          {...register('full_name')}
          label="Full Name"
          placeholder="John Doe"
          error={errors.full_name?.message}
          autoComplete="name"
          disabled={isLoading}
        />

        <Input
          {...register('email')}
          type="email"
          label="Email"
          placeholder="you@example.com"
          error={errors.email?.message}
          autoComplete="email"
          disabled={isLoading}
        />

        <Input
          {...register('phone')}
          type="tel"
          label="Phone (optional)"
          placeholder="+1 (555) 000-0000"
          autoComplete="tel"
          disabled={isLoading}
        />

        <div className="relative">
          <Input
            {...register('password')}
            type={showPassword ? 'text' : 'password'}
            label="Password"
            placeholder="••••••••"
            error={errors.password?.message}
            helperText="At least 8 characters"
            autoComplete="new-password"
            disabled={isLoading}
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-[38px] text-gray-400 hover:text-gray-600"
            aria-label={showPassword ? 'Hide password' : 'Show password'}
          >
            {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
          </button>
        </div>

        <Input
          {...register('confirmPassword')}
          type={showPassword ? 'text' : 'password'}
          label="Confirm Password"
          placeholder="••••••••"
          error={errors.confirmPassword?.message}
          autoComplete="new-password"
          disabled={isLoading}
        />

        <div className="flex items-start gap-2">
          <input type="checkbox" id="terms" required className="mt-1 w-4 h-4 rounded border-gray-300 text-civic-teal focus:ring-civic-teal" />
          <label htmlFor="terms" className="text-sm text-gray-600">
            I agree to the{' '}
            <Link to="/terms" className="text-civic-teal hover:underline">Terms of Service</Link>
            {' '}and{' '}
            <Link to="/privacy" className="text-civic-teal hover:underline">Privacy Policy</Link>
          </label>
        </div>

        <Button type="submit" className="w-full" isLoading={isLoading}>
          {isLoading && <Loader2 className="w-5 h-5 mr-2" />}
          Create Account
        </Button>
      </form>

      <p className="mt-6 text-center text-gray-600">
        Already have an account?{' '}
        <Link to="/login" className="text-civic-teal font-medium hover:underline">
          Sign in
        </Link>
      </p>
    </div>
  );
}