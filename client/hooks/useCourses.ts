'use client';

import { useState, useEffect } from 'react';
import { CourseAPI } from '@/lib/api/course';
import type { Term, Subject, Class, SuggestedPlan } from '@/types/api';

export function useTerms() {
	const [terms, setTerms] = useState<Term[]>([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);

	const fetchTerms = async () => {
		try {
			setLoading(true);
			setError(null);

			console.log('Fetching terms...');
			const data = await CourseAPI.getTerms(50); // Get more terms
			console.log('Terms received:', data);

			setTerms(data);
		} catch (err) {
			console.error('Error fetching terms:', err);
			setError('Failed to fetch terms');
		} finally {
			setLoading(false);
		}
	};

	useEffect(() => {
		fetchTerms();
	}, []);

	const refetch = async () => {
		await fetchTerms();
	};

	return { terms, loading, error, refetch };
}

export function useSubjects(term: string) {
	const [subjects, setSubjects] = useState<Subject[]>([]);
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);

	useEffect(() => {
		if (!term) {
			setSubjects([]);
			return;
		}

		async function fetchSubjects() {
			try {
				setLoading(true);
				setError(null);

				console.log('Fetching subjects for term:', term);
				const data = await CourseAPI.getSubjects(term);
				console.log('Subjects received:', data);

				setSubjects(data);
			} catch (err) {
				console.error('Error fetching subjects:', err);
				setError('Failed to fetch subjects');
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
			setError(null);
			setCourses([]); // Clear previous results

			console.log('Searching courses with params:', params);

			if (!params.term) {
				setError('Term is required for course search');
				return;
			}

			const data = await CourseAPI.searchCourses(params);
			console.log('Course search results:', data);

			setCourses(data);

			if (data.length === 0) {
				setError('No courses found matching your search criteria');
			}
		} catch (err) {
			console.error('Error searching courses:', err);
			setError('Failed to search courses. Please try again.');
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
			setError(null);

			console.log('Generating AI plan...', { interest, years });
			const data = await CourseAPI.suggestPlan(interest, years);
			console.log('AI plan generated:', data);

			setPlan(data);
		} catch (err) {
			console.error('Error generating AI plan:', err);
			setError('Failed to generate plan. Please try again.');
		} finally {
			setLoading(false);
		}
	};

	return { plan, loading, error, generatePlan };
}
