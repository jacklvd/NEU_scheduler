import {
	graphqlClient,
	GET_TERMS,
	GET_SUBJECTS,
	SEARCH_COURSES,
	SUGGEST_PLAN,
	SAVE_SCHEDULE,
} from './graphql';
import type {
	Term,
	Subject,
	Class,
	SuggestedPlan,
	ApiResponse,
} from '@/types/api';

export class CourseAPI {
	static async getTerms(maxResults: number = 20): Promise<Term[]> {
		try {
			const response: ApiResponse<{ getTerms: Term[] }> =
				await graphqlClient.request(GET_TERMS, { maxResults });
			return response.data?.getTerms || [];
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
			const response: { getSubjects: Subject[] } =
				await graphqlClient.request(GET_SUBJECTS, { term, searchTerm });
			return response.getSubjects || [];
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
			const response: ApiResponse<{ searchCourses: Class[] }> =
				await graphqlClient.request(SEARCH_COURSES, params);
			return response.data?.searchCourses || [];
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
			const response: ApiResponse<{ suggestPlan: SuggestedPlan[] }> =
				await graphqlClient.request(SUGGEST_PLAN, { interest, years });
			return response.data?.suggestPlan || [];
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
			const response: ApiResponse<{ saveSchedule: boolean }> =
				await graphqlClient.request(SAVE_SCHEDULE, {
					userId,
					year,
					term,
					courses,
				});
			return response.data?.saveSchedule || false;
		} catch (error) {
			console.error('Error saving schedule:', error);
			return false;
		}
	}

	static async healthCheck(): Promise<string> {
		try {
			const response: ApiResponse<{ healthCheck: string }> =
				await graphqlClient.request(`
        query {
          healthCheck
        }
      `);
			return response.data?.healthCheck || 'Unknown';
		} catch (error) {
			console.error('Health check failed:', error);
			return 'Error';
		}
	}
}
