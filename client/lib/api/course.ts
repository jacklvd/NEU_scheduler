// Removing "use server" directive
import {
	graphqlClient,
	GET_TERMS,
	GET_SUBJECTS,
	SEARCH_COURSES,
	SUGGEST_PLAN,
	SAVE_SCHEDULE,
} from './graphql';
import type { Term, Subject, Class, SuggestedPlan } from '@/types/api';

// Define interfaces for GraphQL responses
interface GetTermsResponse {
	getTerms: Term[];
}

interface GetSubjectsResponse {
	getSubjects: Subject[];
}

interface SearchCoursesResponse {
	searchCourses: Class[];
}

interface SuggestPlanResponse {
	suggestPlan: SuggestedPlan[];
}

interface SaveScheduleResponse {
	saveSchedule: boolean;
}

interface HealthCheckResponse {
	healthCheck: string;
}

export class CourseAPI {
	static async getTerms(maxResults: number = 20): Promise<Term[]> {
		try {
			const response = await graphqlClient.request(GET_TERMS, { maxResults });
			return (response as GetTermsResponse)?.getTerms || [];
		} catch (error) {
			console.error('Error fetching terms:', error);
			return [];
		}
	}

	static async getSubjects(
		term: string,
		searchTerm: string = ''
	): Promise<Subject[]> {
		try {
			const response = await graphqlClient.request(GET_SUBJECTS, {
				term,
				searchTerm,
			});
			return (response as GetSubjectsResponse)?.getSubjects || [];
		} catch (error) {
			console.error('Error fetching subjects:', error);
			return [];
		}
	}

	static async searchCourses(params: {
		term: string;
		subject?: string;
		courseNumber?: string;
		pageSize?: number;
	}): Promise<Class[]> {
		try {
			const response = await graphqlClient.request(SEARCH_COURSES, params);
			return (response as SearchCoursesResponse)?.searchCourses || [];
		} catch (error) {
			console.error('Error searching courses:', error);
			return [];
		}
	}

	static async suggestPlan(
		interest: string,
		years: number = 2
	): Promise<SuggestedPlan[]> {
		try {
			const response = await graphqlClient.request(SUGGEST_PLAN, {
				interest,
				years,
			});
			return (response as SuggestPlanResponse)?.suggestPlan || [];
		} catch (error) {
			console.error('Error generating plan suggestions:', error);
			return [];
		}
	}

	static async saveSchedule(
		userId: string,
		year: number,
		term: string,
		courses: string[]
	): Promise<boolean> {
		try {
			const response = await graphqlClient.request(SAVE_SCHEDULE, {
				userId,
				year,
				term,
				courses,
			});
			return (response as SaveScheduleResponse)?.saveSchedule || false;
		} catch (error) {
			console.error('Error saving schedule:', error);
			return false;
		}
	}

	static async healthCheck(): Promise<string> {
		try {
			const response = await graphqlClient.request(`
        query {
          healthCheck
        }
      `);
			return (response as HealthCheckResponse)?.healthCheck || 'Unknown';
		} catch (error) {
			console.error('Health check failed:', error);
			return 'Error';
		}
	}
}
