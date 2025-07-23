import React from 'react';
import { OTPAuthForm } from '@/components/auth/auth-form';

export default function SignInPage() {
	return <OTPAuthForm initialMode="login" />;
}
