import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { AuthProvider, useAuth } from '../contexts/AuthContext';

const TestComponent = () => {
  const { user } = useAuth();
  return <div>{user ? `User: ${user.email}` : 'Not Logged In'}</div>;
};

describe('AuthContext', () => {
  it('provides default auth state', () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );
    expect(screen.getByText('Not Logged In')).toBeInTheDocument();
  });
});
