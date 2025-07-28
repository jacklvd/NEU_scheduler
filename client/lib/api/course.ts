import { graphqlClient } from './graphql';
import type { Term, Subject, Class, SuggestedPlan } from '@/types/api';

// GraphQL response types
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

interface HealthCheckResponse {
	healthCheck: string;
}

export class CourseAPI {
	static async getTerms(maxResults: number = 50): Promise<Term[]> {
		const query = `
      query GetTerms($maxResults: Int!) {
        getTerms(maxResults: $maxResults) {
          id
          name
          startDate
          endDate
        }
      }
    `;

		try {
			console.log('GraphQL Query - GetTerms');
			const response = (await graphqlClient.request(query, {
				maxResults,
			})) as GetTermsResponse;
			console.log('GraphQL Response - GetTerms:', response);
			return response.getTerms || [];
		} catch (error) {
			console.error('Error fetching terms:', error);
			throw error;
		}
	}

	static async getSubjects(
		term: string,
		searchTerm: string = ''
	): Promise<Subject[]> {
		const query = `
      query GetSubjects($term: String!, $searchTerm: String!) {
        getSubjects(term: $term, searchTerm: $searchTerm) {
          code
          name
          college
        }
      }
    `;

		try {
			console.log('GraphQL Query - GetSubjects', { term, searchTerm });
			const response = (await graphqlClient.request(query, {
				term,
				searchTerm,
			})) as GetSubjectsResponse;
			console.log('GraphQL Response - GetSubjects:', response);
			return response.getSubjects || [];
		} catch (error) {
			console.error('Error fetching subjects:', error);
			throw error;
		}
	}

	static async searchCourses(params: {
		term: string;
		subject?: string;
		courseNumber?: string;
		pageSize?: number;
	}): Promise<Class[]> {
		const query = `
      query SearchCourses($term: String!, $subject: String, $courseNumber: String, $pageSize: Int) {
        searchCourses(term: $term, subject: $subject, courseNumber: $courseNumber, pageSize: $pageSize) {
          crn
          title
          subject
          courseNumber
          instructor
          meetingDays
          meetingTimes
          location
          enrollment
          enrollmentCap
          waitlist
          credits
        }
      }
    `;

		try {
			console.log('GraphQL Query - SearchCourses', params);
			const response = (await graphqlClient.request(query, {
				term: params.term,
				subject: params.subject || '',
				courseNumber: params.courseNumber || '',
				pageSize: params.pageSize || 20,
			})) as SearchCoursesResponse;
			console.log('GraphQL Response - SearchCourses:', response);
			return response.searchCourses || [];
		} catch (error) {
			console.error('Error searching courses:', error);
			throw error;
		}
	}

	static async suggestPlan(
		interest: string,
		years: number = 2
	): Promise<SuggestedPlan[]> {
		const query = `
      query SuggestPlan($interest: String!, $years: Int!) {
        suggestPlan(interest: $interest, years: $years) {
          year
          term
          courses
          credits
          notes
        }
      }
    `;

		try {
			console.log('GraphQL Query - SuggestPlan', { interest, years });
			const response = (await graphqlClient.request(query, {
				interest,
				years,
			})) as SuggestPlanResponse;
			console.log('GraphQL Response - SuggestPlan:', response);
			return response.suggestPlan || [];
		} catch (error) {
			console.error('Error generating plan suggestions:', error);
			throw error;
		}
	}

	static async healthCheck(): Promise<string> {
		const query = `
      query {
        healthCheck
      }
    `;

		try {
			const response = (await graphqlClient.request(
				query
			)) as HealthCheckResponse;
			return response.healthCheck || 'Unknown';
		} catch (error) {
			console.error('Health check failed:', error);
			return 'Error';
		}
	}
}
