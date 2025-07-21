'use client';

import { useState, useEffect } from 'react';
import { CourseAPI } from '@/lib/api/course';
import type { Term, Subject, Class, SuggestedPlan } from '@/types/api';

export function useTerms() {
	const [terms, setTerms] = useState<Term[]>([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);

	async function fetchTerms() {
		try {
			setLoading(true);
			const data = await CourseAPI.getTerms();
			setTerms(data);
			setError(null);
		} catch (err) {
			setError('Failed to fetch terms');
			console.error(err);
		} finally {
			setLoading(false);
		}
	}

	useEffect(() => {
		fetchTerms();
	}, []);

	return { terms, loading, error, refetch: fetchTerms };
}

export function useSubjects(term: string) {
	const [subjects, setSubjects] = useState<Subject[]>([]);
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);

	useEffect(() => {
		if (!term) return;

		async function fetchSubjects() {
			try {
				setLoading(true);
				const data = await CourseAPI.getSubjects(term);
				setSubjects(data);
				setError(null);
			} catch (err) {
				setError('Failed to fetch subjects');
				console.error(err);
			} finally {
				setLoading(false);
			}
		}

		fetchSubjects();
	}, [term]);

	return { subjects, loading, error };
}

export function useCourseSearch() {
	const [courses, setCourses] = useState<Class[]>([]);
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);

	const searchCourses = async (params: {
		term: string;
		subject?: string;
		courseNumber?: string;
		pageSize?: number;
	}) => {
		try {
			setLoading(true);
			const data = await CourseAPI.searchCourses(params);
			setCourses(data);
			setError(null);
		} catch (err) {
			setError('Failed to search courses');
			console.error(err);
		} finally {
			setLoading(false);
		}
	};

	return { courses, loading, error, searchCourses };
}

export function useAIPlan() {
	const [plan, setPlan] = useState<SuggestedPlan[]>([]);
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);

	const generatePlan = async (interest: string, years: number = 2) => {
		try {
			setLoading(true);
			const data = await CourseAPI.suggestPlan(interest, years);
			setPlan(data);
			setError(null);
		} catch (err) {
			setError('Failed to generate plan');
			console.error(err);
		} finally {
			setLoading(false);
		}
	};

	return { plan, loading, error, generatePlan };
}
