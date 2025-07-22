/* eslint-disable @typescript-eslint/no-explicit-any */
// Client-side GraphQL utilities - no server-side code here
import { GraphQLClient } from 'graphql-request';

const GRAPHQL_ENDPOINT =
	process.env.NEXT_PUBLIC_GRAPHQL_ENDPOINT ||
	'http://localhost:8000/api/graphql';

console.log('GraphQL endpoint:', GRAPHQL_ENDPOINT);

// Create a wrapper around the GraphQL client to add better debugging
class DebugGraphQLClient {
	private client: GraphQLClient;

	constructor(endpoint: string, options: any = {}) {
		this.client = new GraphQLClient(endpoint, {
			...options,
			headers: {
				'Content-Type': 'application/json',
				...options.headers,
			},
		});
	}

	async request(query: string, variables: any = {}) {
		try {
			console.log(`GraphQL Request to ${GRAPHQL_ENDPOINT}:`, {
				query: query.slice(0, 200) + '...', // Truncate long queries in logs
				variables,
			});

			const result = await this.client.request(query, variables);
			console.log('GraphQL Response:', result);
			return result;
		} catch (error) {
			console.error('GraphQL Request Failed:', {
				endpoint: GRAPHQL_ENDPOINT,
				query: query.slice(0, 200) + '...',
				variables,
				error,
			});
			throw error;
		}
	}
}

// Export the enhanced client
export const graphqlClient = new DebugGraphQLClient(GRAPHQL_ENDPOINT);

// GraphQL queries
export const GET_TERMS = `
  query GetTerms($maxResults: Int = 20) {
    getTerms(maxResults: $maxResults) {
      id
      name
    }
  }
`;

export const GET_SUBJECTS = `
  query GetSubjects($term: String!, $searchTerm: String = "") {
    getSubjects(term: $term, searchTerm: $searchTerm) {
      code
      name
    }
  }
`;

export const SEARCH_COURSES = `
  query SearchCourses($term: String!, $subject: String = "", $courseNumber: String = "", $pageSize: Int = 20) {
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
      credits
    }
  }
`;

export const SUGGEST_PLAN = `
  query SuggestPlan($interest: String!, $years: Int = 2) {
    suggestPlan(interest: $interest, years: $years) {
      year
      term
      courses
    }
  }
`;

export const SAVE_SCHEDULE = `
  mutation SaveSchedule($userId: String!, $year: Int!, $term: String!, $courses: [String!]!) {
    saveSchedule(userId: $userId, year: $year, term: $term, courses: $courses)
  }
`;
